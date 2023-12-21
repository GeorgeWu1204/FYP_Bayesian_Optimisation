import ast
import torch
import statistics
from pprint import PrettyPrinter
from colorama import Fore, Back, Style
import glob
import sys
import pickle
import os.path as osp
# Read the file
from utils import recover_generated_data

pp = PrettyPrinter(indent=4)


class Data_Sample:
    def __init__(self, data, objs, data_set_type):
        if (data_set_type == 'txt'):
            self.Constraints = data[0]
            self.Cycle_count = data[1]
            self.PPA = {}
            for obj in objs.keys():
                self.PPA[obj] = data[2][obj]
        elif (data_set_type == 'db'):
            self.Constraints = data[0]
            self.Cycle_count = None
            self.PPA = {}
            for obj in objs.keys():
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
        return self.PPA[obj]    

class Data_Set:
    def __init__(self, data, objs, scales, normalized_factors, data_set_type = 'txt'):
        val_list = {}
        self.best_value = {}
        self.best_pair = {}
        self.objs_direct = objs

        if data_set_type == 'txt':
            for i in range(len(data)):
                d_input_dic = data[i][0]
                d_input = [val for val in d_input_dic.values()]
                self.__dict__[tuple(d_input)] = Data_Sample(data[i], objs, data_set_type)
                self.scaled_factors = scales
                self.normalized_factors = normalized_factors
        elif data_set_type == 'db':
            for obj in objs.keys():
                val_list[obj] = []
            for i in data.keys():
                self.__dict__[i] = Data_Sample([i, data[i]], objs, data_set_type)
                self.scaled_factors = scales
                self.normalized_factors = normalized_factors
                for obj in objs.keys():
                    val_list[obj].append(data[i][obj])
            for obj in objs.keys():
                
                if objs[obj] == 'minimise':
                    self.best_value[obj] = min(val_list[obj])
                else:
                    self.best_value[obj] = max(val_list[obj])
                
                self.best_pair[obj] = [[i] for i in data.keys() if data[i][obj] == self.best_value[obj]][0]
    
    def __len__(self):
        return len(self.__dict__)
    
    def list_all_contraints(self):
        constraints = []
        for i in self.__dict__.keys():
            constraints.append(self.__dict__.get(i).Constraints)
        return constraints
    
    def find_ppa_result(self, constraints, objs, dtype):
        """find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        # TODO : prepare for multi objectives
        for obj in objs.keys():
            denormalized_constraints = recover_generated_data(constraints, self.normalized_factors, self.scaled_factors)
            num_restart = denormalized_constraints.shape[0]
            result = torch.zeros(num_restart, dtype=dtype)
            for i in range(0, num_restart):
                rounded_constraints = denormalized_constraints[i].round()
                constraint = rounded_constraints.tolist()
                try:
                    result[i] = self.__dict__.get(tuple(constraint)).get_ppa(obj)
                except:
                    result[i] = 0
            if self.objs_direct[obj] == 'minimise':
                result = -result
        return result


def read_data_from_txt(file_name, objs, scales, normalized_factors):
    with open(file_name, 'r') as f:
        content = f.read()
        raw_data = ast.literal_eval(content)
        print("objs", objs) 
        data_set = Data_Set(raw_data, objs, scales, normalized_factors, 'txt')
    return data_set

def read_data_from_db(db_name, objs, scales, normalized_factors):
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
    data_set = Data_Set(db, objs, scales, normalized_factors, 'db')
    return data_set
    



if __name__ == '__main__':
    read_data_from_db("../data/ppa_v2.db", ['lut'], [1, 1, 1], [1, 1, 1])

