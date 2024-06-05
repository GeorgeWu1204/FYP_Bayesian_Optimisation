import torch
import math

MAX_PARAMETER_VALUE = 1000
NEGATIVE_PARAMETER_VALUE = -1000

def calculate_int_condition(x, condition):
    """This function is used to calculate the input constraints"""
    return (x - condition[0]) * (condition[1] - x)

def calculate_categorical_condition(x, categorical_range, condition):
    #x dim = [num_categories, num_restarts * q_dim]
    index = torch.argmax(x, dim=1)
    return calculate_int_condition(int(categorical_range[index]), condition)

def extract_categorical_parameters_from_flatten_data(data, total_amount, d_dim, categorical_info):
    extracted_data = []
    for i in range(total_amount):
        start_idx = i * d_dim + categorical_info[0]
        end_idx = start_idx + categorical_info[1]
        if end_idx <= len(data):
            extracted_data.append(data[start_idx:end_idx])
    result = torch.stack(extracted_data)
    return result

def build_matrix(data, constraints, num_restarts, q_dim, d_dim):
    """Build a matrix to store all the results of whether the input data meet the constraints."""
    # formatted_correlated_constraints = {d_dim : matrix of shape (condition_size * (num_restarts * q_dim))}
    formatted_correlated_constraints = {}
    individual_constraint = torch.empty((d_dim, num_restarts * q_dim))
    flat_data = data.flatten()

    for i in range(d_dim):
        # individual constraint
        # individual_constraint[i] = calculate_int_condition(selected_data, constraints.Node[i].individual_constraints)
        skip = False
        # Categorical
        for categorical_info in constraints.categorical_info.values():
            if i == categorical_info[0]:
                condition_size = constraints.Node[i].condition_size()
                cal_condition = torch.empty((condition_size, num_restarts * q_dim))
                extracted_data = extract_categorical_parameters_from_flatten_data(flat_data, num_restarts * q_dim, d_dim, categorical_info)
                for j in range(0, constraints.Node[i].condition_size()):
                    cal_condition[j] = calculate_categorical_condition(extracted_data, categorical_info[2], constraints.Node[i].conditions[j])
                formatted_correlated_constraints[i] = cal_condition
                skip = True
                continue
            elif i > categorical_info[0] and i < categorical_info[0] + categorical_info[1]:
                skip = True
                continue
        if skip:
            continue
        # Integer Valued Constraints
        if(constraints.Node[i].have_constraints()):
            indices = torch.arange(start = i, end = len(flat_data), step = d_dim)
            selected_data = flat_data[indices]
            # Coupled Constraints
            condition_size = constraints.Node[i].condition_size()
            cal_condition = torch.empty((condition_size, num_restarts * q_dim))
            for j in range(0, constraints.Node[i].condition_size()):
                cal_condition[j] = calculate_int_condition(selected_data, constraints.Node[i].conditions[j])
            formatted_correlated_constraints[i] = cal_condition
    return individual_constraint, formatted_correlated_constraints

class Constraints_Node:
    def __init__(self, index):
        self.individual_constraints = [0, 1]    # Here we assume all of the parameters are normalised
        self.index = index
        self.scale = 1
        self.conditions = []
        self.normalized_factor = 1
        self.rounded_region = 0.45/(self.scale * self.normalized_factor)
        self.offset = 0
        self.exp_factor = 1
        self.type = 'Int'

    def initialize_scale_normalise_exp_factor(self, scale, normalized_factor, exp_factor):
        self.scale = scale
        self.normalized_factor = normalized_factor
        self.rounded_region = 0.45/(self.scale * self.normalized_factor)

    def have_constraints(self):
        return (len(self.conditions) > 0)

    def update_offset(self, offset):
        self.offset = offset
    
    def condition_size(self):
        return len(self.conditions)

    def check_condition_included(self, condition, parameter_type):
        # TODOTODO, need to modify due to the change of normalisation
        """Check whether the condition is included in the condition list. If not, add it to the list."""
        if parameter_type == 'Int':
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
            # This is to avoid multiple same conditions in the list.
        elif parameter_type == 'Categorical':
            tmp_condition = condition

        if tmp_condition in self.conditions:
            return self.conditions.index(condition)
        else:
            self.conditions.append(tmp_condition)
            return len(self.conditions) - 1
        
       

