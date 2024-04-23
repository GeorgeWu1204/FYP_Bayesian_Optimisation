import random
import time
import torch
from utils import calculate_hypervolume, encapsulate_obj_tensor_into_dict, other_model_training_result
from colorama import Fore, Style
import numpy as np
from typing import Optional

from customised_model import SingleTaskGP_transformed
from botorch.models.transforms.outcome import Standardize
from botorch.models.model_list_gp_regression import ModelListGP
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.acquisition.multi_objective.monte_carlo import qNoisyExpectedHypervolumeImprovement
from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
from botorch.optim import optimize_acqf
from botorch.models import SingleTaskGP
from botorch.acquisition.objective import ConstrainedMCObjective
from botorch.acquisition.monte_carlo import qExpectedImprovement

### <----------------- Single Objective BO Model ----------------->
def obj_callable(Z: torch.Tensor, X: Optional[torch.Tensor] = None):
    return Z[..., 0]

def constraint_callable(Z):
    result = Z[..., 1]
    if Z.shape[-1] > 2:
        for i in range(2, Z.shape[-1]):
            result = result * (Z[..., i] <= 0)
    return result

def calculate_weighted_obj_score(normalised_obj, ref_points, objective_index):
    result = normalised_obj.clone() 
    result[...,0] = result[...,0] - ref_points[objective_index]
    for i in range (1, normalised_obj.shape[-1]):
        result[..., 0] = result[..., 0] * ( normalised_obj[..., i] <= 0)
    return result[..., 0]

### <----------------- Single Objective BO With Resource Limitation Consideration ----------------->

class single_objective_BO_model():
    """Single Objective Bayesian Optimisation Model"""
    def __init__(self, NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, input_info, output_info, ref_points, device, t_type, output_constraints_enable=True, categorical_handle_enable=True):
        self.NUM_RESTARTS = NUM_RESTARTS
        self.RAW_SAMPLES = RAW_SAMPLES
        self.BATCH_SIZE = BATCH_SIZE
        self.ref_points = ref_points
        self.input_info = input_info
        self.output_info = output_info  
        self.device = device
        self.t_type = t_type
        self.output_constraints_enable = output_constraints_enable
        self.categorical_handle_enable = categorical_handle_enable
        self.objective_index = output_info.obj_to_optimise_index
        self.constrained_obj = ConstrainedMCObjective(
                objective=obj_callable,
                constraints=[constraint_callable],
            )
    
    
    def initialize_model(self, train_x, train_obj):
        if self.categorical_handle_enable:
            return self.initialize_custom_model(train_x, train_obj)
        else:
            return self.initialize_default_model(train_x, train_obj)
    
    def calculate_max_obj(self, normalised_obj):
        result = normalised_obj.clone()
        for i in range (1, normalised_obj.shape[-1]):
            result[..., 0] = result[..., 0] * ( normalised_obj[..., i] <= 0)
        return result[..., 0].max()

    def initialize_custom_model(self, train_x, train_obj, state_dict=None):
        """define models that considers the categorical error for objective and constraint"""
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
        if state_dict is not None:
            model.load_state_dict(state_dict)
        return mll, model
    
    def initialize_default_model(self, train_x, train_obj, state_dict=None):
        """define models for objective and constraint"""
        ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
        models = []
        for obj_index in range(train_obj.shape[-1]): 
            train_y = train_obj[..., obj_index : obj_index + 1]
            models.append(SingleTaskGP(
                                        train_x, 
                                        train_y, 
                                        outcome_transform=Standardize(m=1)
                                    ))
        
        model = ModelListGP(*models)
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        if state_dict is not None:
            model.load_state_dict(state_dict)
        return mll, model

    def build_acqf(self, model, train_obj, sampler):
        """Build the qNEHVI acquisition function"""
        qEI = qExpectedImprovement(
            model=model,
            best_f=self.calculate_max_obj(train_obj),
            sampler=sampler,
            objective=self.constrained_obj,
        )
        return qEI
    
    def optimize_acqf_and_get_observation(self, acq_func, data_set):
        """Optimizes the acquisition function, and returns a new candidate and the corresponding observation."""
        # TODO: Noticed that if there is an input constraint, the points are selected from the generated condition.
        candidates, _ = optimize_acqf(
            acq_function=acq_func,
            bounds=self.input_info.constraints.constraint_bound,
            q=self.BATCH_SIZE,
            num_restarts=self.NUM_RESTARTS,
            options={"batch_limit": 1, "maxiter": 200},
            raw_samples=self.RAW_SAMPLES,
            sequential=True
        )
        # observe new values
        new_x = candidates.detach()
        valid_generated_sample, new_exact_obj = data_set.find_ppa_result(new_x)
        new_normalised_obj = data_set.normalise_output_data_tensor(new_exact_obj)
        new_con_obj = data_set.check_obj_constraints(new_normalised_obj)
        new_train_obj = torch.cat([new_normalised_obj[...,self.objective_index:self.objective_index + 1], new_con_obj], dim=-1)
        new_exact_obj = torch.cat([new_exact_obj[...,self.objective_index:self.objective_index + 1], new_con_obj], dim=-1)
        new_obj_score = calculate_weighted_obj_score(new_train_obj, self.ref_points, self.objective_index)
        return valid_generated_sample, new_x, new_exact_obj, new_train_obj, new_obj_score
    
    def generate_initial_data(self, sampler_generator, NUM_OF_INITIAL_POINT, data_set):
        """generate training data"""
        unnormalised_train_x, exact_objs, con_objs, normalised_objs = sampler_generator.generate_valid_initial_data(NUM_OF_INITIAL_POINT, data_set)
        train_obj = torch.cat([normalised_objs[...,self.objective_index:self.objective_index + 1], con_objs], dim=-1)
        # with_noise_train_obj = train_obj + torch.randn_like(train_obj) * NOISE_SE
        obj_scores = calculate_weighted_obj_score(train_obj, self.ref_points, self.objective_index)
        new_exact_obj = torch.cat([exact_objs[...,self.objective_index:self.objective_index + 1], con_objs], dim=-1)
        print("train_obj: ", train_obj.shape)
        return unnormalised_train_x, new_exact_obj, train_obj, obj_scores



