import torch
import numpy as np
import random
from utils import build_matrix
import math

MAX_PARAMETER_VALUE = 1000
NEGATIVE_PARAMETER_VALUE = -1000

class Constraints_Node:
    def __init__(self, index):
        self.individual_constraints = [0, 1]
        self.index = index
        self.scale = 1
        self.conditions = []
        self.normalized_factor = 1
        self.rounded_region = 0.45/(self.scale * self.normalized_factor)
        self.offset = 0
        self.exp_factor = 1

    def initialize_scale_normalise_exp_factor(self, scale, normalized_factor, exp_factor):
        self.scale = scale
        self.normalized_factor = normalized_factor
        self.rounded_region = 0.45/(self.scale * self.normalized_factor)

    def have_constraints(self):
        return (len(self.conditions) > 0)

    def update_offset(self, offset):
        self.offset = offset

    def check_condition_included(self, condition):
        # TODOTODO, need to modify due to the change of normalisation
        """Check whether the condition is included in the condition list. If not, add it to the list."""
        if self.exp_factor != 1:
            lower_bound_cond = int(math.log(condition[0], self.exp_factor) - self.offset ) / (self.scale * self.normalized_factor) - self.rounded_region 
            upper_bound_cond = int(math.log(condition[1], self.exp_factor) - self.offset ) / (self.scale * self.normalized_factor) + self.rounded_region
        else:
            lower_bound_cond = (condition[0] - self.offset) / (self.scale * self.normalized_factor) - self.rounded_region 
            upper_bound_cond = (condition[1] - self.offset) / (self.scale * self.normalized_factor) + self.rounded_region 
        
        if lower_bound_cond < self.individual_constraints[0] or upper_bound_cond > self.individual_constraints[1]:
            lower_bound_cond = max(lower_bound_cond, self.individual_constraints[0])
            upper_bound_cond = min(upper_bound_cond, self.individual_constraints[1])
        tmp_condition = [lower_bound_cond, upper_bound_cond]
        if tmp_condition in self.conditions:
            return self.conditions.index(condition)
        else:
            self.conditions.append(tmp_condition)
            return len(self.conditions) - 1


