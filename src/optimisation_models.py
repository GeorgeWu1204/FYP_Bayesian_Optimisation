import random
import time
import torch
from utils import calculate_hypervolume, encapsulate_obj_tensor_into_dict
from colorama import Fore, Style

from customised_model import SingleTaskGP_transformed
from botorch.models.transforms.outcome import Standardize
from botorch.models.model_list_gp_regression import ModelListGP
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.acquisition.multi_objective.monte_carlo import qNoisyExpectedHypervolumeImprovement
from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
from botorch.optim import optimize_acqf
### Implemented Models


class optimisation_model():
    def __init__(self, NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, input_info, output_info, ref_points, device, t_type):
        self.NUM_RESTARTS = NUM_RESTARTS
        self.RAW_SAMPLES = RAW_SAMPLES
        self.BATCH_SIZE = BATCH_SIZE
        self.OBJECTIVES_TO_OPTIMISE_INDEX = output_info.obj_to_optimise_index
        self.OBJECTIVES_TO_OPTIMISE_DIM = output_info.obj_to_optimise_dim
        self.ref_points = ref_points
        self.input_info = input_info
        self.output_info = output_info  
        self.device = device
        self.t_type = t_type

    def initialize_model(self, train_x, train_obj):
        """define models for objective and constraint"""
        ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
        models = []
        for obj_index in range(train_obj.shape[-1]): 
            train_y = train_obj[..., obj_index : obj_index + 1]
            models.append(SingleTaskGP_transformed(
                                        self.input_info.input_scales,
                                        self.input_info.input_normalized_factor,
                                        train_x, 
                                        train_y, 
                                        outcome_transform=Standardize(m=1),
                                        tensor_type=self.t_type,
                                        tensor_device=self.device
                                    ))
        
        model = ModelListGP(*models)
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        return mll, model


    def build_qNEHVI_acqf(self, model, train_x, sampler):
        """Build the qNEHVI acquisition function"""

        acq_func = qNoisyExpectedHypervolumeImprovement(
            model=model,
            ref_point=self.ref_points.tolist(), 
            X_baseline=train_x,
            sampler=sampler,
            prune_baseline=True,
            objective=IdentityMCMultiOutputObjective(outcomes = self.OBJECTIVES_TO_OPTIMISE_INDEX),
            constraints=[lambda Z: Z[..., -1]],
        )
        return acq_func
    

    def optimize_acqf_and_get_observation(self, acq_func, data_set):
        """Optimizes the acquisition function, and returns a new candidate and the corresponding observation."""
        # TODO: Noticed that if there is an input constraint, the points are selected from the generated condition.
        # initial_cond = sampler_generator.generate_initial_data(NUM_RESTARTS).unsqueeze(1) # to match the dimension n * 1 * m
        # print("sampled_initial_conditions: ", initial_cond)
        candidates, _ = optimize_acqf(
            acq_function=acq_func,
            bounds=self.input_info.constraints.constraint_bound,
            q=self.BATCH_SIZE,
            num_restarts=self.NUM_RESTARTS,
            options={"batch_limit": 1, "maxiter": 200},
            # nonlinear_inequality_constraints = [constraint_set.get_nonlinear_inequality_constraints],
            # batch_initial_conditions = initial_cond,
            raw_samples=self.RAW_SAMPLES,
            sequential=True
        )
        # observe new values
        new_x = candidates.detach()
        print("new_x: ", new_x)
        valid_generated_sample, new_exact_obj = data_set.find_ppa_result(new_x)
        new_normalised_obj = data_set.normalise_output_data_tensor(new_exact_obj)
        new_con_obj = data_set.check_qNEHVI_constraints(new_normalised_obj)
        if new_con_obj.item() <= 0.0:
            hyper_vol = calculate_hypervolume(self.ref_points, new_normalised_obj, self.OBJECTIVES_TO_OPTIMISE_DIM)
        else:
            hyper_vol = 0.0
        new_train_obj = torch.cat([new_normalised_obj[..., : self.OBJECTIVES_TO_OPTIMISE_DIM], new_con_obj], dim=-1)
        return valid_generated_sample, new_x, new_exact_obj, new_train_obj, hyper_vol


### <----------------- Other Models ----------------->
def brute_force(output_info, ref_points, data_set, record, results_record):
    # Global Best Values
    best_volume = 0
    best_sample = None  
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
    sample_inputs = data_set.find_all_possible_designs()
    shuffled_tensor = sample_inputs[torch.randperm(sample_inputs.size(0))]
    overall_iteration_required = shuffled_tensor.shape[0]
    print("overall_iteration_required: ", overall_iteration_required)
    #Optimisation Loop
    for iteration in range(overall_iteration_required):
        t0 = time.monotonic()
        sample_input = sample_inputs[iteration].unsqueeze(0)
        valid_sample, possible_obj = data_set.find_ppa_result(sample_input)
        if valid_sample == False:
            continue
        normalised_obj = data_set.normalise_output_data_tensor(possible_obj)
        con_obj = data_set.check_qNEHVI_constraints(normalised_obj)
        if con_obj.item() <= 0.0:
            volume = calculate_hypervolume(ref_points, normalised_obj, output_info.obj_to_optimise_dim)
            if  best_volume < volume:
                best_volume = volume
                best_sample = sample_input
                best_results = possible_obj
        else:
            continue
        t1 = time.monotonic()
        best_objs = encapsulate_obj_tensor_into_dict(output_info.obj_to_optimise, best_results)
        if record:
            results_record.record(iteration, sample_input.squeeze(0), volume, best_objs, t1-t0)
    print(f"{Fore.GREEN}best_volume: {best_volume}, best_sample: {best_sample}, best_results: {best_results}{Style.RESET_ALL}")
    if record:
        results_record.store()


def hill_climbing(input_info, output_info, ref_points, data_set, record, results_record, max_iterations=30, step_size=0.01):
    # Generate initial solution
    best_volume = 100
    best_sample = None  
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
    current_solution = torch.rand((1, len(input_info.input_names)), device=data_set.tensor_device, dtype=data_set.tensor_type)
    for iteration in range(max_iterations):
        t0 = time.monotonic()
        # Generate a neighbor solution by adding a small step in a random direction
        step_directions = torch.randint(low=0, high=2, size=current_solution.size(), device=data_set.tensor_device, dtype=data_set.tensor_type) * 2 - 1  # Randomly choose -1 or 1 for each element
        step = step_directions * step_size
        neighbor_solution = torch.clamp(current_solution + step, min=0, max=1)
        # Evaluate the neighbor solution
        valid_sample, possible_obj = data_set.find_ppa_result(neighbor_solution)
        if valid_sample == False:
            continue
        normalised_obj = data_set.normalise_output_data_tensor(possible_obj)
        con_obj = data_set.check_qNEHVI_constraints(normalised_obj)
        if con_obj.item() <= 0.0:
            volume = calculate_hypervolume(ref_points, normalised_obj, output_info.obj_to_optimise_dim)
            if volume < best_volume:
                best_volume = volume
                best_sample = neighbor_solution
                best_results = possible_obj
                current_solution = neighbor_solution
            elif volume == 0:
                break
        else:
            continue
        t1 = time.monotonic()
        best_objs = encapsulate_obj_tensor_into_dict(output_info.obj_to_optimise, best_results)
        if record:
            results_record.record(iteration, current_solution.squeeze(0), volume, best_objs, t1-t0)
    print(f"{Fore.GREEN}best_volume: {best_volume}, best_sample: {best_sample}, best_results: {best_results}{Style.RESET_ALL}")
    if record:
        results_record.store()