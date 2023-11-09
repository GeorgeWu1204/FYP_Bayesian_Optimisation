import numpy as np
import torch
from format_constraints import Constraints


def calculate_condition(x, condition, scale):
    return (x - condition[0]) * (condition[1] - x) / (scale ** 2)

def build_matrix(data, constraints, num_restarts, q_dim, d_dim):
    formatted_data = {}
    flat_data = data.flatten()
    for i in range(d_dim):
        if(constraints.Node[i].have_constraints()):
            condition_size = constraints.Node[i].condition_size()
            indices = torch.arange(start = i, end = len(flat_data), step = d_dim)
            selected_data = flat_data[indices]
            cal_condition = torch.empty((condition_size, num_restarts * q_dim))
            for j in range(constraints.Node[i].condition_size()):
                cal_condition[j] = calculate_condition(selected_data, constraints.Node[i].conditions[j], constraints.Node[i].scale)
            
            formatted_data[i] = cal_condition

    return formatted_data


if __name__ == '__main__':
    c = Constraints(2)
    c.update_self_constraints(0, [1, 6])
    c.update_self_constraints(1, [4, 252])
    c.update_new_constraints([{0: [1, 4], 1: [4, 4]}, {0: [4, 6], 1: [4, 252]}])
    c.update_scale(1, 4)

    # tensor
    tensor = torch.tensor([[[5, 4]]])
    num_restarts = 1
    q_dim = 1
    d_dim = 2

    d_data = build_matrix(tensor, c, num_restarts, q_dim, d_dim)
    print(d_data)
    result = c.check_meet_constraint(d_data, 0)
    print(result)