### <----------------- Single Objective BO Designed for Simple Handling of Resource Constraint ----------------->

class single_objective_BO_model_with_resource_constraint(single_objective_BO_model):

    def __init__(self, NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, input_info, output_info, ref_points, device, t_type, output_constraints_enable=True, categorical_handle_enable=True):
        super().__init__(NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, input_info, output_info, ref_points, device, t_type, output_constraints_enable, categorical_handle_enable)

    def initialize_model(self, train_x, train_obj):    
        return self.initialize_default_model(train_x, train_obj)
    
    def calculate_max_obj(self, normalised_obj):
        result = normalised_obj.clone()
        for i in range (1, normalised_obj.shape[-1]):
            result[..., 0] = result[..., 0] * ( normalised_obj[..., i] <= 0)
        return result[..., 0].max()

    
    def initialize_default_model(self, train_x, train_obj, state_dict=None):
        """define models for objective and constraint"""
        ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
        models = []
        for obj_index in range(train_obj.shape[-1]): 
            train_y = train_obj[..., obj_index : obj_index + 1]
            models.append(SingleTaskGP(
                                        train_x, 
                                        train_y, 
                                        outcome_transform=Standardize(m=1)
                                    ))
        
        model = ModelListGP(*models)
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        if state_dict is not None:
            model.load_state_dict(state_dict)
        return mll, model

    def build_acqf(self, model, train_obj, sampler):
        """Build the qNEHVI acquisition function"""
        qEI = qExpectedImprovement(
            model=model,
            best_f=self.calculate_max_obj(train_obj),
            sampler=sampler,
            objective=self.constrained_obj,
        )
        return qEI
    
    def optimize_acqf_and_get_observation(self, acq_func, data_set):
        """Optimizes the acquisition function, and returns a new candidate and the corresponding observation."""
        # TODO: Noticed that if there is an input constraint, the points are selected from the generated condition.
        candidates, _ = optimize_acqf(
            acq_function=acq_func,
            bounds=self.input_info.constraints.constraint_bound,
            q=self.BATCH_SIZE,
            num_restarts=self.NUM_RESTARTS,
            options={"batch_limit": 1, "maxiter": 200},
            raw_samples=self.RAW_SAMPLES,
            sequential=True
        )
        # observe new values
        new_x = candidates.detach()
        valid_generated_sample, new_exact_obj = data_set.find_ppa_result(new_x)
        new_normalised_obj = data_set.normalise_output_data_tensor(new_exact_obj)
        new_con_obj = data_set.check_obj_constraints(new_normalised_obj)
        new_train_obj = torch.cat([new_normalised_obj[...,self.objective_index:self.objective_index + 1], new_con_obj], dim=-1)
        new_exact_obj = torch.cat([new_exact_obj[...,self.objective_index:self.objective_index + 1], new_con_obj], dim=-1)
        new_obj_score = calculate_weighted_obj_score(new_train_obj, self.ref_points, self.objective_index)
        return valid_generated_sample, new_x, new_exact_obj, new_train_obj, new_obj_score
    
    def generate_initial_data(self, sampler_generator, NUM_OF_INITIAL_POINT, data_set):
        """generate training data"""
        unnormalised_train_x, exact_objs, con_objs, normalised_objs = sampler_generator.generate_valid_initial_data(NUM_OF_INITIAL_POINT, data_set)
        train_obj = torch.cat([normalised_objs[...,self.objective_index:self.objective_index + 1], con_objs], dim=-1)
        # with_noise_train_obj = train_obj + torch.randn_like(train_obj) * NOISE_SE
        obj_scores = calculate_weighted_obj_score(train_obj, self.ref_points, self.objective_index)
        new_exact_obj = torch.cat([exact_objs[...,self.objective_index:self.objective_index + 1], con_objs], dim=-1)
        print("train_obj: ", train_obj.shape)
        return unnormalised_train_x, new_exact_obj, train_obj, obj_scores



