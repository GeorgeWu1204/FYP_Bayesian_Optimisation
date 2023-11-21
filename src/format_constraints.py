from settings import MAX_PARAMETER_VALUE, NEGATIVE_PARAMETER_VALUE
import torch
import numpy as np
import random
from utils import build_matrix, normalise_generated_data


class Constraints_Node:
    def __init__(self, index):
        self.individual_constraints = [0, MAX_PARAMETER_VALUE]
        self.index = index
        self.scale = 1
        self.conditions = []
        self.normalized_factor = 1

    def initialize_scale(self, scale):
        self.scale = scale
    
    def initialize_normalized_factor(self, normalized_factor):
        self.normalized_factor = normalized_factor

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
        #linked_constraints = [[or_constraints = {constraints 1, constraints 2}], [or_constraints], ...]]
        self.dim = dim
        self.Node = [Constraints_Node(i) for i in range(dim)]
        self.linked_constraints = []
        self.normalized_factors = []
    
    def update_normalize_factor(self, normalized_factors):
        # not sure whether it is the most efficient way to normalise the data
        self.normalized_factors = normalized_factors
        for index, factor in enumerate(normalized_factors):
            self.Node[index].initialize_normalized_factor(factor)
    
    def update_self_constraints(self, index, indvidual_constraint):
        self.Node[index].initialize_self_constraints([indvidual_constraint[0], indvidual_constraint[1]])

    def update_scale(self, scales):
        for index, scale in enumerate(scales):
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
    
    def create_initial_data(self, num_of_start, bounds, output_type):
        q_dim = 1
        output_tensor = torch.empty((num_of_start, self.dim), dtype=output_type)
        for i in range(num_of_start):
            valid_initial_tensor = torch.zeros((1, 1, self.dim), dtype=output_type)
            data_matrix = build_matrix(valid_initial_tensor, self, 1, q_dim, self.dim)
            while(self.check_meet_constraint(data_matrix, num_of_start) < 0):
                valid_initial_tensor = torch.rand((1, 1, self.dim), dtype=output_type) * (bounds[:, 1] - bounds[:, 0]) + bounds[:, 0]
                data_matrix = build_matrix(valid_initial_tensor, self, 1, q_dim, self.dim)
            output_tensor[i] = valid_initial_tensor.squeeze()
        normalise_generated_data(output_tensor, self.normalized_factors)
        return output_tensor
            
    def get_inequality_constraints(self, X):
        #input X: [num_restarts, q_dim, d_dim] ===> [num_restarts, q_dim]
        num_restarts, q_dim, d_dim = X.shape
        data_matrix = build_matrix(X, self, num_restarts, q_dim, d_dim)
        inequality_constraints = torch.empty((num_restarts, q_dim), dtype=X.dtype)
        for i in range(num_restarts):
            for j in range(q_dim):
                inequality_constraints[i][j] = self.check_meet_constraint(data_matrix, i * q_dim + j)

        return inequality_constraints



        
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