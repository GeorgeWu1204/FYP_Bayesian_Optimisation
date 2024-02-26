import ast
import torch
import glob
import sys
import pickle
import os.path as osp
from utils import calculate_condition, calculate_smooth_condition, recover_single_input_data, read_utilization
from botorch.utils.transforms import normalize

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
    def get_ppa(self, obj):
        return self.PPA.get(obj, None)   

class Data_Set:
    """This class is used for DSE where the dataset is provided"""
    def __init__(self, data, objs, input_scales, input_data_normalized_factors, input_offsets, input_constants, output_obj_constraint, data_set_type = 'txt', tensor_type = torch.float64, tensor_device = torch.device('cpu')):
        val_list = {}
        self.best_value = {}
        self.best_pair = {}
        self.worst_value = {}
        # to recover the output data
        self.objs_to_optimise_dim = len(objs)
        self.objs_to_evaluate = list(objs.keys()) + list(output_obj_constraint.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        self.output_normalised_factors = {}
        self.objs_direct = {}    
        # to recover the input data
        self.input_normalized_factors = torch.tensor(input_data_normalized_factors, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(input_scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_constants = input_constants
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.normaliser_bounds = torch.empty((2, len(objs)), dtype=tensor_type, device=tensor_device)
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

            # Iterate over each item in output_objective
            obj_index = 0
            for obj, values in objs.items():
                # Extract the obj_direction from the values list
                obj_direction = values[0]
                self.objs_direct[obj] = obj_direction
                if obj_direction == 'minimise':
                    self.best_value[obj] = values[1]
                    self.worst_value[obj] = values[2]
                else:
                    self.best_value[obj] = values[2]
                    self.worst_value[obj] = values[1]
                # for recording the best pair
                self.normaliser_bounds[0][obj_index] = min(val_list[obj])
                self.normaliser_bounds[1][obj_index] = max(val_list[obj])
                self.best_pair[obj] = [[i] for i in data.keys() if data[i][obj] == self.best_value[obj]][0]
                obj_index += 1
        self.output_constraints_to_check = []
        for obj in output_obj_constraint:
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound,obj) for bound in output_obj_constraint[obj]])
            self.best_value[obj] = output_obj_constraint[obj][1]
            self.worst_value[obj] = 0.0
        print("self.constrains_to_check: ", self.output_constraints_to_check)

    def normalise_output_data_tensor(self, input_tensor):
        """This function is used to normalise the output data in tensor format"""
        sign_tensor = torch.sign(input_tensor)
        normalised_result = normalize(input_tensor, self.normaliser_bounds)
        return normalised_result * sign_tensor
    
    def normalise_single_output_data(self, input_data, obj):
        """This function is used to normalise the output data in single data format"""
        result = (input_data - min(self.best_value[obj], self.worst_value[obj])) / abs(self.best_value[obj] - self.worst_value[obj])
        return result
    
    def format_input_data(self, input_data):
        """This function is used to add constant input to the input data to make it able to find the ppa result"""
        for index in self.input_constants.keys():
            input_data.insert(index, self.input_constants[index])
        return tuple(input_data)
    
    def find_ppa_result(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets)
            sample_input = self.format_input_data(input)
            for obj_index in range(self.objs_to_evaluate_dim):
                obj = self.objs_to_evaluate[obj_index]
                results[i][obj_index] = self.__dict__.get(sample_input).get_ppa(obj)
                if self.objs_direct.get(obj, None) == 'minimise':
                    results[i][obj_index] = -1 * results[i][obj_index]
                obj_index += 1
        return results

    def find_single_ppa_result_for_brute_force(self, sample_input):
        """This function is used to find the ppa result for a single input, only used in result recording"""
        formatted_input = self.format_input_data(sample_input)
        result = []
        for  obj in self.objs_to_evaluate:
            result.append(self.__dict__.get(tuple(formatted_input)).get_ppa(obj))
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
        data_set = Data_Set(raw_data, objs, scales, input_data_normalized_factors, 'txt')
    return data_set

