import torch
import data
import time
import utils
import warnings
from colorama import Fore, Style

from interface import fill_constraints, parse_constraints
from sampler import initial_sampler
from customised_model import SingleTaskGP_transformed
from train_set import train_set_records

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


# Tensor Settings
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
t_type = torch.float64

# Input Settings
CONSTRAINT_FILE = '../data/input_spec2.txt'
self_constraints, coupled_constraints, INPUT_CONSTANT, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, objective_function_category, parameter_tuning_obj = parse_constraints(CONSTRAINT_FILE)
(INPUT_DATA_DIM, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_NAMES), constraint_set = fill_constraints(self_constraints, coupled_constraints, device)

OBJECTIVES_TO_OPTIMISE_DIM = len(OBJECTIVES_TO_OPTIMISE)
OBJECTIVE_DIM = OBJECTIVES_TO_OPTIMISE_DIM + len(OUTPUT_OBJECTIVE_CONSTRAINT)
OBJECTIVES_TO_OPTIMISE_INDEX = list(range(OBJECTIVES_TO_OPTIMISE_DIM))

# Dataset Settings
if objective_function_category == 'synthetic':
    print("Optimisation in pre-prepared dataset")
    RAW_DATA_FILE = '../data/ppa_v2.db'
    data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_CONSTANT , t_type, device)
else:
    print("Optimisation in real space")
    data_set = data.Explore_Data(OBJECTIVES_TO_OPTIMISE, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_CONSTANT, OUTPUT_OBJECTIVE_CONSTRAINT, parameter_tuning_obj, t_type, device)


# Train Set Settings
TRAIN_SET_DISTURBANCE_RANGE = 0.01                 # noise standard deviation for objective
TRAIN_SET_ACCEPTABLE_THRESHOLD = 0.2            # acceptable distance between the rounded vertex and the real vertex

# Model Settings
NUM_RESTARTS = 1                # number of starting points for BO for optimize_acqf
NUM_OF_INITIAL_POINT = 3        # number of initial points for BO  Note: has to be power of 2 for sobol sampler
N_TRIALS = 1                    # number of trials of BO (outer loop)
N_BATCH = 10                    # number of BO batches (inner loop)
BATCH_SIZE = 1                  # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 1                  # number of MC samples for qNEI

# Runtime Settings
verbose = True
record = True
debug = False
plot_posterior = False


#reference point for optimisation used for hypervolume calculation
ref_points = utils.find_ref_points(OBJECTIVES_TO_OPTIMISE_DIM, OBJECTIVES_TO_OPTIMISE, data_set.worst_value, data_set.output_normalised_factors, t_type, device)

#normalise objective to ensure the same scale
obj_normalized_factors = list(data_set.output_normalised_factors.values())
sampler_generator = initial_sampler(INPUT_DATA_DIM, constraint_set, data_set, t_type, device)
train_set_storage = train_set_records(INPUT_NORMALIZED_FACTOR, TRAIN_SET_ACCEPTABLE_THRESHOLD, TRAIN_SET_DISTURBANCE_RANGE, t_type, device)

if plot_posterior:
    posterior_examiner = utils.test_posterior_result(INPUT_DATA_DIM, t_type, device)
    posterior_objective_index = 1

def calculate_hypervolume(ref_points, train_obj):
    """Calculate the hypervolume"""
    # Y dimension (batch_shape) x n x m-dim
    partitioning = NondominatedPartitioning(ref_point=ref_points, Y = train_obj[..., : OBJECTIVES_TO_OPTIMISE_DIM])

    hv = partitioning.compute_hypervolume().item()
    return hv

def generate_initial_data():
    """generate training data"""
    unnormalised_train_x, exact_objs, con_objs, normalised_objs = sampler_generator.generate_valid_initial_data(NUM_OF_INITIAL_POINT, OBJECTIVE_DIM, data_set, obj_normalized_factors)
    train_obj = torch.cat([normalised_objs[...,:OBJECTIVES_TO_OPTIMISE_DIM], con_objs], dim=-1)
    # with_noise_train_obj = train_obj + torch.randn_like(train_obj) * NOISE_SE
    generate_size = train_obj.shape[0]
    hypervolumes = torch.zeros(generate_size, device=device)
    for i in range(generate_size):
        hypervolumes[i] = calculate_hypervolume(ref_points, train_obj[i].unsqueeze(0))
    return unnormalised_train_x, exact_objs, train_obj, hypervolumes

def initialize_model(train_x, train_obj, scales, normalized_factors):
    """define models for objective and constraint"""
    ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
    models = []
    
    for obj_index in range(train_obj.shape[-1]): 
        train_y = train_obj[..., obj_index : obj_index + 1]
        models.append(SingleTaskGP_transformed(
                                    scales,
                                    normalized_factors,
                                    train_x, 
                                    train_y, 
                                #    likelihood=MODEL_LIKELIHOOD, 
                                    outcome_transform=Standardize(m=1),
                                    tensor_type=t_type,
                                    tensor_device=device
                                   ))
       
    model = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    return mll, model


