import torch

def calculate_condition(x, condition):
    return (x - condition[0]) * (condition[1] - x)

def build_matrix(data, constraints, num_restarts, q_dim, d_dim):
    # formatted_data = {d_dim : [condition_size, num_restarts * q_dim]}
    formatted_data = {}
    flat_data = data.flatten()
    for i in range(d_dim):
        if(constraints.Node[i].have_constraints()):
            condition_size = constraints.Node[i].condition_size()
            indices = torch.arange(start = i, end = len(flat_data), step = d_dim)
            selected_data = flat_data[indices]
            cal_condition = torch.empty((condition_size, num_restarts * q_dim))
            for j in range(constraints.Node[i].condition_size()):
                cal_condition[j] = calculate_condition(selected_data, constraints.Node[i].conditions[j])
            formatted_data[i] = cal_condition
    return formatted_data

def normalise_generated_data(input_tensor, normalized_factors):
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = input_tensor[i][j] / normalized_factors[j]

    return output_tensor

def recover_generated_data(input_tensor, normalized_factors, scaled_factors):
    num_restarts, d_dim = input_tensor.shape
    print("input_tensor: ", input_tensor.shape, "\n", input_tensor)
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = torch.round(input_tensor[i][j] * normalized_factors[j]) * scaled_factors[j] 
    print("recovered output_tensor: ", output_tensor.shape, "\n", output_tensor)
    return output_tensor