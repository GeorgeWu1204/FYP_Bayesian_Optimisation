import ast
import torch
from pprint import PrettyPrinter
from colorama import Fore, Back, Style
import glob
import sys
import pickle
import os.path as osp
# Read the file
from utils import calculate_condition, calculate_smooth_condition, recover_single_input_data
from botorch.utils.transforms import unnormalize


class Data_Sample:
    def __init__(self, data, objs, data_set_type):
        if (data_set_type == 'txt'):
            self.Constraints = data[0]
            self.Cycle_count = data[1]
            self.PPA = {}
            for obj in objs:
                self.PPA[obj] = data[2][obj]
        elif (data_set_type == 'db'):
            self.Constraints = data[0]
            self.Cycle_count = None
            self.PPA = {}
            for obj in objs:
                self.PPA[obj] = data[1][obj]
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
        return self.PPA.get(obj, None)   

class Data_Set:
    def __init__(self, data, objs, scales, input_data_normalized_factors, offsets, output_obj_constraint, data_set_type = 'txt', tensor_type = torch.float64, tensor_device = torch.device('cpu')):
        val_list = {}
        self.best_value = {}
        self.best_pair = {}
        self.worst_value = {}
        # to recover the output data
        self.objs_direct = objs
        self.objs_to_optimise_dim = len(objs)
        self.objs_to_evaluate = list(objs.keys()) + list(output_obj_constraint.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        self.output_normalised_factors = {}
        # to recover the input data
        self.input_normalized_factors = torch.tensor(input_data_normalized_factors, dtype=tensor_type, device=tensor_device)
        self.scaled_factors = torch.tensor(scales, dtype=tensor_type, device=tensor_device)
        self.offsets = torch.tensor(offsets, dtype=tensor_type, device=tensor_device)
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
            
        if data_set_type == 'txt':
            for i in range(len(data)):
                d_input_dic = data[i][0]
                d_input = [val for val in d_input_dic.values()]
                self.__dict__[tuple(d_input)] = Data_Sample(data[i], self.objs_to_evaluate, data_set_type)
                
        elif data_set_type == 'db':
            for obj in self.objs_to_evaluate:
                val_list[obj] = []
            for i in data.keys():
                self.__dict__[i] = Data_Sample([i, data[i]], self.objs_to_evaluate, data_set_type)
                for obj in self.objs_to_evaluate:
                    val_list[obj].append(data[i][obj])
            for obj in self.objs_to_evaluate:
                if objs.get(obj, None) == 'minimise':
                    self.best_value[obj] = min(val_list[obj])
                    self.worst_value[obj] = max(val_list[obj])
                else:
                    self.best_value[obj] = max(val_list[obj])
                    self.worst_value[obj] = min(val_list[obj])

                self.best_pair[obj] = [[i] for i in data.keys() if data[i][obj] == self.best_value[obj]][0]
                
                if self.best_value[obj] == self.worst_value[obj]:
                    # if the best value is the same as the worst value, then the normalised factor is 1
                    self.output_normalised_factors[obj] = 1.0
                else:
                    # self.output_normalised_factors[obj] = abs(self.best_value[obj] - self.worst_value[obj])
                    self.output_normalised_factors[obj] = abs(self.best_value[obj])
        
        self.output_constraints_to_check = []
        for obj in output_obj_constraint:
            self.output_constraints_to_check.append([bound / self.output_normalised_factors[obj] for bound in output_obj_constraint[obj]])
    
    def list_all_contraints(self):
        constraints = []
        for i in self.__dict__.keys():
            constraints.append(self.__dict__.get(i).Constraints)
        return constraints
    
    def find_ppa_result(self, sample_inputs, dtype):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=dtype)
        obj_index = 0
        for i in range(num_restart):
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.scaled_factors, self.offsets)
            for obj_index in range(self.objs_to_evaluate_dim):
                obj = self.objs_to_evaluate[obj_index]
                results[i][obj_index] = self.__dict__.get(tuple(input)).get_ppa(obj)
                if self.objs_direct.get(obj, None) == 'minimise':
                    results[i][obj_index] = -1 * results[i][obj_index]
                obj_index += 1

        return results
    
    def find_single_ppa_result(self, sample_input):
        """This function is used to find the ppa result for a single input, only used in result recording"""
        result = []
        recovered_sample_input = []
        # [round(x + y) for x, y in zip(sample_input, self.input_offset)]
        for i in range(len(sample_input)):
            recovered_sample_input.append(round(sample_input[i] * self.input_normalized_factors[i].item()) * self.scaled_factors[i].item()) + self.offsets[i].item()
        
        for obj in self.objs_to_evaluate:
            result.append(self.__dict__.get(tuple(recovered_sample_input)).get_ppa(obj))
        return result

    def find_single_ppa_result_for_brute_force(self, sample_input):
        """This function is used to find the ppa result for a single input, only used in result recording"""
        result = []
        for  obj in self.objs_to_evaluate:
            result.append(self.__dict__.get(tuple(sample_input)).get_ppa(obj))
        return result
    

    def check_qEHVI_constraints(self, X):
        """This is the callable function for the output constraints of the qEHVI acq function"""
        # X shape sample_shape x batch-shape x q x m , Output shape sample_shape x batch-shape x q
        results = torch.zeros((X.shape[0], X.shape[1], X.shape[2]), device=X.device, dtype=X.dtype)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                for k in range(X.shape[2]):
                    for obj_index in range(self.objs_to_optimise_dim, X.shape[3]):
                        condition_val = calculate_condition(X[i][j][k][obj_index], self.output_constraints_to_check[obj_index - self.objs_to_optimise_dim])
                        if  condition_val < 0:
                            results[i][j][k] = 1e-3
                            break
                        else:
                            results[i][j][k] -= condition_val
        return results

    def check_qNEHVI_constraints(self, X):
        """This is the callable function for the output constraints of the qNEHVI acq function"""
        # X shape n x m , Output shape n x 1
        # Negative implies feasible
        results = torch.zeros((X.shape[0], 1), device=X.device, dtype=X.dtype)
        for i in range(X.shape[0]):
            condition_vals = []
            for obj_index in range(self.objs_to_optimise_dim, X.shape[1]):
                condition_val = calculate_smooth_condition(X[i][obj_index], self.output_constraints_to_check[obj_index - self.objs_to_optimise_dim])
                condition_vals.append(condition_val)
            results[i] = max(condition_vals)
        return results


