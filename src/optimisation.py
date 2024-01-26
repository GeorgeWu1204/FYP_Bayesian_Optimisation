import torch
import data
import time
import utils
import warnings
from colorama import Fore, Style

from interface import fill_constraints, parse_constraints
from discretization import SingleTaskGP_transformed
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.models.transforms.outcome import Standardize
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
from botorch.acquisition.multi_objective.monte_carlo import qNoisyExpectedHypervolumeImprovement
from botorch.optim import optimize_acqf
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_model

# Warning Suppression
from botorch.exceptions import BadInitialCandidatesWarning
from linear_operator.utils.cholesky import NumericalWarning
from botorch.exceptions.warnings import InputDataWarning


# Device Settings
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Input Settings
CONSTRAINT_FILE = '../data/input_constraint.txt'
self_constraints, coupled_constraints, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT = parse_constraints(CONSTRAINT_FILE)
(INPUT_DATA_DIM, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_NAMES), constraint_set = fill_constraints(self_constraints, coupled_constraints, device)
OBJECTIVES_TO_OPTIMISE_DIM = len(OBJECTIVES_TO_OPTIMISE)
OBJECTIVE_DIM = OBJECTIVES_TO_OPTIMISE_DIM + len(OUTPUT_OBJECTIVE_CONSTRAINT)
OBJECTIVES_TO_OPTIMISE_INDEX = list(range(OBJECTIVES_TO_OPTIMISE_DIM))
# Dataset Settings
RAW_DATA_FILE = '../data/ppa_v2.db'
data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS)

# Model Settings
NUM_RESTARTS = 16               # number of starting points for BO for optimize_acqf
NUM_OF_INITIAL_POINT = 200      # number of initial points for BO
N_TRIALS = 1                    # number of trials of BO (outer loop)
N_BATCH = 2                     # number of BO batches (inner loop)
BATCH_SIZE = 1                  # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 128                # number of MC samples for qNEI
# NOISE_SE = 1e-3               # noise level for qNEI
# MODEL_LIKELIHOOD = GaussianLikelihood(
#     noise_constraint=GreaterThan(NOISE_SE) # noise level for qNEI
# )
# Runtime Settings
verbose = True
record = False
debug = True

t_type = torch.float64

#reference point for optimisation used for hypervolume calculation
ref_points = utils.find_ref_points(OBJECTIVES_TO_OPTIMISE_DIM, OBJECTIVES_TO_OPTIMISE, data_set.worst_value, data_set.output_normalised_factors, t_type, device)
#normalise objective to ensure the same scale
obj_normalized_factors = list(data_set.output_normalised_factors.values())

def calculate_hypervolume(ref_points, train_obj):
    """Calculate the hypervolume"""
    # Y dimension (batch_shape) x n x m-dim
    partitioning = NondominatedPartitioning(ref_point=ref_points, Y = train_obj[..., : OBJECTIVES_TO_OPTIMISE_DIM])
    hv = partitioning.compute_hypervolume().item()
    return hv

def generate_initial_data(data_type):
    """generate training data"""
    unnormalised_train_x, exact_objs, con_objs, normalised_objs = utils.generate_valid_initial_data(NUM_OF_INITIAL_POINT, INPUT_DATA_DIM, OBJECTIVE_DIM, data_set, constraint_set, obj_normalized_factors, data_type, device)
    train_obj = torch.cat([normalised_objs[...,:OBJECTIVES_TO_OPTIMISE_DIM], con_objs], dim=-1)
    # with_noise_train_obj = train_obj + torch.randn_like(train_obj) * NOISE_SE
    print("tran obj is ", train_obj.shape)
    hypervolumes = torch.zeros(NUM_OF_INITIAL_POINT, device=device)
    for i in range(NUM_OF_INITIAL_POINT):
        hypervolumes[i] = calculate_hypervolume(ref_points, train_obj[i].unsqueeze(0))
    return unnormalised_train_x, exact_objs, train_obj, hypervolumes

def initialize_model(train_x, train_obj, GP_kernel_mapping_covar_identification):
    """define models for objective and constraint"""
    ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
    models = []
    
    for obj_index in range(train_obj.shape[-1]): 
        train_y = train_obj[..., obj_index : obj_index + 1]
        models.append(SingleTaskGP_transformed(train_x, 
                                   train_y, 
                                   GP_kernel_mapping_covar_identification,
                                #    likelihood=MODEL_LIKELIHOOD, 
                                   outcome_transform=Standardize(m=1)
                                   ))
       
    model = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    return mll, model


