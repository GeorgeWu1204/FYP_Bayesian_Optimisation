import torch
import itertools


def calculate_condition(x, condition):
    """This function is used to calculate the input constraints"""
    return (x - condition[0]) * (condition[1] - x)

def calculate_smooth_condition(x, condition):
    """Smooth, differentiable step function. Used for calculating the output constraints"""
    return (1 / (1 + torch.exp(-10 * (x - condition[1]))) - 1 / (1 + torch.exp(-10 * (x - condition[0]))) + 0.5) * 1e-2


def build_matrix(data, constraints, num_restarts, q_dim, d_dim):
    """Build a matrix to store all the results of whether the input data meet the constraints."""
    # formatted_correlated_constraints = {d_dim : [condition_size, num_restarts * q_dim]}
    formatted_correlated_constraints = {}
    individual_constraint = torch.empty((d_dim, num_restarts * q_dim))
    
    flat_data = data.flatten()

    for i in range(d_dim):
        indices = torch.arange(start = i, end = len(flat_data), step = d_dim)
        selected_data = flat_data[indices]
        # individual constraint
        individual_constraint[i] = calculate_condition(selected_data, constraints.Node[i].individual_constraints)
        if(constraints.Node[i].have_constraints()):
            condition_size = constraints.Node[i].condition_size()
            cal_condition = torch.empty((condition_size, num_restarts * q_dim))
            for j in range(0, constraints.Node[i].condition_size()):
                cal_condition[j] = calculate_condition(selected_data, constraints.Node[i].conditions[j])
            formatted_correlated_constraints[i] = cal_condition
    return individual_constraint, formatted_correlated_constraints

def normalise_input_data(input_tensor, normalized_factors):
    """This function is used to normalise the input data, it is not used currently"""
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = input_tensor[i][j] / normalized_factors[j]
    return output_tensor

def normalise_output_data(input_tensor, normalized_factors, device):
    num_restarts, obj_m = input_tensor.shape
    output_tensor = torch.empty((num_restarts, obj_m), device=device,dtype=input_tensor.dtype)
    for i in range(obj_m):
        for j in range(num_restarts):
            output_tensor[j][i] = input_tensor[j][i] / normalized_factors[i]
    return output_tensor

def recover_single_input_data(input_tensor, normalised_factor, scales, offsets):
    """This function is to find the real input from the x tensor in optimisation process"""
    #assuming the input_tensor is in the shape of num_restarts x d_dim
    input_var = torch.round(input_tensor * normalised_factor) * scales + offsets
    results = input_var.tolist()
    return results

def recover_all_input_data(input_tensor, normalised_factor, scales, offsets, type, device):
    """This function is to find the real input from the x tensor in recording process"""
    results = torch.round(input_tensor * torch.tensor(normalised_factor, dtype=type, device=device)) * torch.tensor(scales, dtype=type, device=device) + torch.tensor(offsets, dtype=type, device=device)
    return results

def recover_unrounded_input_data(input_tensor, normalised_factor, scales, offsets, type, device):
    """This function is to find the unrounded version of the real input from the x tensor in recording process"""
    results = input_tensor * torch.tensor(normalised_factor, dtype=type, device=device) * torch.tensor(scales, dtype=type, device=device) + torch.tensor(offsets, dtype=type, device=device)
    return results


def recover_output_data(input_tensor, normalized_factors):
    """This function is used to recover the output data"""
    obj_m, num_restarts = input_tensor.shape
    output_tensor = torch.empty((obj_m, num_restarts), dtype=input_tensor.dtype)
    for i in range(obj_m):
        for j in range(num_restarts):
            output_tensor[i][j] = input_tensor[i][j] * normalized_factors[i]
    return output_tensor

def encapsulate_obj_tensor_into_dict(objs, obj_tensor):
    """This function is used to facilitate the recording of the output results"""
    obj_dict = {}
    obj_index = 0
    for obj in objs.keys():
        obj_dict[obj] = obj_tensor[... , obj_index].item()
        obj_index += 1
    return obj_dict 

def encapsulate_input_tensor_into_dict(input_tensor, input_var_names):
    """This function is used to facilitate the recording of the input results"""
    input_dict = {}
    input_index = 0
    for var in input_var_names:
        input_dict[var] = input_tensor[... , input_index].item()
        input_index += 1
    return input_dict