class Input_Constraints:

    def __init__(self, dim, device):  
        #linked_constraints = [[or_constraints = {constraints 1, constraints 2}], [or_constraints], ...]]
        self.dim = dim
        self.Node = [Constraints_Node(i) for i in range(dim)]
        self.linked_constraints = []
        self.normalized_factors = []
        self.normalized_bound = torch.empty((2, dim), device=device)
        self.constraint_bound = torch.empty((2, dim), device=device)
    
    def update_self_constraints(self, index, indvidual_constraint):
        self.Node[index].update_offset(indvidual_constraint[0])
        self.normalized_bound[:,index] = torch.tensor([indvidual_constraint[0], indvidual_constraint[1]])
        # constraint_bound is used to set the bound for the acquisition function.
        self.constraint_bound[:,index] = torch.tensor(self.Node[index].individual_constraints)
        print(self.normalized_bound)

    def update_scale_normalize_exp_factor(self, scales, normalized_factors, exp_factors):
        self.normalized_factors = normalized_factors
        for index in range(self.dim):
            self.Node[index].initialize_scale_normalise_exp_factor(scales[index], normalized_factors[index], exp_factors[index])

    def update_coupled_constraints(self, new_constraints):
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

    def check_meet_constraint(self, individual_constraint, formatted_correlated_constraints, X_index):
        #X_index : the index of the candidtate of the point.
        overall_constraint_sum = 0
        # check meet the individual constraint
        for individual_constraint_index in range(self.dim):
            if(individual_constraint[individual_constraint_index][X_index] < 0):
                #if the initial condition is not met, return the value of the constraint.
                return individual_constraint[individual_constraint_index][X_index]
            else:
                overall_constraint_sum += individual_constraint[individual_constraint_index][X_index]
        # check meet the coupled constraint
        for or_constraints in self.linked_constraints:
            # loop through all the or_constraints sets in the linked_constraints
            max_constraint_sum = torch.tensor(NEGATIVE_PARAMETER_VALUE)
            for linked_constraint in or_constraints:
                # loop through all the constraints in the or_constraints
                constraint_sum = 0
                for constraint in linked_constraint.keys():
                    # loop through all the constraints in the and_constraint
                    if(formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index] <= 0):
                        # constraint_sum = torch.tensor(NEGATIVE_PARAMETER_VALUE)
                        constraint_sum = formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index]
                        break
                    else:
                        constraint_sum += formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index]
                if(constraint_sum > max_constraint_sum):
                    max_constraint_sum = constraint_sum.clone()
            if(max_constraint_sum <= 0):
                #within a or_constraint, if all the and_constraint are not satisfied, the or_constraint is not satisfied.
                return max_constraint_sum
            overall_constraint_sum += max_constraint_sum
        return overall_constraint_sum
    
    
    def check_single_point_meet_constraint(self, X):
        q_dim = 1
        x_input = X.unsqueeze(0)
        individual_constraint, correlated_constraints = build_matrix(x_input, self, 1, q_dim, self.dim)
        if self.check_meet_constraint(individual_constraint, correlated_constraints, 0) > 0:
            return True
        else:
            return False
    
            
    def get_nonlinear_inequality_constraints(self, X):
        if(X.shape[0] == self.dim):
            # To be confirmed At the initial part of the optimisation, the batch size is the same as the dimension of the data.
            d_dim = self.dim
            q_dim = 1       #nonlinear_inequality has restricted the batch size to be 1.
            num_restarts = round(X.shape[0]/(d_dim * q_dim)) 
            re_organized_x = X.reshape((num_restarts, q_dim, d_dim))
        else:
            num_restarts, q_dim, d_dim = X.shape
            re_organized_x = X

        individual_constraint, correlated_constraints = build_matrix(re_organized_x, self, num_restarts, q_dim, d_dim)
        inequality_constraints = torch.empty((num_restarts, q_dim), dtype=X.dtype)
        for i in range(num_restarts):
            for j in range(q_dim):
                inequality_constraints[i][j] = self.check_meet_constraint(individual_constraint, correlated_constraints, i * q_dim + j)
        return inequality_constraints
    
            
class Simpler_Constraints:
    def __init__(self, obj_to_optimise_dim, obj_to_check_constraints_dim):
        self.self_constraints = []
        self.output_obj_constraint = []
        self.output_obj_constraint_index = [i for i in range(obj_to_optimise_dim, obj_to_optimise_dim + obj_to_check_constraints_dim)]
    
    def update_self_constraints(self, self_constraints):
        self.self_constraints.append(self_constraints)
    
    def update_output_obj_constraint(self, output_obj_constraint):
        self.output_obj_constraint.append(output_obj_constraint)
    
    def check_meet_self_constraint_for_brute_force(self, X):
        for index, element in enumerate(X):
            if element < self.self_constraints[index][0] or element > self.self_constraints[index][1]:
                return False
        return True

    def check_meet_output_obj_constraint_for_brute_force(self, X, obj_for_optimise_dim):
        for i in self.output_obj_constraint_index:
            if X[i] < self.output_obj_constraint[i - obj_for_optimise_dim][0] or X[i] > self.output_obj_constraint[i - obj_for_optimise_dim][1]:
                return False
        return True



        
if __name__ == '__main__':
    c = Input_Constraints(2)
    c.update_self_constraints(0, [1, 6])
    c.update_self_constraints(1, [4, 252])
    c.update_coupled_constraints([{0: [1, 4], 1: [4, 4]}, {0: [4, 6], 1: [4, 252]}])
    c.update_scale(1, 4)

    tensor = torch.tensor([[[3, 4]]])
    print(tensor.shape)
    num_restarts = 1
    q_dim = 1
    d_dim = 2
    # result = c.check_meet_constraint(d_data, 0)
    # print(result)
    # test = c.create_initial_data(1)