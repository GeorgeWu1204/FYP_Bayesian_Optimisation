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

def normalise_input_data(input_tensor, normalized_factors):
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = input_tensor[i][j] / normalized_factors[j]
    return output_tensor

def recover_input_data(input_tensor, normalized_factors, scaled_factors):
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = torch.round(input_tensor[i][j] * normalized_factors[j]) * scaled_factors[j] 
    return output_tensor

def normalise_output_data(input_tensor, normalized_factors):
    batch_dim, num_restarts, obj_m = input_tensor.shape
    output_tensor = torch.empty((batch_dim, num_restarts, obj_m), dtype=input_tensor.dtype)
    for b in range(batch_dim):
        for i in range(obj_m):
            for j in range(num_restarts):
                output_tensor[b][j][i] = input_tensor[b][j][i] / normalized_factors[i]
    return output_tensor

def recover_output_data(input_tensor, normalized_factors):
    # Note: not sure if this is correct, as there might be a rounding problem
    obj_m, num_restarts = input_tensor.shape
    output_tensor = torch.empty((obj_m, num_restarts), dtype=input_tensor.dtype)
    for i in range(obj_m):
        for j in range(num_restarts):
            output_tensor[i][j] = input_tensor[i][j] * normalized_factors[i]
    return output_tensor

def encapsulate_obj_tensor_into_dict(objs, obj_tensor):
    obj_dict = {}
    obj_index = 0
    for obj in objs.keys():
        obj_dict[obj] = obj_tensor[... , obj_index].item()
        obj_index += 1
    return obj_dict 

def find_ref_points(OBJECTIVES_DIM, OBJECTIVES, worst_value, output_normalised_factors, t_type):
    ref_points = torch.empty((OBJECTIVES_DIM), dtype=t_type)
    ref_point_index = 0
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            ref_points[ref_point_index] = -1 * (worst_value[obj] / output_normalised_factors[obj])
        else:
            ref_points[ref_point_index] = (worst_value[obj] / output_normalised_factors[obj])
        ref_point_index += 1
    normalized_factors = list(output_normalised_factors.values())
    print("ref_point: ", ref_points)
    return ref_points, normalized_factors



class recorded_training_result:
    def __init__(self, objectives, best_values, best_pairs, record_file_name):
        self.objs  = objectives
        self.best_vals  = best_values
        self.best_pairs = best_pairs
        self.history = {}
        self.iterations = 0
        self.record_file_name = record_file_name
        for i in objectives.keys():
            self.history[i] = {}
    def record(self, iteration, current_best_vals, current_vals, time):
        #Note prepare for multi objectives
        self.iterations = iteration
        for obj in self.objs:
            self.history[obj][iteration] = [current_best_vals[obj], current_vals[obj], time]
    
    def store(self):
        total_time = 0
        with open(self.record_file_name, 'w') as f:
            for obj in self.objs:
                f.write(f"obj: {obj}\n")
                f.write(f"best: {self.best_vals[obj]}\n")
                for i in self.best_pairs[obj]:
                    f.write(f"best pair : {i} \n")
                f.write("iteration, current_best_val, current_val, time\n")
                for i in range(1, self.iterations + 1):
                    total_time += self.history[obj][i][2]
                    f.write(f"{i}, {self.history[obj][i][0]:>2}, {self.history[obj][i][1]}, {total_time:>4.2f}\n")