import torch
import data
import time
import utils
from colorama import Fore, Back, Style

from format_constraints import Constraints
from botorch.models import SingleTaskGP
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.models.transforms.outcome import Standardize
from gpytorch.mlls import ExactMarginalLogLikelihood
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood

from botorch.optim import optimize_acqf
from botorch.acquisition import qExpectedImprovement
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_model

#Data variables

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

NOISE_SE = 0.5

OBJECTIVES = {'lut': 'minimise'}
RAW_SAMPLES = 1

#BO variables
NUM_RESTARTS = 2
N_TRIALS = 2            # number of trials of BO (outer loop)
N_BATCH = 10             # number of BO batches (inner loop)
BATCH_SIZE = 1          # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 16         # number of MC samples for qNEI


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
d_type = torch.int
t_type = torch.float64

data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES, DATA_SCALES, DATA_NORMALIZED_FACTOR)
# data_set = data.read_data_from_txt(RAW_DATA_FILE, OBJECTIVES, DATA_SCALES, DATA_NORMALIZED_FACTOR)
constraint_set = Constraints(DATA_DIM)

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


# define models and data

def generate_initial_data(data_type):
    """generate training data"""
    train_x = constraint_set.create_initial_data(NUM_RESTARTS, data_type)
    exact_obj = data_set.find_ppa_result(train_x, OBJECTIVES, data_type)
    best_observed_value = exact_obj.max().item()
    return train_x, exact_obj, best_observed_value

def generate_internal_bound(data_type):
    bounds = torch.empty((DATA_DIM, 2), dtype=data_type)
    scalas = torch.empty((DATA_DIM, 1), dtype=data_type)
    for i in range(DATA_DIM):
        bounds[i] = torch.tensor(constraint_set.Node[i].individual_constraints)
        scalas[i] = torch.tensor(constraint_set.Node[i].scale)
    return bounds, scalas.squeeze()


def initialize_model(train_x, train_obj):
    """define models for objective and constraint"""
    ### Model selection: When multiple independent output training on the same data, otherwise MultiTaskGP ###
    models = []
    for obj_index in range(len(OBJECTIVES)): 
        train_y = train_obj[..., obj_index : obj_index + 1]
        models.append(SingleTaskGP(train_x, train_y, outcome_transform=Standardize(m=1)))
    model = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    # mll = ExactMarginalLogLikelihood(noise_free_model.likelihood, noise_free_model)
    return mll, model


def optimize_acqf_and_get_observation(acq_func, generated_bounds):
    """Optimizes the acquisition function, and returns a new candidate and a noisy observation."""

    sampled_initial_conditions = constraint_set.create_initial_data(NUM_RESTARTS, t_type).unsqueeze(1)
    # optimize
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=torch.transpose(generated_bounds, 0, 1),
        q=BATCH_SIZE,
        num_restarts=NUM_RESTARTS,
        options={"batch_limit": 1, "maxiter": 200},
        nonlinear_inequality_constraints = [constraint_set.get_nonlinear_inequality_constraints],
        batch_initial_conditions = sampled_initial_conditions
    )
    # observe new values
    new_x = candidates.detach()
    new_obj = data_set.find_ppa_result(new_x, OBJECTIVES, t_type)
    return new_x, new_obj

verbose = True
record = True
bounds, scalas = generate_internal_bound(t_type)
print("bounds: ", bounds, "scalas: ", scalas)
if record:
    results_record = utils.recorded_training_result(OBJECTIVES, data_set.best_value, data_set.best_pair, '../test/record_result.txt')

# Global Best Values
best_observed_all = []

#Optimisation Loop
for trial in range (1, N_TRIALS + 1):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ")
    best_observed_ei = []

    (   train_x_ei,
        train_obj_ei,
        best_value_ei,
    ) = generate_initial_data(t_type)

    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei)

    best_observed_ei.append(best_value_ei)

    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()
        # fit the models
        fit_gpytorch_model(mll_ei)

        #QMC sampler
        qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
        
        qEI = qExpectedImprovement(
            model = model_ei,
            best_f = best_value_ei,
            sampler=qmc_sampler,
        )

        # optimize and get new observation
        new_x_ei, new_obj_ei = optimize_acqf_and_get_observation(qEI, bounds)
        
        # update training points
        train_x_ei = torch.cat([train_x_ei, new_x_ei])
        train_obj_ei = torch.cat([train_obj_ei, new_obj_ei])
        

        # update progress
        best_value_ei = train_obj_ei.max().item()
        best_observed_ei.append(best_value_ei)
        

        # TODO: There is a warning in initialize model standardize data
        # scaler = StandardScaler()
        # standardized_data = scaler.fit_transform(train_obj_ei)
        # print("standardized_data: ", standardized_data)

        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = initialize_model(
            train_x_ei,
            train_obj_ei,
        )
        t1 = time.monotonic()

        if verbose:
            print(f"{Fore.YELLOW}Iteration: {iteration}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}new x: {new_x_ei[0]}  == > new y: {new_obj_ei}{Style.RESET_ALL}")
            for obj in OBJECTIVES.keys():
                if(OBJECTIVES[obj] == 'minimise'):
                    print(f"{Fore.RED}best_value_{obj}: {-1 * best_value_ei}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}best_value_{obj}: {best_value_ei}{Style.RESET_ALL}")
        else:
            print(".", end="")
        
        if record:
            #TODO: prepare for multi objectives
            for obj in OBJECTIVES.keys():
                if(OBJECTIVES[obj] == 'minimise'):
                    tmp_best_value_ei = {obj: -1 * best_value_ei}
                    tmp_new_obj_ei = {obj: -1 * new_obj_ei.item()}
                else:
                    tmp_best_value_ei = {obj: best_value_ei}
                    tmp_new_obj_ei = {obj: new_obj_ei.item()}
            results_record.record(iteration, tmp_best_value_ei, tmp_new_obj_ei, t1-t0)
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            best_observed_all.append(-1 * best_value_ei)
        else:
            best_observed_all.append(best_value_ei)
    
    print(f"{Fore.BLUE}Best value found: {best_observed_all}{Style.RESET_ALL}")
if record:
    results_record.store()
