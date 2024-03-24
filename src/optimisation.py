import torch
import data
import time
import utils
import warnings
from colorama import Fore, Style

from interface import parse_constraints
from sampler import initial_sampler
from optimisation_models import optimisation_models

from train_set import train_set_records
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
CONSTRAINT_FILE = '../specification/input_spec_optimisation_set_3.txt'
input_info, output_info, param_tuner = parse_constraints(CONSTRAINT_FILE, device)
print(input_info.input_names)
print(output_info.obj_to_optimise)
print(output_info.optimisation_target)

# Dataset Settings
if output_info.optimisation_target == 'synthetic':
    RAW_DATA_FILE = '../specification/ppa_v2.db'
    data_set = data.read_data_from_db(RAW_DATA_FILE, input_info, output_info, t_type, device)
elif output_info.optimisation_target == 'NutShell':
    data_set = data.NutShell_Data(input_info, output_info, param_tuner, t_type, device)
elif output_info.optimisation_target == 'EL2':
    data_set = data.EL2_Data(input_info, output_info, param_tuner, t_type, device)

print("<-------------- Optimisation Settings -------------->")
print(f"Input Names: {input_info.input_names}")
print(f"Input Self Constraints: {input_info.self_constraints}")
print(f"Input Offset: {input_info.input_offsets}")
print(f"Input Scales: {input_info.input_scales}")
print(f"Input Normalised Factor: {input_info.input_normalized_factor}")
print(f"Input Exponential: {input_info.input_exp}")
print(f"Optimisation Device : {output_info.optimisation_target}")
print(f"Objectives to Optimise: {output_info.obj_to_optimise}")
print(f"Output Objective Constraint: {output_info.output_constraints}")
print("<--------------------------------------------------->")

# Train Set Settings
TRAIN_SET_DISTURBANCE_RANGE = 0.01                  # noise standard deviation for objective
TRAIN_SET_ACCEPTABLE_THRESHOLD = 0.2                # acceptable distance between the rounded vertex and the real vertex

# Model Settings
NUM_RESTARTS = 4                # number of starting points for BO for optimize_acqf
NUM_OF_INITIAL_POINT = 16       # number of initial points for BO  Note: has to be power of 2 for sobol sampler
N_TRIALS = 1                    # number of trials of BO (outer loop)
N_BATCH = 50                    # number of BO batches (inner loop)
BATCH_SIZE = 1                  # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 128                # number of MC samples for qNEI
RAW_SAMPLES = 8                 # number of raw samples for qNEI

# Runtime Settings
verbose = True
record = True
debug = True
plot_posterior = False


#reference point for optimisation used for hypervolume calculation
ref_points = utils.find_ref_points(output_info.obj_to_optimise_dim, data_set.objs_direct, t_type, device)
#normalise objective to ensure the same scale
sampler_generator = initial_sampler(input_info.input_dim, output_info.obj_to_evaluate_dim, input_info.constraints, data_set, t_type, device)
train_set_storage = train_set_records(input_info.input_normalized_factor, list(input_info.self_constraints.values()), ref_points, output_info.obj_to_optimise_dim, TRAIN_SET_ACCEPTABLE_THRESHOLD, TRAIN_SET_DISTURBANCE_RANGE, t_type, device)

if plot_posterior:
    posterior_examiner = utils.test_posterior_result(input_info.input_names, t_type, device)
    posterior_objective_index = 0


if not debug:
    warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=NumericalWarning)
    warnings.filterwarnings("ignore", category=InputDataWarning)
    torch.set_printoptions(sci_mode=False)

if record:
    record_file_name = '../test/test_results/'
    for obj_name in output_info.obj_to_optimise.keys():
        record_file_name = record_file_name + obj_name + '_'
    results_record = utils.recorded_training_result(input_info.input_names, output_info.obj_to_optimise, data_set.best_value, record_file_name, N_TRIALS, N_BATCH)
# Global Best Values
best_hyper_vols_per_trial = []
best_sample_points_per_trial = {trial : {input : 0.0 for input in input_info.input_names} for trial in range(1, N_TRIALS + 1)}
optimisation_model = optimisation_models(NUM_RESTARTS, NUM_OF_INITIAL_POINT, BATCH_SIZE, RAW_SAMPLES, MC_SAMPLES, ref_points, output_info.obj_to_optimise_dim, t_type, device)