def build_qNEHVI_acqf(model, train_x, sampler):
    """Build the qNEHVI acquisition function"""
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
    unnormalised_train_x, *_ = sampler_generator.generate_valid_initial_data(NUM_RESTARTS, OBJECTIVE_DIM, data_set, obj_normalized_factors)
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
    new_exact_obj = data_set.find_ppa_result(new_x)
    new_normalised_obj = utils.normalise_output_data(new_exact_obj, obj_normalized_factors, device)
    new_con_obj = data_set.check_qNEHVI_constraints(new_normalised_obj)
    if new_con_obj.item() <= 0.0:
        hyper_vol = calculate_hypervolume(ref_points, new_normalised_obj)
    else:
        hyper_vol = 0.0
    new_train_obj = torch.cat([new_normalised_obj[...,:OBJECTIVES_TO_OPTIMISE_DIM], new_con_obj], dim=-1)
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
    results_record = utils.recorded_training_result(INPUT_NAMES, OBJECTIVES_TO_OPTIMISE, data_set.best_value, record_file_name, N_TRIALS, N_BATCH)

# Global Best Values
best_hyper_vol_per_trial = []
best_sample_points_per_trial = {trial : {input : 0.0 for input in INPUT_NAMES} for trial in range(1, N_TRIALS + 1)}

#Optimisation Loop
for trial in range (1, N_TRIALS + 1):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ")
    (   train_x_ei,
        exact_obj_ei,
        train_obj_ei,
        hyper_vol_ei,
    ) = generate_initial_data()
    train_set_storage.store_initial_data(train_x_ei)
    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR)

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

        # examine the posterior
        if plot_posterior and iteration == 10:
            # posterior_examiner.examine_posterior(model_ei.subset_output([posterior_objective_index]), iteration)
            posterior_examiner.examine_acq_function(acqf, iteration)
        #--------------for debug------------------
        if debug:
            print("new_x_ei: ", new_x_ei)
            print("recovered new_x_ei: ", utils.recover_all_input_data(new_x_ei.squeeze(0), INPUT_NORMALIZED_FACTOR, INPUT_DATA_SCALES,INPUT_OFFSETS, t_type, device))
            print("new_train_obj_ei: ", new_train_obj_ei)
            print("hyper_vol: ", hyper_vol)
        #-----------------------------------------


        # update training points
        valid_point, modified_new_train_x, modified_new_train_obj_ei, modified_hyper_vol  = train_set_storage.store_new_data(new_x_ei, new_train_obj_ei, hyper_vol)
        
        #--------------for debug------------------
        if debug:
            print("modified_new_train_x: ", modified_new_train_x)
            print("modified_new_train_obj_ei: ", modified_new_train_obj_ei)
            print("modified_hyper_vol: ", modified_hyper_vol)

        if valid_point:
            train_x_ei   = torch.cat([train_x_ei, modified_new_train_x])
            train_obj_ei = torch.cat([train_obj_ei, modified_new_train_obj_ei])
            hyper_vol_ei = torch.cat([hyper_vol_ei, modified_hyper_vol])
            if hyper_vol > best_hyper_vol_per_interation:
                best_hyper_vol_per_interation = hyper_vol
                best_observation_per_interation = utils.encapsulate_obj_tensor_into_dict(OBJECTIVES_TO_OPTIMISE, new_exact_obj_ei)
                best_constraint_per_interation = utils.encapsulate_obj_tensor_into_dict(OUTPUT_OBJECTIVE_CONSTRAINT, new_exact_obj_ei[... , OBJECTIVES_TO_OPTIMISE_DIM :])
                best_sample_point_per_interation = new_x_ei
        

        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR)
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
        unnormalized_train_x = utils.recover_unrounded_input_data(train_x_ei, INPUT_NORMALIZED_FACTOR, INPUT_DATA_SCALES, INPUT_OFFSETS, t_type, device)
        results_record.record_input(trial, unnormalized_train_x, hyper_vol_ei)

if record:
    results_record.store()
# Final stage, find the best sample point and the corresponding best observation
print("<------------------Final Result------------------>")
best_trial = utils.find_max_index_in_list(best_hyper_vol_per_trial)
best_objective = data_set.find_ppa_result(best_sample_points_per_trial[best_trial + 1])
real_sample_point = utils.recover_all_input_data(best_sample_points_per_trial[best_trial + 1], INPUT_NORMALIZED_FACTOR, INPUT_DATA_SCALES, INPUT_OFFSETS, t_type, device)
print(f"{Fore.BLUE}Best sample point: {real_sample_point}{Style.RESET_ALL}")
print(f"{Fore.BLUE}Best objective: {best_objective}{Style.RESET_ALL}")