### <----------------- Multi-objective Model ----------------->

class multi_objective_BO_model():
    def __init__(self, NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, input_info, output_info, ref_points, device, t_type, output_constraints_enable=True, categorical_handle_enable=True):
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
        self.output_constraints_enable = output_constraints_enable
        self.categorical_handle_enable = categorical_handle_enable
    
    def initialize_model(self, train_x, train_obj):
        if self.categorical_handle_enable:
            return self.initialize_custom_model(train_x, train_obj)
        else:
            return self.initialize_default_model(train_x, train_obj)


    def initialize_custom_model(self, train_x, train_obj):
        """define models that considers the categorical error for objective and constraint"""
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
    
    def initialize_default_model(self, train_x, train_obj):
        """define models for objective and constraint"""
        ### Model selection: Assume multiple independent output training on the same data in this case, otherwise MultiTaskGP ###
        models = []
        for obj_index in range(train_obj.shape[-1]): 
            train_y = train_obj[..., obj_index : obj_index + 1]
            models.append(SingleTaskGP(
                                        train_x, 
                                        train_y, 
                                        outcome_transform=Standardize(m=1)
                                    ))
        
        model = ModelListGP(*models)
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        return mll, model


    def build_acqf(self, model, train_x, sampler):
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
        new_con_obj = data_set.check_obj_constraints(new_normalised_obj)
        if new_con_obj.item() <= 0.0:
            hyper_vol = calculate_hypervolume(self.ref_points, new_normalised_obj, self.OBJECTIVES_TO_OPTIMISE_DIM)
        else:
            hyper_vol = 0.0
        new_train_obj = torch.cat([new_normalised_obj[..., : self.OBJECTIVES_TO_OPTIMISE_DIM], new_con_obj], dim=-1)
        return valid_generated_sample, new_x, new_exact_obj, new_train_obj, hyper_vol
    
    def generate_initial_data(self, sampler_generator, NUM_OF_INITIAL_POINT, data_set):
        """generate training data"""
        unnormalised_train_x, exact_objs, con_objs, normalised_objs = sampler_generator.generate_valid_initial_data(NUM_OF_INITIAL_POINT, data_set)
        train_obj = torch.cat([normalised_objs[...,:self.OBJECTIVES_TO_OPTIMISE_DIM], con_objs], dim=-1)
        # with_noise_train_obj = train_obj + torch.randn_like(train_obj) * NOISE_SE
        generate_size = train_obj.shape[0]
        hypervolumes = torch.zeros(generate_size, device=self.device)
        print("ref_points: ", self.ref_points)
        print("train_obj: ", train_obj.shape)
        for i in range(generate_size):
            hypervolumes[i] = calculate_hypervolume(self.ref_points, train_obj[i].unsqueeze(0), self.OBJECTIVES_TO_OPTIMISE_DIM)
        return unnormalised_train_x, exact_objs, train_obj, hypervolumes

