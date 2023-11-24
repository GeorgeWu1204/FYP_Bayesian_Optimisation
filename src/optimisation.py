import os
import torch
import data
import time

from format_constraints import Constraints
from botorch.models import SingleTaskGP
from botorch.models.transforms.outcome import Standardize
from gpytorch.mlls import ExactMarginalLogLikelihood

from botorch.optim import optimize_acqf
from botorch.acquisition import qExpectedImprovement
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch import fit_gpytorch_model

#Data variables
DATA_DIM = 2
DATA_SCALES = [1, 4]
DATA_NORMALIZED_FACTOR = [6, 63]    # normalized_Factor = max_value / scale
RAW_DATA_FILE = '../data/ppa.txt'
NOISE_SE = 0.5
OBJECTIVE = 'target_clock_period'
RAW_SAMPLES = 1

#BO variables
NUM_RESTARTS = 1
N_TRIALS = 1            # number of trials of BO (outer loop)
N_BATCH = 10             # number of BO batches (inner loop)
BATCH_SIZE = 1          # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 16         # number of MC samples for qNEI


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
d_type = torch.int
t_type = torch.float64

data_set = data.read_from_data(RAW_DATA_FILE, [OBJECTIVE], DATA_SCALES, DATA_NORMALIZED_FACTOR)
constraint_set = Constraints(DATA_DIM)

#TODO : write a interface to read the constraints from file
constraint_set.update_scale(DATA_SCALES)
constraint_set.update_normalize_factor(DATA_NORMALIZED_FACTOR)

constraint_set.update_self_constraints(0, [1, 6])
constraint_set.update_self_constraints(1, [4, 252])
constraint_set.update_new_constraints([{0: [1, 4], 1: [4, 4]}, {0: [5, 6], 1: [4, 252]}])


# define output constraints
def weighted_objective(X):
    """Feasibility weighted objective; zero if not feasible."""
    # if samples != None:
    #     print("samples: ", samples.shape, "\n", samples)
    return data_set.find_ppa_result(X, OBJECTIVE, t_type)

# define models and data

def generate_initial_data(data_type):
    """generate training data"""
    train_x = constraint_set.create_initial_data(NUM_RESTARTS, data_type)
    exact_obj = data_set.find_ppa_result(train_x, OBJECTIVE, data_type).unsqueeze(-1)  # add additional dimension at the last position
    best_observed_value = weighted_objective(train_x).max().item()
    return train_x, exact_obj, best_observed_value

def generate_internal_bound(data_type):
    bounds = torch.empty((DATA_DIM, 2), dtype=data_type)
    scalas = torch.empty((DATA_DIM, 1), dtype=data_type)
    for i in range(DATA_DIM):
        bounds[i] = torch.tensor(constraint_set.Node[i].individual_constraints)
        scalas[i] = torch.tensor(constraint_set.Node[i].scale)
    return bounds, scalas.squeeze()


def initialize_model(train_x, train_obj, state_dict=None):
    """define models for objective and constraint"""
    ### SingleTaskGP ###
    noise_free_model = SingleTaskGP(train_x, train_obj, outcome_transform=Standardize(m=1))
    mll = ExactMarginalLogLikelihood(noise_free_model.likelihood, noise_free_model)
    if state_dict is not None:
        noise_free_model.load_state_dict(state_dict)
    return mll, noise_free_model

def ic_generator(*args, **kwargs):
    # generate training data
    train_x = constraint_set.create_initial_data(NUM_RESTARTS, t_type)
    return train_x

def optimize_acqf_and_get_observation(acq_func, generated_bounds):
    """Optimizes the acquisition function, and returns a new candidate and a noisy observation."""

    sampled_initial_conditions = ic_generator().unsqueeze(1)
    sampled_initial_conditions.requires_grad = True
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
    new_obj = data_set.find_ppa_result(new_x, OBJECTIVE, t_type).unsqueeze(-1)
    return new_x, new_obj

verbose = True
bounds, scalas = generate_internal_bound(t_type)
print("bounds: ", bounds, "scalas: ", scalas)
# Global Best Values
best_observed_all = []
#Optimisation Loop
for trial in range (N_TRIALS):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ", end="")
    best_observed_ei = []

    (
        train_x_ei,
        train_obj_ei,
        best_observed_value_ei,
    ) = generate_initial_data( t_type)

    print("tran_x_ei: ", train_x_ei, "\ntran_obj_ei: ", train_obj_ei, "\nbest_observed_value_ei: ", best_observed_value_ei)

    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei)
    best_observed_ei.append(best_observed_value_ei)

    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()
        fit_gpytorch_model(mll_ei)  

        #QMC sampler
        qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
        qEI = qExpectedImprovement(
            model = model_ei,
            best_f = best_observed_value_ei,
            sampler=qmc_sampler,
        )

        # optimize and get new observation
        new_x_ei, new_obj_ei = optimize_acqf_and_get_observation(qEI, bounds)
        
        # update training points
        train_x_ei = torch.cat([train_x_ei, new_x_ei])
        train_obj_ei = torch.cat([train_obj_ei, new_obj_ei])
        

        # update progress
        best_value_ei = weighted_objective(train_x_ei).max().item()
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
            print("<---------------------------------------------------------------->")
            print("at iteration: ", iteration)
            print("new_x_ei: ", new_x_ei, "new_obj_ei: ", new_obj_ei)
            print("train_x_ei: ", train_x_ei)
            print("train_obj_ei: ", train_obj_ei)
            print("best_value_ei: ", best_value_ei)
            print("best_observed_ei: ", best_observed_ei)
            print(
                f"\nBatch {iteration:>2}: "
                f"time = {t1-t0:>4.2f}.",
                end="",
            )
            print("\n")
        else:
            print(".", end="")
    best_observed_all.append(best_observed_ei)
