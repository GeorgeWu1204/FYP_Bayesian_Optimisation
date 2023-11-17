from settings import MAX_PARAMETER_VALUE, NEGATIVE_PARAMETER_VALUE
import torch
import numpy as np
import random

def calculate_condition(x, condition):
    return (x - condition[0]) * (condition[1] - x)

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
                cal_condition[j] = calculate_condition(selected_data, constraints.Node[i].conditions[j])
            
            formatted_data[i] = cal_condition

    return formatted_data

class Constraints_Node:
    def __init__(self, index):
        self.individual_constraints = [0, MAX_PARAMETER_VALUE]
        self.index = index
        self.scale = 1
        self.conditions = []

    def initialize_scale(self, scale):
        self.scale = scale

    def have_constraints(self):
        return (len(self.conditions) > 0)

    def condition_size(self):
        return len(self.conditions)

    def initialize_self_constraints(self, indvidual_constraint):
        self.individual_constraints = [x/self.scale for x in indvidual_constraint]

    def check_condition_included(self, condition):
        
        lower_bound_cond = round(condition[0] / self.scale)
        upper_bound_cond = round(condition[1] / self.scale)

        if lower_bound_cond < self.individual_constraints[0] or upper_bound_cond > self.individual_constraints[1]:
            raise Exception('Condition out of range')
        tmp_condition = [lower_bound_cond, upper_bound_cond]
        
        if tmp_condition in self.conditions:
            return self.conditions.index(condition)
        else:
            self.conditions.append(tmp_condition)
            return len(self.conditions) - 1


class Constraints:

    def __init__(self, dim):  
        self.dim = dim
        self.Node = [Constraints_Node(i) for i in range(dim)]
        self.linked_constraints = []
        #linked_constraints = [[or_constraints = {constraints 1, constraints 2}], [or_constraints], ...]]
    
    def update_self_constraints(self, index, indvidual_constraint):
        self.Node[index].initialize_self_constraints([indvidual_constraint[0], indvidual_constraint[1]])

    def update_scale(self, index, scale):
        self.Node[index].initialize_scale(scale)

    def update_new_constraints(self, new_constraints):
        # new_constraints = {index: [condition]}
        and_constraint = []
        for or_constraint in new_constraints:
            linked_constraint = {}
            for constraint_var_index in or_constraint.keys():
                if(constraint_var_index >= self.dim):
                    raise Exception('Constraint variable index out of range')
                condition_index_within_node = self.Node[constraint_var_index].check_condition_included(or_constraint[constraint_var_index])
                linked_constraint[constraint_var_index] = condition_index_within_node
            and_constraint.append(linked_constraint)
        self.linked_constraints.append(and_constraint)

    def check_meet_constraint(self, data, X_index):
        #X_index : the index of the candidtate of the point.
        overall_constraint_sum = 0
        for or_constraints in self.linked_constraints:
            max_constraint_sum = NEGATIVE_PARAMETER_VALUE
            for linked_constraint in or_constraints:
                constraint_sum = 0
                for constraint in linked_constraint.keys():
                    if(data[constraint][linked_constraint[constraint]][X_index] <0):
                        constraint_sum = NEGATIVE_PARAMETER_VALUE
                        break
                    else:
                        constraint_sum += data[constraint][linked_constraint[constraint]][X_index]
                if(constraint_sum > max_constraint_sum):
                    max_constraint_sum = constraint_sum.clone()
            if(max_constraint_sum < 0):
                return max_constraint_sum
            overall_constraint_sum += max_constraint_sum
        return overall_constraint_sum
    
    def print_linked_constraints(self):
        for or_constraints in self.linked_constraints:
            for linked_constraint in or_constraints:
                for constraint in linked_constraint.keys():
                    print("At D ", constraint, "D col: ", linked_constraint[constraint])
                    print("Condition: ", self.Node[constraint].conditions[linked_constraint[constraint]])
    
    def create_initial_data(self, num_of_start, bounds, dtype):
        q_dim = 1
        output_tensor = torch.empty((num_of_start, self.dim), dtype=dtype)
        for i in range(num_of_start):
            valid_initial_tensor = torch.zeros((1, 1, self.dim), dtype=dtype)
            data_matrix = build_matrix(valid_initial_tensor, self, 1, q_dim, self.dim)
            while(self.check_meet_constraint(data_matrix, 0) < 0):
                for j in range(self.dim):
                    valid_initial_tensor[0][0][j] = random.randint(bounds[j][0], bounds[j][1])
                data_matrix = build_matrix(valid_initial_tensor, self, 1, q_dim, self.dim)
            print("final data_matrix", data_matrix)
            print("check_meet_constraint", self.check_meet_constraint(data_matrix, 0))
            output_tensor[i] = valid_initial_tensor.squeeze()
        return output_tensor
            

        
if __name__ == '__main__':
    c = Constraints(2)
    c.update_self_constraints(0, [1, 6])
    c.update_self_constraints(1, [4, 252])
    c.update_new_constraints([{0: [1, 4], 1: [4, 4]}, {0: [4, 6], 1: [4, 252]}])
    c.update_scale(1, 4)

    # tensor

    tensor = torch.tensor([[[3, 4]]])
    print(tensor.shape)
    num_restarts = 1
    q_dim = 1
    d_dim = 2
    # result = c.check_meet_constraint(d_data, 0)
    # print(result)
    test = c.create_initial_data(1)