### <----------------- Other Models ----------------->
def brute_force(input_info, output_info, ref_points, data_set, record, record_file_name):
    # Global Best Values
    best_volume = 0
    best_sample = None  
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
    sample_inputs = data_set.find_all_possible_designs()
    shuffled_tensor = sample_inputs[torch.randperm(sample_inputs.size(0))]
    overall_iteration_required = shuffled_tensor.shape[0]
    #Optimisation Loop
    if record:
        for obj_name in output_info.obj_to_optimise.keys():
            record_file_name = record_file_name + obj_name + '_'
        record_file_name = record_file_name + 'brute_force_record_result.txt'
        results_record = other_model_training_result(input_info.input_names, output_info.obj_to_optimise, overall_iteration_required, record_file_name)
    for iteration in range(overall_iteration_required):
        t0 = time.monotonic()
        sample_input = sample_inputs[iteration].unsqueeze(0)
        valid_sample, possible_obj = data_set.find_ppa_result(sample_input)
        if valid_sample == False:
            continue
        normalised_obj = data_set.normalise_output_data_tensor(possible_obj)
        con_obj = data_set.check_obj_constraints(normalised_obj)
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


def hill_climbing(input_info, output_info, ref_points, data_set, record, record_file_name, obj_index = None, max_iterations=30, step_size=0.05):
    # Generate initial solution
    if record:
        for obj_name in output_info.obj_to_optimise.keys():
            record_file_name = record_file_name + obj_name + '_'
        record_file_name = record_file_name + 'hill_climbing_record_result.txt'
        results_record = other_model_training_result(input_info.input_names, output_info.obj_to_optimise, max_iterations, record_file_name)
    best_score = 0
    best_sample = None  
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
    current_solution = torch.rand((1, len(input_info.input_names)), device=data_set.tensor_device, dtype=data_set.tensor_type)
    for iteration in range(max_iterations):
        t0 = time.monotonic()
        # Generate a neighbor solution by adding a small step in a random direction
        step_directions = torch.randint(low=0, high=2, size=current_solution.size(), device=data_set.tensor_device, dtype=data_set.tensor_type) * 2 - 1  # Randomly choose -1 or 1 for each element
        step = step_directions * step_size
        neighbor_solution = torch.clamp(current_solution + step, min=0, max=1)
        print("neighbor_solution: ", neighbor_solution)
        # Evaluate the neighbor solution
        valid_sample, possible_obj = data_set.find_ppa_result(neighbor_solution)
        if valid_sample == False:
            continue
        normalised_obj = data_set.normalise_output_data_tensor(possible_obj)
        print("normalised_obj: ", normalised_obj)
        con_obj = data_set.check_obj_constraints(normalised_obj)
        print("con_obj: ", con_obj)
        train_obj = torch.cat([normalised_obj[...,0:1], con_obj], dim=-1)
        if obj_index is not None:
            obj_scores = calculate_weighted_obj_score(train_obj, ref_points, obj_index)
        if con_obj.item() <= 0.0:
            if best_score < obj_scores:
                best_score = obj_scores
                best_sample = neighbor_solution
                best_results = possible_obj
                current_solution = neighbor_solution
        else:
            continue
        t1 = time.monotonic()
        best_objs = encapsulate_obj_tensor_into_dict(output_info.obj_to_optimise, best_results)
        if record:
            results_record.record(iteration, current_solution.squeeze(0), obj_scores.item(), best_objs, t1-t0)
    print(f"{Fore.GREEN}best_score: {obj_scores}, best_sample: {best_sample}, best_results: {best_results}{Style.RESET_ALL}")
    if record:
        results_record.store()