def build_qNEHVI_acqf(model, train_x, sampler):
    """Build the qNEHVI acquisition function"""
    # normalized_train_x = normalize(train_x, bounds)
    
    acq_func = qNoisyExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_points.tolist(), 
        X_baseline=train_x,
        sampler=sampler,
        prune_baseline=True,
        objective=IdentityMCMultiOutputObjective(outcomes = OBJECTIVES_TO_OPTIMISE_INDEX),
        constraints=[lambda Z: Z[..., -1]],
    )
    return acq_func
    

def optimize_acqf_and_get_observation(acq_func, constraint_bounds, data_type):
    """Optimizes the acquisition function, and returns a new candidate and the corresponding observation."""
    unnormalised_train_x, *_ = utils.generate_valid_initial_data(NUM_RESTARTS, INPUT_DATA_DIM, OBJECTIVE_DIM, data_set, constraint_set, obj_normalized_factors, t_type, device)
    sampled_initial_conditions = unnormalised_train_x.unsqueeze(1) # to match the dimension n * 1 * m
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=constraint_bounds,
        q=BATCH_SIZE,
        num_restarts=NUM_RESTARTS,
        options={"batch_limit": 1, "maxiter": 200},
        nonlinear_inequality_constraints = [constraint_set.get_nonlinear_inequality_constraints],
        batch_initial_conditions = sampled_initial_conditions,
    )
    # observe new values
    new_x = candidates.detach()
    new_exact_obj = data_set.find_ppa_result(new_x, data_type)
    new_normalised_obj = utils.normalise_output_data(new_exact_obj, obj_normalized_factors, device)
    new_con_obj = data_set.check_qNEHVI_constraints(new_normalised_obj)
    if new_con_obj.item() <= 0.0:
        hyper_vol = calculate_hypervolume(ref_points, new_normalised_obj)
    else:
        hyper_vol = 0.0
    new_train_obj = torch.cat([new_normalised_obj[...,:OBJECTIVES_TO_OPTIMISE_DIM], new_con_obj], dim=-1)
    # with_noise_new_train_obj = new_train_obj + torch.randn_like(new_train_obj) * NOISE_SE
    return new_x, new_exact_obj, new_train_obj, hyper_vol

if not debug:
    warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=NumericalWarning)
    warnings.filterwarnings("ignore", category=InputDataWarning)
    torch.set_printoptions(sci_mode=False)

if record:
    record_file_name = '../test/test_results/'
    for obj_name in OBJECTIVES_TO_OPTIMISE.keys():
        record_file_name = record_file_name + obj_name + '_'
    results_record = utils.recorded_training_result(INPUT_NAMES, OBJECTIVES_TO_OPTIMISE, data_set.best_value, data_set.best_pair, record_file_name, N_TRIALS, N_BATCH)

# Global Best Values
best_hyper_vol_per_trial = []
best_sample_points_per_trial = {trial : {input : 0.0 for input in INPUT_NAMES} for trial in range(1, N_TRIALS + 1)}

# This variable is temporarily used to match the data format of the SingleTaskGP_transformed, which is a copy of greattunes project on Github
GP_kernel_mapping_covar_identification = [
    {
        "name": "arch",
        "type": int,
        "column": 0,        
    },

    {
        "name": "arch",
        "type": int,
        "column": 1,        
    },

    {
        "name": "arch",
        "type": int,
        "column": 2,        
    },

]