#Optimisation Loop
for trial in range (1, N_TRIALS + 1):

    print(f"\nTrial {trial:>2} of {N_TRIALS} ")
    
    (   train_x_ei,
        exact_obj_ei,
        train_obj_ei,
        hyper_vol_ei,
    ) = data.generate_initial_data(sampler_generator, NUM_OF_INITIAL_POINT, data_set, ref_points, device, output_info.obj_to_optimise_dim)
    
    print("<----------------Initial Data--------------->")
    print("train_x_ei: ", train_x_ei)
    print("train_obj_ei: ", train_obj_ei)
    print("hyper_vol_ei: ", hyper_vol_ei)
    print("<------------------------------------------->")

    train_set_storage.store_initial_data(train_x_ei)
    mll_ei, model_ei = optimisation_model.initialize_model(train_x_ei, train_obj_ei)
    #reset the best observation
    # best_observation_per_interation = {obj : None for obj in OBJECTIVES_TO_OPTIMISE.keys()}
    # best_constraint_per_interation = {obj : None for obj in OUTPUT_OBJECTIVE_CONSTRAINT.keys()}
    # best_hyper_vol_per_interation = 0.0
    best_sample_point_per_interation, best_observation_per_interation, best_constraint_per_interation, best_hyper_vol_per_interation = \
        utils.extract_best_from_initialisation_results(train_x_ei, exact_obj_ei, hyper_vol_ei, output_info.obj_to_optimise, output_info.output_constraints)
    for iteration in range(1, N_BATCH + 1):
        t0 = time.monotonic()

        # fit the models
        fit_gpytorch_model(mll_ei)

        #QMC sampler
        qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
        acqf = optimisation_model.build_qNEHVI_acqf(model_ei, train_x_ei, qmc_sampler)
        # optimize and get new observation
        valid_generated_sample, new_x_ei, new_exact_obj_ei, new_train_obj_ei, hyper_vol = optimisation_model.optimize_acqf_and_get_observation(acqf, data_set)

        # examine the posterior
        if plot_posterior and iteration == 10:
            posterior_examiner.examine_posterior(model_ei.subset_output([posterior_objective_index]), iteration)
            # posterior_examiner.examine_acq_function(acqf, iteration)

        #--------------for debug------------------
        # if debug:
        #     if valid_generated_sample:
        #         print("new_x_ei: ", new_x_ei)
        #         print("recovered new_x_ei: ", utils.recover_all_input_data(new_x_ei.squeeze(0), INPUT_NORMALIZED_FACTOR, INPUT_DATA_SCALES,INPUT_OFFSETS, t_type, device))
        #         print("new_exact_obj_ei: ", new_exact_obj_ei)
        #         print("hyper_vol: ", hyper_vol)
        #     else:
        #         print("No valid sample found")
        #-----------------------------------------

        # update training points
        valid_point_for_storage, modified_new_train_x, modified_new_train_obj_ei, modified_hyper_vol  = train_set_storage.store_new_data(valid_generated_sample, new_x_ei, new_train_obj_ei, hyper_vol, data_set)
        
        #--------------for debug------------------
        if debug:
            print("modified_new_train_x: ", modified_new_train_x)
            print("modified_new_train_obj_ei: ", modified_new_train_obj_ei)
            print("modified_hyper_vol: ", modified_hyper_vol)

        if valid_point_for_storage:
            train_x_ei   = torch.cat([train_x_ei, modified_new_train_x])
            train_obj_ei = torch.cat([train_obj_ei, modified_new_train_obj_ei])
            hyper_vol_ei = torch.cat([hyper_vol_ei, modified_hyper_vol])
            if hyper_vol > best_hyper_vol_per_interation:
                best_hyper_vol_per_interation = hyper_vol
                best_observation_per_interation = utils.encapsulate_obj_tensor_into_dict(output_info.obj_to_optimise, new_exact_obj_ei)
                best_constraint_per_interation = utils.encapsulate_obj_tensor_into_dict(output_info.output_constraints, new_exact_obj_ei[... , output_info.obj_to_optimise_dim :])
                best_sample_point_per_interation = new_x_ei
        
        # reinitialize the models so they are ready for fitting on next iteration
        mll_ei, model_ei = optimisation_model.initialize_model(train_x_ei, train_obj_ei)
        t1 = time.monotonic()

        if verbose:
            print(f"{Fore.YELLOW}Iteration: {iteration}{Style.RESET_ALL}")
            
            for obj in output_info.obj_to_optimise.keys():
                if best_observation_per_interation[obj] is None:
                    print(f"{Fore.RED}best_value_{obj}: None{Style.RESET_ALL}")
                    continue
                if(output_info.obj_to_optimise[obj] == 'minimise'):
                    print(f"{Fore.RED}best_value_{obj}: {-1 * best_observation_per_interation[obj]}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}best_value_{obj}: {best_observation_per_interation[obj]}{Style.RESET_ALL}")
            for obj in output_info.output_constraints:
                print(f"{Fore.GREEN}check constraint_{obj}: {best_constraint_per_interation[obj]}{Style.RESET_ALL}")
        else:
            print(".", end="")
        
        if record:
            tmp_new_obj_ei = {}
            for obj in output_info.obj_to_optimise.keys():
                if best_observation_per_interation[obj] is None:
                    continue
                if(output_info.obj_to_optimise[obj] == 'minimise'):
                    tmp_new_obj_ei[obj] = -1 * best_observation_per_interation[obj]
                else:
                    tmp_new_obj_ei[obj] = best_observation_per_interation[obj]
            results_record.record(iteration, trial, tmp_new_obj_ei, t1-t0)
    
    print("best_sample_point_per_interation: ", best_sample_point_per_interation)
    best_hyper_vols_per_trial.append(best_hyper_vol_per_interation)
    best_sample_points_per_trial[trial] = best_sample_point_per_interation

    if record:
        unnormalized_train_x = utils.recover_unrounded_input_data(train_x_ei, input_info, t_type, device)
        results_record.record_input(trial, unnormalized_train_x, hyper_vol_ei)

if record:
    results_record.store()
# Final stage, find the best sample point and the corresponding best observation
print("<------------------Final Result------------------>")
best_trial = utils.find_max_index_in_list(best_hyper_vols_per_trial)
_, best_objective = data_set.find_ppa_result(best_sample_points_per_trial[best_trial + 1])
print("best_sample_points_per_trial: ", best_sample_points_per_trial[best_trial + 1])
real_sample_point = utils.recover_single_input_data(best_sample_points_per_trial[best_trial + 1].squeeze(0), input_info.input_normalized_factor, input_info.input_scales, input_info.input_offsets, input_info.input_exp)
print(f"{Fore.BLUE}Best sample point: {real_sample_point}{Style.RESET_ALL}")
print(f"{Fore.BLUE}Best objective: {best_objective}{Style.RESET_ALL}")
