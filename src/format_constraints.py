from settings import MAX_PARAMETER_VALUE, NEGATIVE_PARAMETER_VALUE
import torch

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
        self.individual_constraints = indvidual_constraint

    def check_condition_included(self, condition):
        if condition[0] < self.individual_constraints[0] or condition[1] > self.individual_constraints[1]:
            raise Exception('Condition out of range')
        
        if condition in self.conditions:
            return self.conditions.index(condition)
        else:
            self.conditions.append(condition)
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
        overall_constraint_sum = 0
        for or_constraints in self.linked_constraints:
            max_constraint_sum = NEGATIVE_PARAMETER_VALUE
            for linked_constraint in or_constraints:
                constraint_sum = 0
                for constraint in linked_constraint.keys():
                    constraint_sum += data[constraint][linked_constraint[constraint]][X_index]
                print("constraint_sum: ", constraint_sum)
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




if __name__ == '__main__':
    c = Constraints(2)
    c.update_self_constraints(0, [1, 16])
    c.update_self_constraints(1, [4, 252])
    c.update_scale(1, 4)
    c.update_new_constraints({0: [1, 4], 1: [4, 4]})
    c.print_linked_constraints()