def genetic_algorithm(input_info, output_info, ref_points, data_set, record, record_file_name, max_generations=30, population_size=10, crossover_rate=0.7, mutation_rate=0.01):
    if record:
        for obj_name in output_info.obj_to_optimise.keys():
            record_file_name = record_file_name + obj_name + '_'
        record_file_name = record_file_name + 'genetic_algorithm_record_result.txt'
        results_record = other_model_training_result(input_info.input_names, output_info.obj_to_optimise, max_generations * population_size, record_file_name)
    # Initialize population
    population = torch.rand((population_size, len(input_info.input_names)), device=data_set.tensor_device, dtype=data_set.tensor_type)

    best_volume = 0
    best_sample = None
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]

    for generation in range(max_generations):
        t0 = time.monotonic()
        # Evaluate fitness of each solution
        fitness = []
        current_iteration = generation * population_size
        for i in range(population_size):
            print(f"population[{i}]: ", population[i])
            valid_sample, possible_obj = data_set.find_ppa_result(population[i].unsqueeze(0))
            if not valid_sample:
                fitness.append(float('inf'))  # Assign a large value for invalid samples
                continue
            normalised_obj = data_set.normalise_output_data_tensor(possible_obj)
            con_obj = data_set.check_obj_constraints(normalised_obj)
            if con_obj.item() <= 0.0:
                volume = calculate_hypervolume(ref_points, normalised_obj, output_info.obj_to_optimise_dim)
                fitness.append(volume)
                if best_volume < volume:
                    best_volume = volume
                    best_sample = population[i]
                    best_results = possible_obj
            else:
                fitness.append(float('inf'))  # Assign a large value for constrained samples
            t1 = time.monotonic()
            if record:
                possible_objs = encapsulate_obj_tensor_into_dict(output_info.obj_to_optimise, possible_obj)
                results_record.record(current_iteration + i, population[i], best_volume, possible_objs, t1-t0)

        # Selection
        selected_indices = np.random.choice(population_size, size=population_size, replace=True, p=np.reciprocal(fitness)/np.sum(np.reciprocal(fitness)))
        selected_population = population[selected_indices]

        # Crossover
        children = []
        for i in range(0, population_size, 2):
            if np.random.rand() < crossover_rate:
                crossover_point = np.random.randint(1, len(input_info.input_names))
                child1 = torch.cat((selected_population[i][:crossover_point], selected_population[i+1][crossover_point:]))
                child2 = torch.cat((selected_population[i+1][:crossover_point], selected_population[i][crossover_point:]))
                children.append(child1)
                children.append(child2)
            else:
                children.append(selected_population[i])
                children.append(selected_population[i+1])
        children = torch.stack(children)

        # Mutation
        mutation_matrix = (torch.rand(children.size(), device=data_set.tensor_device, dtype=data_set.tensor_type) < mutation_rate).float()
        mutation_steps = torch.randint(low=0, high=2, size=children.size(), device=data_set.tensor_device, dtype=data_set.tensor_type) * 2 - 1  # -1 or 1
        mutation = mutation_matrix * mutation_steps * mutation_rate
        population = torch.clamp(children + mutation, min=0, max=1)

        
    print(f"{Fore.GREEN}Best volume: {best_volume}, Best sample: {best_sample}, Best results: {best_results}{Style.RESET_ALL}")
    if record:
        results_record.store()