def read_data_from_txt(file_name, objs, scales, input_data_normalized_factors):
    with open(file_name, 'r') as f:
        content = f.read()
        raw_data = ast.literal_eval(content)
        print("objs", objs) 
        data_set = Data_Set(raw_data, objs, scales, input_data_normalized_factors, 'txt')
    return data_set

def read_data_from_db(db_name, objs, output_obj_constraint, scales, input_data_normalized_factors, input_offsets, type, device):
    db = {}
    if not osp.exists(db_name):
        print(f"[i] generating: '{db_name}'")
        if len(sys.argv) == 2:
            loc = sys.argv[1]
        else:
            loc = "**"

        for dbf in glob.glob(f'{loc}/ppa*.db', recursive=True):
            print(f"[i] loading db: '{dbf}'")
            with open(dbf, 'r') as f:
                local_db = eval(f.read())
                db.update(local_db)

        # pickle our database
        with open(db_name, 'wb') as f:
            pickle.dump(db, f)
    else:
        print(f"[i] loading: '{db_name}'")
        with open(db_name, 'rb') as f:
            db.update(pickle.load(f))
    data_set = Data_Set(db, objs, scales, input_data_normalized_factors, input_offsets, output_obj_constraint, 'db', type, device)
    return data_set
    



if __name__ == '__main__':
    read_data_from_db("../data/ppa_v2.db", ['lut'], [1, 1, 1], [1, 1, 1])