def find_ref_points(OBJECTIVES_DIM, OBJECTIVES, worst_value, output_normalised_factors, t_type, device):
    """This function is used to find the reference points for qNEHVI optimisation"""
    ref_points = torch.empty((OBJECTIVES_DIM), device=device, dtype=t_type)
    ref_point_index = 0
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            ref_points[ref_point_index] = -1 * (worst_value[obj] / output_normalised_factors[obj])
        else:
            ref_points[ref_point_index] = (worst_value[obj] / output_normalised_factors[obj])
        ref_point_index += 1
    return ref_points

def find_samples_brute_force(ranges):
    """This function is used for brute force optimisation to prepare all the samples"""
    for i in range(len(ranges)):
        ranges[i] = list(range(ranges[i][0], ranges[i][1] + 1))
    combinations = list(itertools.product(*ranges))
    vectors = [list(combination) for combination in combinations]
    return vectors

def calculate_volumes_for_brute_force(objs, normalised_factors, objs_to_optimise_dim):
    """This function is used for brute force optimisation to calculate the volume of the design space"""
    volumes = 1
    for obj_index in range(objs_to_optimise_dim):
        volumes *= objs[obj_index]/ normalised_factors[obj_index]
    return volumes


def find_max_index_in_list(list):
    max_index = 0
    for i in range(len(list)):
        if(list[i] > list[max_index]):
            max_index = i
    return max_index




class recorded_training_result:
    """This class is used to record the results of optimisation."""
    def __init__(self, input_names, objectives, best_values, best_pairs, record_file_name, num_trials, num_iterations):
        self.objs  = objectives
        self.best_vals  = best_values
        self.best_pairs = best_pairs
        self.history = {}
        self.iterations = num_iterations
        self.trials = num_trials
        self.record_file_name = record_file_name
        for i in range(num_trials * num_iterations):
            self.history[i] = {}
        self.input_history = {}
        self.input_names = input_names

    def record(self, iteration, trial, best_objs, time):
        self.history[(trial -1) * self.iterations + (iteration-1)] = [best_objs, time]
    
    def record_input(self, trial, train_x, hyper_vols):
        self.input_history[trial] = [trial, train_x, hyper_vols]
    
    def store(self):
        total_time = 0
        with open(self.record_file_name + 'record_result.txt', 'w') as f:
            f.write("iteration, time")
            for obj in self.objs:
                f.write(f", {obj}")
            f.write("\n")
            for i in range(self.trials * self.iterations):
                total_time += self.history[i][1]
                f.write(f"{i}, {total_time:>4.2f}")
                for obj in self.objs:
                    result = self.history[i][0].get(obj, 0)
                    f.write(f", {result}")
                f.write("\n")
        
        with open(self.record_file_name + 'record_input.txt', 'w') as f:
            f.write("trial, hyper_vol")
            for name in self.input_names:
                f.write(f", {name}")
            f.write("\n")
            for trial in self.input_history.keys():
                for data_idx in range(len(self.input_history[trial][1])):
                    f.write(f"{trial}, {self.input_history[trial][2][data_idx]}")
                    for input_index in range(len(self.input_names)):
                       f.write(f", {self.input_history[trial][1][data_idx][input_index]}")
                    f.write("\n")
    

class brute_force_training_result:
    """This class is used to record the results of brute force optimisation."""
    def __init__(self, objectives, overall_iteration_size, record_file_name):
        self.history = {}
        self.objs  = objectives
        self.record_file_name = record_file_name
        for i in range(overall_iteration_size):
            self.history[i] = {}
    def record(self, iteration, best_objs, time):
        self.history[iteration] = [best_objs, time]
    
    def store(self):
        total_time = 0
        with open(self.record_file_name, 'w') as f:
            f.write("iteration, time")
            for obj in self.objs:
                f.write(f", {obj}")
            f.write("\n")
            for i in range(len(self.history)):
                total_time += self.history[i][1]
                f.write(f"{i}, {total_time:>4.2f}")
                for obj in range(len(self.objs)):
                    result = self.history[i][0][obj]
                    f.write(f", {result}")
                f.write("\n")
