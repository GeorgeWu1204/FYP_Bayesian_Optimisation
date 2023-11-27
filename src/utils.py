import torch

def calculate_condition(x, condition):
    return (x - condition[0]) * (condition[1] - x)

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

def normalise_generated_data(input_tensor, normalized_factors):
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = input_tensor[i][j] / normalized_factors[j]
    return output_tensor

def recover_generated_data(input_tensor, normalized_factors, scaled_factors):
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = torch.round(input_tensor[i][j] * normalized_factors[j]) * scaled_factors[j] 
    return output_tensor

class recorded_training_result:
    def __init__(self, objective, max_value, record_file_name):
        self.obj  = objective
        self.max  = max_value
        self.history = {}
        self.record_file_name = record_file_name
    def record(self, iteration, current_best_val, current_val, time):
        self.history[iteration] = [current_best_val, current_val, time]
    
    def store(self):
        total_time = 0
        with open(self.record_file_name, 'w') as f:
            f.write(f"obj: {self.obj}\n")
            f.write(f"max: {self.max}\n")
            f.write("iteration, current_best_val, current_val, time\n")
            for i in self.history:
                total_time += self.history[i][2]
                f.write(f"{i}, {self.history[i][0]:>2}, {self.history[i][1]}, {total_time:>4.2f}\n")