import torch
import data
import time
import utils
from colorama import Fore, Back, Style

from format_constraints import Input_Constraints
from botorch.models import SingleTaskGP
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.models.transforms.outcome import Standardize
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.utils.multi_objective.box_decompositions.non_dominated import (
    FastNondominatedPartitioning,
    NondominatedPartitioning
)
from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
from botorch.acquisition.multi_objective.monte_carlo import qExpectedHypervolumeImprovement

from botorch.optim import optimize_acqf
from botorch.acquisition import qExpectedImprovement
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_model


#Data Inputs
#Data_set 1
DATA_DIM = 3
DATA_SCALES = [1, 1, 1]
DATA_NORMALIZED_FACTOR = [12, 6, 255]    # normalized_Factor = max_value / scale
RAW_DATA_FILE = '../data/ppa_v2.db'

#Data_set 2
# DATA_DIM = 2
# DATA_SCALES = [1, 4]
# DATA_NORMALIZED_FACTOR = [6, 63]    # normalized_Factor = max_value / scale
# RAW_DATA_FILE = '../data/ppa.txt'

OBJECTIVES = {'estimated_clock_period': 'minimise', 'ncycles_matmul': 'minimise'}
OBJECTIVES_DIM = len(OBJECTIVES)
OBJECTIVE_TO_OPTIMISE = list(range(OBJECTIVES_DIM))
OUTPUT_OBJECTIVE_CONSTRAINT = {'lut': [0,20000], 'ff' : [0, 12000]}


#Model Settings
RAW_SAMPLES = 1
NOISE_SE = 0.5
NUM_RESTARTS = 2
N_TRIALS = 2            # number of trials of BO (outer loop)
N_BATCH = 50            # number of BO batches (inner loop)
BATCH_SIZE = 1          # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 16         # number of MC samples for qNEI


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
d_type = torch.int
t_type = torch.float64

data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES, OUTPUT_OBJECTIVE_CONSTRAINT, DATA_SCALES, DATA_NORMALIZED_FACTOR)
# data_set = data.read_data_from_txt(RAW_DATA_FILE, OBJECTIVES, DATA_SCALES, DATA_NORMALIZED_FACTOR)

#Reference point for Optimisation


constraint_set = Input_Constraints(DATA_DIM)

#TODO : write a interface to read the constraints from file
constraint_set.update_scale(DATA_SCALES)
constraint_set.update_normalize_factor(DATA_NORMALIZED_FACTOR)

#Data_set 1
constraint_set.update_self_constraints(0, [1, 12])
constraint_set.update_self_constraints(1, [5, 6])
constraint_set.update_self_constraints(2, [4, 255])

#Data_set 2
# constraint_set.update_self_constraints(0, [1, 6])
# constraint_set.update_self_constraints(1, [4, 252])
# constraint_set.update_new_constraints([{0: [1, 4], 1: [4, 4]}, {0: [5, 6], 1: [4, 252]}])



def calculate_hypervolume(ref_points, train_obj):
    """Calculate the hypervolume"""
    # Y dimension (batch_shape) x n x m-dim
    partitioning = NondominatedPartitioning(ref_point=ref_points, Y = train_obj[..., : ref_points.shape[0]])
    hv = partitioning.compute_hypervolume().item()
    return hv

def generate_initial_data(data_type):
    """generate training data"""
    train_x = constraint_set.create_initial_data(NUM_RESTARTS, data_type)
    exact_obj = data_set.find_ppa_result(train_x, BATCH_SIZE, data_type)
    normalised_obj = utils.normalise_output_data(exact_obj, normalized_factors)
    best_observed_value = calculate_hypervolume(ref_points, normalised_obj)
    return train_x, exact_obj, normalised_obj, best_observed_value

def generate_internal_bound(data_type):
    bounds = torch.empty((DATA_DIM, 2), dtype=data_type)
    scalas = torch.empty((DATA_DIM, 1), dtype=data_type)
    for i in range(DATA_DIM):
        bounds[i] = torch.tensor(constraint_set.Node[i].individual_constraints)
        scalas[i] = torch.tensor(constraint_set.Node[i].scale)
    return bounds, scalas.squeeze()


def initialize_model(train_x, train_obj):
    """define models for objective and constraint"""
    ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
    models = []
    for obj_index in range(OBJECTIVES_DIM): 
        train_y = train_obj[..., obj_index : obj_index + 1].squeeze(0)
        models.append(SingleTaskGP(train_x, train_y, outcome_transform=Standardize(m=1)))
    model = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    return mll, model

def build_multi_objective_acqf(model, train_obj, sampler):
    """Build the qEHVI acquisition function"""
    # partition non-dominated space into disjoint rectangles
    train_y = train_obj.squeeze(0)
    partitioning = FastNondominatedPartitioning(
        ref_point=ref_points,
        Y=train_y,
    )
    acq_func = qExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_points,
        partitioning=partitioning,
        objective=IdentityMCMultiOutputObjective(outcomes = OBJECTIVE_TO_OPTIMISE),
        sampler=sampler,
        constraints=data.check_output_constraints,
    )
    return acq_func

