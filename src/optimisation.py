import os
import torch
import data
import time
import warnings

from format_constraints import Constraints
from botorch.models import SingleTaskGP
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.optim import optimize_acqf
from botorch.acquisition import qExpectedImprovement
from botorch.sampling.normal import NormalSampler
from botorch.exceptions import BadInitialCandidatesWarning
from botorch import fit_gpytorch_model
#Data variables
DATA_DIM = 2
DATA_SCALES = [1, 4]
RAW_DATA_FILE = '../ppa.txt'
NOISE_SE = 0.5
OBJECTIVE = 'avail_ff'
RAW_SAMPLES = 32

#BO variables
NUM_RESTARTS = 1
N_TRIALS = 1            # number of trials of BO (outer loop)
N_BATCH = 1             # number of BO batches (inner loop)
BATCH_SIZE = 1
MC_SAMPLES = 16         # number of MC samples for qNEI


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
dtype = torch.int64


#TODO
constraint_set.update_scale(1, 4)
constraint_set.update_self_constraints(0, [1, 6])
constraint_set.update_self_constraints(1, [4, 252])
constraint_set.update_new_constraints([{0: [1, 4], 1: [4, 4]}, {0: [5, 6], 1: [4, 252]}])


# define output constraints
def weighted_obj(X):
    """Feasibility weighted objective; zero if not feasible."""
    return data_set.find_ppa_result(X, OBJECTIVE, dtype)

# define models and data

def generate_initial_data(bounds, dtype):
    # generate training data
    train_x = constraint_set.create_initial_data(NUM_RESTARTS, bounds, dtype)
    exact_obj = data_set.find_ppa_result(train_x, OBJECTIVE, dtype).unsqueeze(-1)  # add additional dimension at the last position
    best_observed_value = weighted_obj(train_x).max().item()
    return train_x, exact_obj, best_observed_value

def generate_internal_bound():
    bounds = torch.empty((DATA_DIM, 2), dtype=dtype)
    scalas = torch.empty((DATA_DIM, 1), dtype=dtype)
    for i in range(DATA_DIM):
        bounds[i] = torch.tensor([x / constraint_set.Node[i].scale for x in constraint_set.Node[i].individual_constraints])
        scalas[i] = torch.tensor(constraint_set.Node[i].scale)
    return bounds, scalas.squeeze()


def initialize_model(train_x, train_obj, state_dict=None):
    # define models for objective and constraint
    train_Yvar = torch.full_like(train_obj, 1e-6)
    noise_free_model = SingleTaskGP(
        train_x, train_obj, train_Yvar
    )
    mll = SumMarginalLogLikelihood(noise_free_model.likelihood, noise_free_model)
    # load state dict if it is passed
    if state_dict is not None:
        noise_free_model.load_state_dict(state_dict)
    return mll, noise_free_model



def optimize_acqf_and_get_observation(acq_func):
    """Optimizes the acquisition function, and returns a new candidate and a noisy observation."""
    # optimize
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=bounds,
        q=BATCH_SIZE,
        num_restarts=NUM_RESTARTS,
        raw_samples=RAW_SAMPLES,  # used for intialization heuristic
        options={"batch_limit": 5, "maxiter": 200},
    )
    # observe new values
    new_x = candidates.detach()
    new_obj = data_set.find_ppa_result(new_x, OBJECTIVE).unsqueeze(-1) 
    return new_x, new_obj


def update_random_observations(best_random):
    """Simulates a random policy by taking a the current list of best values observed randomly,
    drawing a new random point, observing its value, and updating the list.
    """
    rand_x = torch.rand(BATCH_SIZE, 6)
    next_random_best = weighted_obj(rand_x).max().item()
    best_random.append(max(best_random[-1], next_random_best))
    return best_random


train_yvar = torch.tensor(NOISE_SE**2, device=device, dtype=dtype)
data_set = data.read_from_data(RAW_DATA_FILE, [OBJECTIVE], DATA_SCALES)
constraint_set = Constraints(DATA_DIM)
verbose = True
bounds, scalas = generate_internal_bound()
# Global Best Values
best_observed_all, best_random_all = [], []

#Optimisation Loop
for trial in range (N_TRIALS):
    print(f"\nTrial {trial:>2} of {N_TRIALS} ", end="")
    best_observed_ei, best_random = [], []

    (
        train_x_ei,
        train_obj_ei,
        best_observed_value_ei,
    ) = generate_initial_data(bounds, dtype)

    mll_ei, model_ei = initialize_model(train_x_ei, train_obj_ei)

    best_observed_ei.append(best_observed_value_ei)
    best_random.append(best_observed_value_ei)

    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()

        # Clearing house for fitting models passed as GPyTorch MarginalLogLikelihoods.
        fit_gpytorch_model(mll_ei)  
        #QMC sampler
        qmc_sampler = NormalSampler(num_samples=MC_SAMPLES)
        qEI = qExpectedImprovement(
            model=model_ei,
            best_f=best_observed_value_ei,
            sampler=qmc_sampler,
            objective=weighted_obj,
        )
        # optimize and get new observation
        new_x_ei, new_obj_ei = optimize_acqf_and_get_observation(qEI)

        # update training points
        train_x_ei = torch.cat([train_x_ei, new_x_ei])
        train_obj_ei = torch.cat([train_obj_ei, new_obj_ei])

        # update progress
        best_random = update_random_observations(best_random)
        best_value_ei = weighted_obj(train_x_ei).max().item()
        best_observed_ei.append(best_value_ei)
        
        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = initialize_model(
            train_x_ei,
            train_obj_ei,
        )
        t1 = time.monotonic()

        if verbose:
            print(
                f"\nBatch {iteration:>2}: best_value (random, qEI, qNEI) = "
                f"({max(best_random):>4.2f}, {best_value_ei:>4.2f}, {best_value_nei:>4.2f}), "
                f"time = {t1-t0:>4.2f}.",
                end="",
            )
        else:
            print(".", end="")
    best_observed_all.append(best_observed_ei)
    best_random_all.append(best_random)