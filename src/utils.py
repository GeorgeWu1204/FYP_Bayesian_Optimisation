import torch
import itertools
import numpy as np
import matplotlib.pyplot as plt
import re

def calculate_condition(x, condition):
    """This function is used to calculate the input constraints"""
    return (x - condition[0]) * (condition[1] - x)

def calculate_smooth_condition(x, condition):
    """Smooth, differentiable step function. Used for calculating the output constraints"""
    return (1 / (1 + torch.exp(-10 * (x - condition[1]))) - 1 / (1 + torch.exp(-10 * (x - condition[0]))) + 0.5) * 1e-1

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

def recover_single_input_data(input_tensor, normalised_factor, scales, offsets, exps = None):
    """This function is to find the real input from the x tensor in optimisation process"""
    #assuming the input_tensor is in the shape of num_restarts x d_dim
    if exps is not None:
        input_var = exps ** (torch.round(input_tensor * normalised_factor) * scales + offsets)  
    else:
        input_var = torch.round(input_tensor * normalised_factor) * scales + offsets
    results = input_var.tolist()
    return results

def recover_all_input_data(input_tensor, normalised_factor, scales, offsets, type, device, exps = None):
    """This function is to find the real input from the x tensor in recording process"""
    if exps is not None:
        results = torch.tensor(exps, dtype=type, device=device) ** (torch.round(input_tensor * torch.tensor(normalised_factor, dtype=type, device=device)) * torch.tensor(scales, dtype=type, device=device) + torch.tensor(offsets, dtype=type, device=device))
    else:
        results = torch.round(input_tensor * torch.tensor(normalised_factor, dtype=type, device=device)) * torch.tensor(scales, dtype=type, device=device)
    return results

def recover_unrounded_input_data(input_tensor, normalised_factor, scales, offsets, type, device, exps = None):
    """This function is to find the unrounded version of the real input from the x tensor in recording process"""
    if exps is not None:
        results = torch.tensor(exps, dtype=type, device=device) ** (torch.round(input_tensor * torch.tensor(normalised_factor, dtype=type, device=device)) * torch.tensor(scales, dtype=type, device=device) + torch.tensor(offsets, dtype=type, device=device))
    else:
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

def find_ref_points(OBJECTIVES_DIM, OBJECTIVES, t_type, device):
    """This function is used to find the reference points for qNEHVI optimisation"""
    ref_points = torch.empty((OBJECTIVES_DIM), device=device, dtype=t_type)
    ref_point_index = 0
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            ref_points[ref_point_index] = -1
        else:
            ref_points[ref_point_index] = 1
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



def read_utilization(rpt_file_path, variable_names):
    """This function is used to read the utilization from the Vivado report file"""
    in_section = False
    # Define a pattern to match the rows in the utilization table
    row_pattern = re.compile(r'\|\s*(.*?)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+\.\d+|\d+)\s*\|')

    # Initialize a list to hold multiple matches, if any
    results = []

    try:
        with open(rpt_file_path, 'r') as file:
            table_margin_count = 0
            for line in file:
                # Check if we've reached the CLB Logic section, only focus on this section first.
                if 'CLB Logic' in line:
                    in_section = True
                # Check if we've passed the section of interest
                elif in_section and '+----------------------------+' in line:
                    table_margin_count += 1  # Exit the loop if we're past the relevant section
                elif in_section:
                    # Match the row pattern within the section
                    match = row_pattern.match(line)
                    for variable_name in variable_names:
                        if match and variable_name in match.group(1):
                            # Append the variable name and its Util% to the results list
                            results.append(float(match.group(2)))
                if table_margin_count == 3:
                    break
            return results
    except FileNotFoundError:
        print(f"File not found: {rpt_file_path}")
        return





#<--------------------------------- Classes for recording the results --------------------------------->

class recorded_training_result:
    """This class is used to record the results of optimisation."""
    def __init__(self, input_names, objectives, best_values, record_file_name, num_trials, num_iterations):
        self.objs  = objectives
        self.best_vals  = best_values
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
    def __init__(self, input_vars, objectives, overall_iteration_size, record_file_name):
        self.history = {}
        self.input_vars = input_vars
        self.objs  = objectives
        self.record_file_name = record_file_name
        for i in range(overall_iteration_size):
            self.history[i] = {}
    def record(self, iteration, sample_input, sample_result, best_objs, time):
        self.history[iteration] = [sample_input, sample_result, best_objs, time]
    
    def store(self):
        total_time = 0
        with open(self.record_file_name, 'w') as f:
            f.write("iteration, time")
            for input in self.input_vars:
                f.write(f", {input}")
            f.write(", current_hyper_vol")
            for obj in self.objs:
                f.write(f", {obj}")
            f.write("\n")
            for i in range(len(self.history)):
                valid_history = self.history.get(i, None)
                if(valid_history != {}):
                    total_time += valid_history[3]
                    f.write(f"{i}, {total_time:>4.2f}")
                    for input in valid_history[0]:
                        f.write(f", {input}")
                    f.write(f", {valid_history[1]}")
                    for obj in range(len(self.objs)):
                        result = valid_history[2][obj]
                        f.write(f", {result}")
                    f.write("\n")