def optimize_acqf_and_get_observation(acq_func, generated_bounds):
    """Optimizes the acquisition function, and returns a new candidate and the corresponding observation."""
    sampled_initial_conditions = constraint_set.create_initial_data(NUM_RESTARTS, t_type).unsqueeze(1)
    
    # optimize
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=torch.transpose(generated_bounds, 0, 1),
        q=BATCH_SIZE,
        num_restarts=NUM_RESTARTS,
        options={"batch_limit": 1, "maxiter": 200},
        nonlinear_inequality_constraints = [constraint_set.get_nonlinear_inequality_constraints],
        batch_initial_conditions = sampled_initial_conditions,
    )

    # observe new values
    new_x = candidates.detach()
    new_exact_obj = data_set.find_ppa_result(new_x, BATCH_SIZE, t_type)
    new_normalised_obj = utils.normalise_output_data(new_exact_obj, normalized_factors)
    hyper_vol = calculate_hypervolume(ref_points, new_normalised_obj)
    return new_x, new_exact_obj, new_normalised_obj, hyper_vol



verbose = True
record = True
bounds, scalas = generate_internal_bound(t_type)
print("bounds: ", bounds, "scalas: ", scalas)
if record:
    results_record = utils.recorded_training_result(OBJECTIVES, data_set.best_value, data_set.best_pair, '../test/record_result.txt')

# Global Best Values
best_hyper_vol_per_trial = []
best_observation_per_trial = {trial : {obj : [] for obj in OBJECTIVES.keys()} for trial in range(1, N_TRIALS + 1)}

#Optimisation Loop
for trial in range (1, N_TRIALS + 1):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ")
    (   train_x_ei,
        exact_obj_ei,
        train_obj_ei,
        _,
    ) = generate_initial_data(t_type)
    
    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei)
    #reset the best observation
    best_observation_per_interation = {obj : None for obj in OBJECTIVES.keys()}
    best_hyper_vol_per_interation = 0.0

    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()
        # fit the models
        fit_gpytorch_model(mll_ei)

        #QMC sampler
        qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
        acqf = build_multi_objective_acqf(model_ei, train_obj_ei, qmc_sampler)

        # optimize and get new observation
        new_x_ei, new_exact_obj_ei, new_train_obj_ei, best_value_ei = optimize_acqf_and_get_observation(acqf, bounds)
        
        # update training points
        train_x_ei = torch.cat([train_x_ei, new_x_ei])
        train_obj_ei = torch.cat((train_obj_ei, new_train_obj_ei), dim=1)

        # update progress
        if best_value_ei > best_hyper_vol_per_interation:
            best_hyper_vol_per_interation = best_value_ei
            best_observation_per_interation = utils.encapsulate_obj_tensor_into_dict(OBJECTIVES, new_exact_obj_ei)

        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = initialize_model(
            train_x_ei,
            train_obj_ei,
        )
        t1 = time.monotonic()

        if verbose:
            print(f"{Fore.YELLOW}Iteration: {iteration}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}new x: {new_x_ei[0]}  == > new y: {new_exact_obj_ei}{Style.RESET_ALL}")
            for obj in OBJECTIVES.keys():
                if(OBJECTIVES[obj] == 'minimise'):
                    print(f"{Fore.RED}best_value_{obj}: {-1 * best_observation_per_interation[obj]}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}best_value_{obj}: {best_observation_per_interation[obj]}{Style.RESET_ALL}")
        else:
            print(".", end="")
        
        if record:
            #TODO: prepare for multi objectives
            tmp_best_value_ei = {}
            tmp_new_obj_ei = {}
            for obj in OBJECTIVES.keys():
                if(OBJECTIVES[obj] == 'minimise'):
                    tmp_best_value_ei[obj] = -1 * best_value_ei
                    tmp_new_obj_ei[obj] = -1 * best_observation_per_interation[obj]
                else:
                    tmp_best_value_ei[obj] =  best_value_ei
                    tmp_new_obj_ei[obj] = best_observation_per_interation[obj]
            results_record.record(iteration, tmp_best_value_ei, tmp_new_obj_ei, t1-t0)
    
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            best_observation_per_trial[trial][obj] = -1 * best_observation_per_interation[obj]
        else:
            best_observation_per_trial[trial][obj] = best_observation_per_interation[obj]
    best_hyper_vol_per_trial.append(best_hyper_vol_per_interation)
    
    print(f"{Fore.BLUE}Best value found: {best_hyper_vol_per_trial}{Style.RESET_ALL}")
if record:
    results_record.store()