class Input_Constraints:
    def __init__(self, dim, input_names, categorical_info, device):  
        #linked_constraints = [[or_constraints = {constraints 1, constraints 2}], [or_constraints], ...]]
        self.dim = dim
        self.Node = [Constraints_Node(i) for i in range(dim)]
        self.linked_constraints = []
        self.normalized_factors = []
        self.input_names_index = {}
        self.categorical_info = categorical_info
        self.constraint_bound = torch.empty((2, dim), device=device)
        input_name_start_index = 0
        input_name_index = 0
        if self.categorical_info is not None:
            for key in self.categorical_info.keys():
                for index in range(self.categorical_info[key][0], self.categorical_info[key][0] + self.categorical_info[key][1]):
                    self.Node[index].type = 'Categorical'
                # To build the input_names_index
                if input_name_start_index <= self.categorical_info[key][0]:
                    for i in range(input_name_start_index, self.categorical_info[key][0] + 1):
                        self.input_names_index[input_names[input_name_index]] = i
                        input_name_index += 1
                    input_name_start_index = self.categorical_info[key][0] + self.categorical_info[key][1]
            if input_name_start_index < dim:
                for i in range(input_name_start_index, dim):
                    self.input_names_index[input_names[input_name_index]] = i
                    input_name_index += 1
                
        
    def update_self_constraints(self, index, indvidual_constraint):
        self.Node[index].update_offset(indvidual_constraint[0])
        # constraint_bound is used to set the bound for the acquisition function.
        self.constraint_bound[:,index] = torch.tensor(self.Node[index].individual_constraints)


    def update_integer_transform_info(self, input_offset, scales, normalized_factors, exp_factors):
        self.normalized_factors = normalized_factors
        for index in range(self.dim):
            self.Node[index].initialize_scale_normalise_exp_factor(scales[index], normalized_factors[index], exp_factors[index])
            self.Node[index].update_offset(input_offset[index])

    def update_coupled_constraints(self, new_constraints):
        # new_constraints = {index: [condition]}
        and_constraint = []
        for or_constraint in new_constraints:
            linked_constraint = {}
            for constraint_var_name in or_constraint.keys():
                constraint_var_index = self.input_names_index[constraint_var_name]

                if constraint_var_name in self.categorical_info.keys():
                    condition_index_within_node = self.Node[constraint_var_index].check_condition_included(or_constraint[constraint_var_name], 'Categorical')
                else:
                    if(constraint_var_index >= self.dim):
                        raise Exception('Constraint variable index out of range')
                    condition_index_within_node = self.Node[constraint_var_index].check_condition_included(or_constraint[constraint_var_name], 'Int')
                linked_constraint[constraint_var_index] = condition_index_within_node
            and_constraint.append(linked_constraint)
        self.linked_constraints.append(and_constraint)

    def check_meet_constraint(self, formatted_correlated_constraints, X_index):
        #X_index : the index of the candidtate of the point.
        overall_constraint_sum = 0
        # # check meet the individual constraint
        # for individual_constraint_index in range(self.dim):
        #     if(individual_constraint[individual_constraint_index][X_index] < 0):
        #         #if the initial condition is not met, return the value of the constraint.
        #         return individual_constraint[individual_constraint_index][X_index]
        #     else:
        #         overall_constraint_sum += individual_constraint[individual_constraint_index][X_index]
        # check meet the conditional constraint
        for or_constraints in self.linked_constraints:
            # loop through all the or_constraints sets in the linked_constraints
            max_constraint_sum = torch.tensor(NEGATIVE_PARAMETER_VALUE)
            for linked_constraint in or_constraints:
                # loop through all the constraints in the or_constraints
                constraint_sum = 0
                for constraint in linked_constraint.keys():
                    # loop through all the constraints in the and_constraint
                    if(formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index] < 0):
                        # constraint_sum = torch.tensor(NEGATIVE_PARAMETER_VALUE)
                        constraint_sum = formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index]
                        break
                    else:
                        constraint_sum += formatted_correlated_constraints[constraint][linked_constraint[constraint]][X_index]
                if(constraint_sum > max_constraint_sum):
                    max_constraint_sum = constraint_sum.clone()
            if(max_constraint_sum < 0):
                #within a or_constraint, if all the and_constraint are not satisfied, the or_constraint is not satisfied.
                return max_constraint_sum
            overall_constraint_sum += max_constraint_sum
        return overall_constraint_sum
    
    
    def check_single_point_meet_constraint(self, X):
        q_dim = 1
        x_input = X.unsqueeze(0)
        _, correlated_constraints = build_matrix(x_input, self, 1, q_dim, self.dim)
        if self.check_meet_constraint(correlated_constraints, 0) > 0:
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

        _, correlated_constraints = build_matrix(re_organized_x, self, num_restarts, q_dim, d_dim)
        inequality_constraints = torch.empty((num_restarts, q_dim), dtype=X.dtype)
        for i in range(num_restarts):
            for j in range(q_dim):
                inequality_constraints[i][j] = self.check_meet_constraint(correlated_constraints, i * q_dim + j)
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