class test_posterior_result:
    """This class is used to visualise the posterior funcitons"""
    def __init__(self, input_names, dtype, device, num_samples = 100):
        self.dim = len(input_names)
        self.input_names = input_names
        self.X = np.linspace(0, 1, num_samples) 
        self.num_samples = num_samples
        # Create multi-dimensional grids
        basis_grid = np.meshgrid(*[self.X for _ in range(self.dim)])
        # Flatten and combine all grids to form the combination array
        # Each row in the combination array represents a point in the multi-dimensional space
        combination_array = np.vstack([grid.ravel() for grid in basis_grid]).T
        # Convert the combination array to a PyTorch tensor
        self.testcase = torch.from_numpy(combination_array).to(dtype=dtype, device=device)

    def examine_posterior(self, model, iteration):
        """This function is used to examine the function"""
        # self.mean_prediction, self.std_deviation = model.forward(self.testcase)
        posterior = model.posterior(self.testcase)
        mean_prediction = posterior.mean.cpu().detach().numpy()  # Mean of the predictive distribution
        std_deviation = posterior.variance.cpu().detach().numpy() 

        Z_mean = mean_prediction.reshape([self.num_samples for _ in range(self.dim)])
        Z_uncertainty = std_deviation.reshape([self.num_samples for _ in range(self.dim)])

        X = self.testcase[:,0].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        Y = self.testcase[:,1].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z_mean, cmap='viridis', edgecolor='none', alpha=0.7)
        # Plot Uncertainty using Contourf  at the base
        min_uncertainty, max_uncertainty = np.min(Z_uncertainty), np.max(Z_uncertainty)
        levels  = np.linspace(min_uncertainty, max_uncertainty, num=10)
        levels  = np.unique(levels)  # Ensure levels are unique
        epsilon = np.diff(levels).min() * 0.1  # Small increment
        levels[1:] += epsilon  # Avoid incrementing the first level to keep the minimum

        contour = ax.contourf(X, Y, Z_uncertainty, zdir='z', offset=Z_mean.min()-0.25, levels=levels, cmap='inferno', alpha=0.5)

        ax.set_xlabel(self.input_names[0])
        ax.set_ylabel(self.input_names[1])
        ax.set_zlabel('Mean Prediction')
        ax.set_title('Posterior Mean and Uncertainty at Iteration ' + str(iteration))

        # Add a color bar for the contour plot
        fig.colorbar(contour, shrink=0.5, aspect=5, label='Uncertainty (Std Dev)')
        plt.show()

    def examine_acq_function(self, acq_function, iteration):
        """This function is used to examine the acquisition function"""
        acq_values = acq_function(self.testcase.unsqueeze(-2)).cpu().detach().numpy()
        Z = acq_values.reshape([self.num_samples for _ in range(self.dim)])
        X = self.testcase[:,0].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        Y = self.testcase[:,1].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.7)
        ax.set_xlabel(self.input_names[0])
        ax.set_ylabel(self.input_names[1])
        ax.set_zlabel('Acquisition Function Value')
        ax.set_title('Acquisition Function Examination at Iteration ' + str(iteration))
        plt.show()
        



if __name__ == '__main__':
    # print("test")
    # result = read_utilization('D:\\Imperial\\Year4\\MasterThesis\\FYP_Bayesian_Optimisation\\object_functions\\Syn_Report\\NutShell_utilization_synth.rpt', ['LUT as Logic', 'CLB Registers'] )
    # print(result)
    # x_values = torch.linspace(-0, 0.5, 1000)
    # # Define the condition (start and end points of the step)
    # condition = [0, 0.03]  # Example condition
    # # Calculate y values using the smooth condition function
    # y_values = calculate_smooth_condition(x_values, condition)
    # print(y_values)
    test = read_utilization('../object_functions/Syn_Report/EL2_utilization_synth.rpt', ['LUT as Logic', 'CLB Registers'])
    print(test)


    