def read_data_from_db(db_name, objs, output_obj_constraint, scales, input_data_normalized_factors, input_offsets, input_constants, type, device):
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
    data_set = Data_Set(db, objs, scales, input_data_normalized_factors, input_offsets, input_constants, output_obj_constraint, 'db', type, device)
    return data_set
    

class NutShell_Data(Data_Set):
    def __init__(self, input_names, objs, scales, input_data_normalized_factors, input_offsets, input_constants, output_obj_constraint, param_tuner, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        
        self.utilisation_path = '../object_functions/Syn_Report/NutShell_utilization_synth.rpt'
        self.param_tuner = param_tuner
        # to recover the output data
        self.objs_to_optimise_dim = len(objs)
        self.objs_to_evaluate = list(objs.keys()) + list(output_obj_constraint.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        # assume all the output is percentage
        self.output_normalised_factors = {}
        self.worst_value = {}
        self.best_value = {}
        # TODO: worst value selection 
        self.objs_direct = {}
        # Iterate over each item in output_objective
        for obj_name, values in objs.items():
            # Extract the obj_direction from the values list
            obj_direction = values[0]
            self.objs_direct[obj_name] = obj_direction
            if obj_direction == 'minimise':
                self.best_value[obj_name] = values[1]
                self.worst_value[obj_name] = values[2]
            else:
                self.best_value[obj_name] = values[2]
                self.worst_value[obj_name] = values[1]
        # TODO, since for some of the conditions that are very small, the boundary calculation methods does not work well, hence normalising to the largest value of the condition.
        for obj in list(output_obj_constraint.keys()):
            self.output_normalised_factors[obj] = output_obj_constraint[obj][1]
            self.best_value[obj] = output_obj_constraint[obj][1]
            self.worst_value[obj] = 0.0
        
        # to recover the input data
        self.input_normalized_factors = torch.tensor(input_data_normalized_factors, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_constants = input_constants
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.output_constraints_to_check = []
        for obj in output_obj_constraint:
            self.output_constraints_to_check.append([bound / self.output_normalised_factors[obj] for bound in output_obj_constraint[obj]])
        self.build_new_dataset = create_data_set(input_names, self.objs_to_evaluate, 'NutShell')

    def find_ppa_result(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            # num_restart needs to be fixed to 1
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets)
            sample_input = self.format_input_data(input)
            # Modify the paramter settings
            utilisation_percentage = self.build_new_dataset.find_corresponding_data(sample_input)
            if utilisation_percentage is None:
                print("Not found in the dataset, Start to Generate ")
                self.param_tuner.tune_parameter(sample_input)
                # Regenerate the customised processor
                pass_generation = self.param_tuner.regenerate_design_locally()
                # Check if successfully generated the processor
                if not osp.exists(self.param_tuner.generation_path + 'build') or not pass_generation:
                    print("Failed to generate the processor")
                    self.build_new_dataset.record_data(sample_input, 'failed')
                    return False, results
                # Run the Synthesis on Vivado
                print("Start to run the synthesis")
                self.param_tuner.run_synthesis()
                # Store the utilisation result
                self.param_tuner.store_synthesis_report()
                # Read the utilisation percentage
                utilisation_percentage = read_utilization(self.utilisation_path, self.objs_to_evaluate)
                self.build_new_dataset.record_data(sample_input, utilisation_percentage)
                print("utilisation_percentage ", utilisation_percentage)
                for obj_index in range(self.objs_to_evaluate_dim):
                    obj = self.objs_to_evaluate[obj_index]
                    results[i][obj_index] = utilisation_percentage[obj_index]
                    if self.objs_direct.get(obj, None) == 'minimise':
                        results[i][obj_index] = -1 * results[i][obj_index]
                    obj_index += 1
                return True, results
            else:
                if utilisation_percentage == 'failed':
                    return False, results
                else:
                    for obj_index in range(self.objs_to_evaluate_dim):
                        obj = self.objs_to_evaluate[obj_index]
                        results[i][obj_index] = utilisation_percentage[obj_index]
                        if self.objs_direct.get(obj, None) == 'minimise':
                            results[i][obj_index] = -1 * results[i][obj_index]
                        obj_index += 1
            return True, results



class EL2_Data(Data_Set):
    def __init__(self, input_names, objs, scales, input_data_normalized_factors, input_offsets, input_constants, input_exp, output_obj_constraint, param_tuner, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
    
        self.utilisation_path = '../object_functions/Syn_Report/EL2_utilization_synth.rpt'
        self.param_tuner = param_tuner

        # to recover the output data
        self.objs_to_optimise_dim = len(objs)
        self.objs_to_evaluate = list(objs.keys()) + list(output_obj_constraint.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        # this is to check what type of performance objectives are needed to be stored
        self.performance_objs_benchmarks = []
        # assume all the output is percentage
        self.worst_value = {}
        self.best_value = {}
        self.objs_direct = {}
        self.normaliser_bounds = torch.empty((2, self.objs_to_evaluate_dim), dtype=tensor_type, device=tensor_device)

        # Iterate over each item in output_objective
        obj_index = 0   
        for obj_name, values in objs.items():
            # Extract the obj_direction from the values list
            obj_direction = values[0]
            self.objs_direct[obj_name] = obj_direction
            if obj_direction == 'minimise':
                self.best_value[obj_name] = values[1]
                self.worst_value[obj_name] = values[2]
                self.normaliser_bounds[0][obj_index] = -1 * values[1]
                self.normaliser_bounds[1][obj_index] = -1 * values[2]
            else:
                self.best_value[obj_name] = values[2]
                self.worst_value[obj_name] = values[1]
                self.normaliser_bounds[0][obj_index] = values[1]
                self.normaliser_bounds[1][obj_index] = values[2]

            if values[3] != 'NotBenchmark':
                self.performance_objs_benchmarks.append(values[3])
            obj_index += 1
        
        # TODO, since for some of the conditions that are very small, the boundary calculation methods does not work well, hence normalising to the largest value of the condition.
        self.output_constraints_to_check = []
        for obj_name in list(output_obj_constraint.keys()):
            self.best_value[obj_name] = output_obj_constraint[obj_name][1]
            self.worst_value[obj_name] = output_obj_constraint[obj_name][0]
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound, obj_name) for bound in output_obj_constraint[obj_name]])
            
            self.normaliser_bounds[0][obj_index] = output_obj_constraint[obj_name][0]
            self.normaliser_bounds[1][obj_index] = output_obj_constraint[obj_name][1]
        # to recover the input data
        self.input_normalized_factors = torch.tensor(input_data_normalized_factors, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_exp = torch.tensor(input_exp, dtype=tensor_type, device=tensor_device)
        self.input_constants = input_constants

        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.build_new_dataset = create_data_set(input_names, self.objs_to_evaluate, 'EL2')

    def find_ppa_result(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            # num_restart needs to be fixed to 1
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets, self.input_exp)
            sample_input = self.format_input_data(input)
            # Modify the paramter settings
            utilisation_percentage = self.build_new_dataset.find_corresponding_data(sample_input)
            if utilisation_percentage is None:
                print("Not found in the dataset, Start to Generate ")
                pass_generation = self.param_tuner.tune_parameter(sample_input)
                # Check if successfully generated the processor
                if not pass_generation:
                    print("Failed to generate the processor")
                    self.build_new_dataset.record_data(sample_input, 'failed')
                    return False, results
                objective_results = []
                # print("Start to run the performance simulation for ", type(self.performance_objs_benchmarks))
                # Run the Performance Simulation (Recording mcycle only)
                for benchmark in self.performance_objs_benchmarks:
                    valid_simulation, _, mcycle = self.param_tuner.run_performance_simulation(benchmark)
                    if valid_simulation == False:
                        self.build_new_dataset.record_data(sample_input, 'failed')
                        return False, results
                    objective_results.append(mcycle)
                # Run the Synthesis on Vivado
                self.param_tuner.run_synthesis()
                # Store the utilisation result
                self.param_tuner.store_synthesis_report()
                # Read the utilisation percentage
                utilisation_percentage = read_utilization(self.utilisation_path, self.objs_to_evaluate[len(self.performance_objs_benchmarks) : ])
                objective_results += utilisation_percentage 
                self.build_new_dataset.record_data(sample_input, objective_results)
                for obj_index in range(self.objs_to_evaluate_dim):
                    obj = self.objs_to_evaluate[obj_index]
                    results[i][obj_index] = objective_results[obj_index]
                    if self.objs_direct.get(obj, None) == 'minimise':
                        results[i][obj_index] = -1 * results[i][obj_index]
                    obj_index += 1
                return True, results
            else:
                if utilisation_percentage == 'failed':
                    return False, results
                else:
                    for obj_index in range(self.objs_to_evaluate_dim):
                        obj = self.objs_to_evaluate[obj_index]
                        results[i][obj_index] = utilisation_percentage[obj_index]
                        if self.objs_direct.get(obj, None) == 'minimise':
                            results[i][obj_index] = -1 * results[i][obj_index]
                        obj_index += 1
            return True, results

        

class create_data_set:
    """This class is implemented to accelerate the redundant synthesis and simulation process"""
    def __init__(self, input_name, objective_name, file_name):
        self.input_name = input_name
        self.input_dim = len(input_name)
        self.objective_name = list(objective_name)
        self.names = input_name + objective_name
        self.file_name = '../object_functions/Dataset/' + file_name + '_dataset_record.txt'
        match_file = True
        if osp.exists(self.file_name):
            with open(self.file_name, 'r') as file:
                line = file.readline()
                first_line = line.split(',')
                trimmed_array = [item.lstrip() for item in first_line]
                #TODO: make it better
                for index in range (self.input_dim + len(objective_name) - 1):
                    if trimmed_array[index] != self.names[index]:    
                        print("trimmed_array[index] ", trimmed_array[index])
                        print("self.names[index] ", self.names[index])
                        match_file = False
                        raise ValueError("The input and objective names do not match the dataset")
        else:
            match_file = False
        if not match_file:
            with open(self.file_name, 'w') as file:
                for index in range(self.input_dim + len(objective_name)):
                    if index == 0:
                        file.write(f"{self.names[index]}")
                    else:
                        file.write(f", {self.names[index]}")
                file.write("\n")
    def record_data(self, input_data, objective_data):
        with open(self.file_name, 'a') as file:
            for index in range(self.input_dim):
                if index == 0:
                    file.write(f"{input_data[index]}")
                else:
                    file.write(f", {input_data[index]}")
            if objective_data == 'failed':
                file.write(", failed\n")
            else:
                for data in objective_data:
                    file.write(f", {data}")
                file.write("\n")    

    def find_corresponding_data(self, input_data):
        with open(self.file_name, 'r') as file:
            lines = file.readlines()
            for line in lines[1:]:
                line = line.split(',')
                sample_data = tuple([float(i) for i in line[0:self.input_dim]])
                if sample_data == input_data:
                    if line[self.input_dim] != ' failed\n':
                        result = [float(i) for i in line[self.input_dim:] ]
                        return result
                    else:
                        return 'failed'
        return None



if __name__ == '__main__':
    input_names = ['LUT', 'FF']
    objective_names = ['Latency', 'Throughput']
    dataset = create_data_set(input_names, objective_names)
    dataset.record_data([3.0, 2.0], [3.234, 4.23])
    print(dataset.find_corresponding_data((3.0, 2.0)))