#Optimisation Loop
for trial in range (1, N_TRIALS + 1):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ")
    (   train_x_ei,
        exact_obj_ei,
        train_obj_ei,
        hyper_vol_ei,
    ) = generate_initial_data(t_type)

    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei, GP_kernel_mapping_covar_identification)
    #reset the best observation
    best_observation_per_interation = {obj : None for obj in OBJECTIVES_TO_OPTIMISE.keys()}
    best_constraint_per_interation = {obj : None for obj in OUTPUT_OBJECTIVE_CONSTRAINT.keys()}
    best_sample_point_per_interation = {input : None for input in INPUT_NAMES}
    best_hyper_vol_per_interation = 0.0

    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()
        
        # fit the models
        fit_gpytorch_model(mll_ei)

        #QMC sampler
        qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
        acqf = build_qNEHVI_acqf(model_ei, train_x_ei, qmc_sampler)
        # optimize and get new observation
        new_x_ei, new_exact_obj_ei, new_train_obj_ei, hyper_vol = optimize_acqf_and_get_observation(acqf, constraint_set.constraint_bound, t_type)

        #--------------for debug------------------
        if debug:
            print("new_x_ei: ", new_x_ei)
            print("recovered new_x_ei: ", utils.recover_input_data(new_x_ei, INPUT_OFFSETS, INPUT_DATA_SCALES))
            print("new_train_obj_ei: ", new_train_obj_ei)
            print("hyper_vol: ", hyper_vol)
        #-----------------------------------------

        # update training points
        is_duplicate = any(torch.all(torch.isclose(new_x_ei, old_x), dim=-1) for old_x in train_x_ei)
        if not is_duplicate:
            train_x_ei   = torch.cat([train_x_ei, new_x_ei])
            train_obj_ei = torch.cat([train_obj_ei, new_train_obj_ei])
            hyper_vol_ei = torch.cat([hyper_vol_ei, torch.tensor(hyper_vol, device=device).unsqueeze(0)])
        # print("train x is ", train_x_ei)
        # print("train obj is ", train_obj_ei)
        # print("hyper vol is ", hyper_vol_ei)
        
        if hyper_vol > best_hyper_vol_per_interation:
            best_hyper_vol_per_interation = hyper_vol
            best_observation_per_interation = utils.encapsulate_obj_tensor_into_dict(OBJECTIVES_TO_OPTIMISE, new_exact_obj_ei)
            best_constraint_per_interation = utils.encapsulate_obj_tensor_into_dict(OUTPUT_OBJECTIVE_CONSTRAINT, new_exact_obj_ei[... , OBJECTIVES_TO_OPTIMISE_DIM :])
            best_sample_point_per_interation = utils.encapsulate_input_tensor_into_dict(new_x_ei, INPUT_NAMES)

        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei, GP_kernel_mapping_covar_identification)
        t1 = time.monotonic()

        if verbose:
            print(f"{Fore.YELLOW}Iteration: {iteration}{Style.RESET_ALL}")
            
            for obj in OBJECTIVES_TO_OPTIMISE.keys():
                if best_observation_per_interation[obj] is None:
                    print(f"{Fore.RED}best_value_{obj}: None{Style.RESET_ALL}")
                    continue
                if(OBJECTIVES_TO_OPTIMISE[obj] == 'minimise'):
                    print(f"{Fore.RED}best_value_{obj}: {-1 * best_observation_per_interation[obj]}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}best_value_{obj}: {best_observation_per_interation[obj]}{Style.RESET_ALL}")
            for obj in OUTPUT_OBJECTIVE_CONSTRAINT:
                print(f"{Fore.GREEN}check constraint_{obj}: {best_constraint_per_interation[obj]}{Style.RESET_ALL}")
        else:
            print(".", end="")
        
        if record:
            tmp_new_obj_ei = {}
            for obj in OBJECTIVES_TO_OPTIMISE.keys():
                if best_observation_per_interation[obj] is None:
                    continue
                if(OBJECTIVES_TO_OPTIMISE[obj] == 'minimise'):
                    tmp_new_obj_ei[obj] = -1 * best_observation_per_interation[obj]
                else:
                    tmp_new_obj_ei[obj] = best_observation_per_interation[obj]
            results_record.record(iteration, trial, tmp_new_obj_ei, t1-t0)
    

    best_hyper_vol_per_trial.append(best_hyper_vol_per_interation)
    best_sample_points_per_trial[trial] = best_sample_point_per_interation

    if record:
        results_record.record_input(trial, train_x_ei, hyper_vol_ei)

if record:
    results_record.store()
# Final stage, find the best sample point and the corresponding best observation
print("<------------------Final Result------------------>")
best_trial = utils.find_max_index_in_list(best_hyper_vol_per_trial)
best_objective = data_set.find_single_ppa_result(list(best_sample_points_per_trial[best_trial + 1].values()))
real_sample_point = utils.recover_single_input_data(best_sample_points_per_trial[best_trial + 1], INPUT_OFFSETS, INPUT_DATA_SCALES)
print(f"{Fore.BLUE}Best sample point: {real_sample_point}{Style.RESET_ALL}")
print(f"{Fore.BLUE}Best objective: {best_objective}{Style.RESET_ALL}")
