import ast
import torch
# Read the file

class Data_Sample:
    def __init__(self, data, objs):
        self.Constraints = data[0]
        self.Cycle_count = data[1]
        self.PPA = {}
        for obj in objs:
            self.PPA[obj] = data[2][obj]
    def print_constraints(self):
        print("Constraints:")
        for k, v in self.Constraints.items():
            print(f"{k} = {v}")

    def print_cycle_count(self):
        print("Cycle count:")
        for k, v in self.Cycle_count.items():
            print(f"{k} = {v}")
    
    def print_ppa(self):
        print("PPA:")
        for k, v in self.PPA.items():
            print(f"{k} = {v}")
    def get_ppa(self, obj):
        return self.PPA[obj]    

class Data_Set:
    def __init__(self, data, objs, scales):
        for i in range(len(data)):
            d_input_dic = data[i][0]
            d_input = [val for val in d_input_dic.values()]
            for i in range(len(d_input)):
                d_input[i] = round(d_input[i] / scales[i])
            self.__dict__[tuple(d_input)] = Data_Sample(data[i], objs)
    def __len__(self):
        return len(self.__dict__)
    
    def list_all_contraints(self):
        constraints = []
        for i in self.__dict__.keys():
            constraints.append(self.__dict__.get(i).Constraints)
        return constraints
    
    def find_BTB_constraints(self, constraint):
        Pre_Type = []
        for i in self.__dict__.keys():
            tmp_constraint = self.__dict__.get(i).Constraints
            if tmp_constraint['BTB'] == constraint:
                Pre_Type.append(tmp_constraint['Pre_Type'])
        return Pre_Type
    
    def find_Pre_Type_constraints(self, constraint):
        BTB = []
        for i in self.__dict__.keys():
            tmp_constraint = self.__dict__.get(i).Constraints
            if tmp_constraint['Pre_Type'] == constraint:
                BTB.append(tmp_constraint['BTB'])
        return BTB
    
    def find_ppa_result(self, constraints, obj, dtype):
        print("constraints", constraints.shape)
        num_constraints = constraints.shape[0]
        result = torch.zeros(num_constraints, dtype=dtype)
        for i in range(0, num_constraints):
            constraint = constraints[i].tolist()
            print("constraint", constraint)
            result[i] = self.__dict__.get(tuple(constraint)).get_ppa(obj)
        return result
 
    


def read_from_data(file_name, objs, scales):
    with open(file_name, 'r') as f:
        content = f.read()
        raw_data = ast.literal_eval(content)
        print("objs", objs) 
        data_set = Data_Set(raw_data, objs, scales)
    return data_set

