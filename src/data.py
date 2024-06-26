import ast
import torch
import glob
import sys
import pickle
import os.path as osp
from utils import calculate_smooth_condition, recover_single_input_data, read_utilization, find_the_anticipated_fastest_time_period
from botorch.utils.transforms import normalize

def read_data_from_db(db_name):
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
    return db


class Input_Info:
    """Class to store all the related input information"""
    def __init__(self, input_dim, input_scales, input_normalized_factor, input_exp, input_offsets, input_names, input_constraints, input_categorical, self_constraints, conditional_constraints):
        self.input_dim = input_dim
        self.input_scales = input_scales
        self.input_normalized_factor = input_normalized_factor
        self.input_exp = input_exp
        self.input_offsets = input_offsets
        self.input_names = input_names
        self.constraints = input_constraints
        self.constants = None
        self.self_constraints = self_constraints
        self.conditional_constraints = conditional_constraints
        self.input_categorical = input_categorical

class Output_Info:
    """Class to store all the related output information"""
    def __init__(self, obj_to_optimise, output_constraints, optimisation_target):
        self.obj_to_optimise = obj_to_optimise
        self.output_constraints = output_constraints
        self.optimisation_target = optimisation_target
        self.obj_to_optimise_dim = len(obj_to_optimise)
        self.obj_to_evaluate_dim = self.obj_to_optimise_dim + len(output_constraints)
        self.obj_to_optimise_index = list(range(self.obj_to_optimise_dim))

class Data_Sample:
    """Individual Storage Element"""
    def __init__(self, data, objs, data_set_type):
        self.objective_vals = {}
        if (data_set_type == 'txt'):
            for obj in objs:
                if obj == 'ncycle_2':
                    index = obj.split('_')[-1]
                    self.objective_vals[obj] = int(list(data[1][int(index)].values())[0])
                else:
                    self.objective_vals[obj] = data[2][obj]
        elif (data_set_type == 'db'):
            self.Constraints = data[0]
            self.Cycle_count = None
            for obj in objs:
                self.objective_vals[obj] = data[1][obj]
    def get_objectives(self, obj):
        return self.objective_vals.get(obj, None)

class Data_Set:
    """This class is used for DSE where the dataset is provided"""
    def __init__(self, input_info, output_info, data_set_type = 'txt', tensor_type = torch.float64, tensor_device = torch.device('cpu')):
        val_list = {}
        self.best_value = {}
        self.best_pair = {}
        self.worst_value = {}
        # to recover the output data
        self.objs_to_optimise_dim = output_info.obj_to_optimise_dim
        self.objs_to_evaluate = list(output_info.obj_to_optimise.keys()) + list(output_info.output_constraints.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        self.output_normalised_factors = {}
        self.objs_direct = {}    
        # to recover the input data
        self.input_normalized_factors = torch.tensor(input_info.input_normalized_factor, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(input_info.input_scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(input_info.input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_exp = torch.tensor(input_info.input_exp, dtype=tensor_type, device=tensor_device)
        self.input_constants = input_info.constants
        self.input_categorical = input_info.input_categorical
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.normaliser_bounds = torch.empty((2, self.objs_to_evaluate_dim), dtype=tensor_type, device=tensor_device)
        
        if data_set_type == 'txt':
            file_name = '../specification/Simple_Dataset/ppa.txt'
            with open(file_name, 'r') as f:
                content = f.read()
                raw_data = ast.literal_eval(content)
            for i in range(len(raw_data)):
                d_input_dic = raw_data[i][0]
                d_input = [val for val in d_input_dic.values()]
                self.__dict__[tuple(d_input)] = Data_Sample(raw_data[i], self.objs_to_evaluate, data_set_type)
        elif data_set_type == 'db':
            for obj in self.objs_to_evaluate:
                val_list[obj] = []
            raw_data = read_data_from_db('../specification/Simple_Dataset/ppa_v2.db')
            for i in raw_data.keys():
                self.__dict__[i] = Data_Sample([i, raw_data[i]], self.objs_to_evaluate, data_set_type)
                for obj in self.objs_to_evaluate:
                    val_list[obj].append(raw_data[i][obj])
            

            # Iterate over each item in output_objective
        obj_index = 0
        for obj, values in output_info.obj_to_optimise.items():
            # Extract the obj_direction from the values list
            obj_direction = values[0]
            self.objs_direct[obj] = obj_direction
            if obj_direction == 'minimise':
                self.best_value[obj] = values[1]
                self.worst_value[obj] = values[2]
                self.normaliser_bounds[0][obj_index] = -1 * values[1]
                self.normaliser_bounds[1][obj_index] = -1 * values[2]
            else:
                self.best_value[obj] = values[2]
                self.worst_value[obj] = values[1]
                self.normaliser_bounds[0][obj_index] = values[1]
                self.normaliser_bounds[1][obj_index] = values[2]
            # for recording the best pair
            # self.normaliser_bounds[0][obj_index] = min()
            # self.normaliser_bounds[1][obj_index] = max(val_list[obj])
            # self.best_pair[obj] = [[i] for i in raw_data.keys() if raw_data[i][obj] == self.best_value[obj]][0]
            obj_index += 1
        self.output_constraints_to_check = []
        for obj in output_info.output_constraints:
            self.best_value[obj] = output_info.output_constraints[obj][1]
            self.worst_value[obj] = 0.0
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound,obj) for bound in output_info.output_constraints[obj]])
            self.normaliser_bounds[0][obj_index] = output_info.output_constraints[obj][0]
            self.normaliser_bounds[1][obj_index] = output_info.output_constraints[obj][1]

    def normalise_output_data_tensor(self, input_tensor):
        """This function is used to normalise the output data in tensor format"""
        sign_tensor = torch.sign(input_tensor)
        normalised_result = normalize(input_tensor, self.normaliser_bounds)
        return normalised_result * sign_tensor
    
    def normalise_single_output_data(self, input_data, obj):
        """This function is used to normalise the output data in single data format"""
        result = (input_data - min(self.best_value[obj], self.worst_value[obj])) / abs(self.best_value[obj] - self.worst_value[obj])
        return result
    
    def format_and_add_const_to_data(self, input_data):
        """This function is used to add constant input to the input data to make it able to find the ppa result"""
        for index in self.input_constants.keys():
            input_data.insert(index, self.input_constants[index])
        return tuple(input_data)
    
    def find_evaluation_results(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets, self.input_categorical)
            sample_input = self.format_and_add_const_to_data(input)
            for obj_index in range(self.objs_to_evaluate_dim):
                obj = self.objs_to_evaluate[obj_index]
                sample_objective = self.__dict__.get(sample_input, None)
                if sample_objective is None:
                    return False, results   
                results[i][obj_index] = sample_objective.get_objectives(obj)
                if self.objs_direct.get(obj, None) == 'minimise':
                    results[i][obj_index] = -1 * results[i][obj_index]
                obj_index += 1
        return True, results

    def find_single_ppa_result_for_unnormalised_sample(self, sample_input):
        """This function is used to find the ppa result for a single input, only used in result recording"""
        formatted_input = self.format_and_add_const_to_data(sample_input)
        result = []
        for  obj in self.objs_to_evaluate:
            result.append(self.__dict__.get(tuple(formatted_input)).get_objectives(obj))
        return result

    def check_obj_constraints(self, X):
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
        
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.output_constraints_to_check = []
        for obj in output_obj_constraint:
            self.output_constraints_to_check.append([bound / self.output_normalised_factors[obj] for bound in output_obj_constraint[obj]])
        self.build_new_dataset = create_data_set(input_names, self.objs_to_evaluate, 'NutShell')

    def find_evaluation_results(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            # num_restart needs to be fixed to 1
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets)
            sample_input = self.format_and_add_const_to_data(input)
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
    def __init__(self, input_info, output_info, param_tuner, optimisation_name, build_dataset = True, tensor_type=torch.float64, tensor_device=torch.device('cpu'), benchmark_to_eval_to_build_dataset = ['cmark', 'dhry', 'cmark_iccm', 'cmark_dccm']):
        self.utilisation_path = '../object_functions/Syn_Report/EL2_utilization_synth.rpt'
        self.time_report = '../object_functions/Syn_Report/EL2_time_summary.rpt'
        self.param_tuner = param_tuner
        self.frequency_constraint = 50000000             #50MHz
        # to recover the Output data
        self.objs_to_optimise_dim = output_info.obj_to_optimise_dim
        self.objs_to_evaluate = list(output_info.obj_to_optimise.keys()) + list(output_info.output_constraints.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        # this is to check what type of performance objectives are needed to be stored
        self.performance_objs_benchmarks = []
        # assume all the output is percentage
        self.worst_value = {}
        self.best_value = {}
        self.objs_direct = {}
        self.normaliser_bounds = torch.empty((2, self.objs_to_evaluate_dim), dtype=tensor_type, device=tensor_device)

        # Note: this is to build the dataset to store the objective vals for a parameter set, in order to facilitate the future DSE
        self.build_dataset = build_dataset
        self.benchmark_to_eval_to_build_dataset = benchmark_to_eval_to_build_dataset

        # Iterate over each item in output_objective
        obj_index = 0   
        for obj_name, values in output_info.obj_to_optimise.items():
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
        for obj_name in list(output_info.output_constraints.keys()):
            self.best_value[obj_name] = output_info.output_constraints[obj_name][1]
            self.worst_value[obj_name] = output_info.output_constraints[obj_name][0]
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound, obj_name) for bound in output_info.output_constraints[obj_name]])
            self.normaliser_bounds[0][obj_index] = output_info.output_constraints[obj_name][0]
            self.normaliser_bounds[1][obj_index] = output_info.output_constraints[obj_name][1]
        
        # to recover the Input data
        self.input_normalized_factors = torch.tensor(input_info.input_normalized_factor, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(input_info.input_scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(input_info.input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_exp = torch.tensor(input_info.input_exp, dtype=tensor_type, device=tensor_device)
        self.input_constants = input_info.constants
        self.input_categorical = input_info.input_categorical

        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.build_new_dataset = create_data_set(input_info.input_names, self.performance_objs_benchmarks, self.benchmark_to_eval_to_build_dataset, optimisation_name)
    
    def find_evaluation_results(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            # num_restart needs to be fixed to 1
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets, self.input_categorical, self.input_exp)
            sample_input = self.format_and_add_const_to_data(input)
            # Modify the paramter settings
            utilisation_percentage = self.build_new_dataset.find_corresponding_data(sample_input)
            if utilisation_percentage is None:
                print(f"{sample_input} not found in the dataset, Start to Generate ")
                simulation_results = []
                if self.build_dataset:
                    # Add all the benchmark performance in one round to facilitate the future DSE
                    simulation_results_for_all_benchmarks = []
                    for benmark in self.benchmark_to_eval_to_build_dataset:
                        valid_simulation, _, mcycle = self.param_tuner.tune_and_run_performance_simulation(sample_input, benmark)
                        if valid_simulation == False:
                            simulation_results_for_all_benchmarks.append('failed')
                        else:
                            simulation_results_for_all_benchmarks.append(mcycle)
                    simulation_results.append(simulation_results_for_all_benchmarks[self.performance_objs_benchmarks.index(self.performance_objs_benchmarks[0])])
                else:
                    for benchmark in self.performance_objs_benchmarks:
                        valid_simulation, _, mcycle = self.param_tuner.tune_and_run_performance_simulation(sample_input, benchmark)
                        if valid_simulation == False:
                            return False, results
                        simulation_results.append(mcycle)
                
                # Run the Synthesis on Vivado
                self.param_tuner.run_synthesis()
                # Store the utilisation result
                self.param_tuner.store_synthesis_report()
                # Read the utilisation percentage
                utilisation_percentage = read_utilization(self.utilisation_path, self.objs_to_evaluate[len(self.performance_objs_benchmarks) : ])
                # Read the Time Report
                time_period = find_the_anticipated_fastest_time_period(self.time_report, self.frequency_constraint)
                objective_results = [i * time_period * 1e-3 for i in simulation_results]  # Here we assume the time unit is ms
                objective_results_for_all_benchmarks = [i * time_period * 1e-3 for i in simulation_results_for_all_benchmarks]  # Here we assume the time unit is ms
                objective_results.append(utilisation_percentage)  
                print("objective_results ", objective_results)
                print("utilisation_percentage ", utilisation_percentage)
                
                if self.build_dataset:
                    self.build_new_dataset.record_simulation_results(sample_input, objective_results_for_all_benchmarks)
                    self.build_new_dataset.record_synthesis_results(utilisation_percentage, time_period)

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

    def find_all_possible_designs(self):
        """This function is used to find all the possible designs"""
        print("normalised_Factors", self.input_normalized_factors)
        ranges = [torch.linspace(0, 1, steps=int(factor) * 2 + 1, device=self.tensor_device) for factor in self.input_normalized_factors]
        # Generate all combinations using torch.meshgrid with the 'indexing' argument for future compatibility
        grids = torch.meshgrid(*ranges, indexing='ij')
        # Stack the grids to form a tensor of shape (5*3*2*3, 4)
        combinations = torch.stack(grids, dim=-1).reshape(-1, self.input_normalized_factors.size(0))
        # Use .to() method to ensure the tensor is on the right device and has the right dtype
        combinations = combinations.to(device=self.tensor_device, dtype=self.tensor_type)
        return combinations

    def brute_design_space_exploration(self):
        combinations = self.find_all_possible_designs()
        for index in range(combinations.shape[0]):
            print("combinations[index]: ", combinations[index])
            valid, result = self.find_evaluation_results(combinations[index].unsqueeze(0))
            print("valid: ", valid, "result: ", result)


class Rocket_Chip_data(EL2_Data):
    def __init__(self, input_info, output_info, param_tuner, optimisation_name, build_dataset = True, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        benchmark_to_eval_to_build_dataset = ['dhrystone', 'qsort', 'mt-matmul', 'median']
        super().__init__(input_info, output_info, param_tuner, optimisation_name, build_dataset, tensor_type, tensor_device, benchmark_to_eval_to_build_dataset)
        self.utilisation_path = '../object_functions/Syn_Report/rocket_utilization_synth.rpt'
        self.time_report = '../object_functions/Syn_Report/rocket_time_summary.rpt'


class create_data_set:
    """This class is implemented to accelerate the redundant synthesis and simulation process"""
    def __init__(self, input_name, object_to_optimise, all_benchmarks_to_eval, optimisation_set_name):
        self.input_name = input_name
        self.input_dim = len(input_name)
        self.all_benchmarks_to_eval = list(all_benchmarks_to_eval)
        # index to evaluate
        self.object_to_optimise = self.all_benchmarks_to_eval.index(object_to_optimise[0])
        self.names = input_name + all_benchmarks_to_eval
        self.file_name = f'../object_functions/Dataset/{optimisation_set_name}.txt'
        match_file = True
        if osp.exists(self.file_name):
            with open(self.file_name, 'r') as file:
                line = file.readline()
                first_line = line.split(',')
                trimmed_array = [item.lstrip() for item in first_line]
                for index in range (self.input_dim + len(all_benchmarks_to_eval) - 1):
                    if trimmed_array[index] != self.names[index]:    
                        print("trimmed_array[index] ", trimmed_array[index])
                        print("self.names[index] ", self.names[index])
                        match_file = False
                        # raise ValueError("The input and objective names do not match the dataset")
        else:
            match_file = False
        if not match_file:
            with open(self.file_name, 'w') as file:
                for index in range(self.input_dim + len(all_benchmarks_to_eval)):
                    if index == 0:
                        file.write(f"{self.names[index]}")
                    else:
                        file.write(f", {self.names[index]}")
                file.write("\n")
    def record_simulation_results(self, input_data, objective_data_set):
        with open(self.file_name, 'a') as file:
            for index in range(self.input_dim):
                if index == 0:
                    file.write(f"{input_data[index]}")
                else:
                    file.write(f", {input_data[index]}")
            
            else:
                for objective_data in objective_data_set:
                    file.write(f", {objective_data}")
    
    def record_synthesis_results(self, utilisation_data, time_period):
        with open(self.file_name, 'a') as file:
            file.write(f", {utilisation_data}")
            file.write(f", {time_period}")
            file.write("\n")

    def find_corresponding_data(self, input_data):
        with open(self.file_name, 'r') as file:
            lines = file.readlines()
            for line in lines[1:]:
                line = line.split(',')
                sample_data = tuple([float(i) for i in line[0:self.input_dim]])
                if sample_data == input_data:
                    if line[self.input_dim] != ' failed\n':
                        result = []
                        result.append(float(line[self.input_dim + self.object_to_optimise]))
                        result.append(float(line[-2]))
                        return result
                    else:
                        return 'failed'
        return None



## Functions



# if __name__ == '__main__':
    # input_names = ['LUT', 'FF']
    # all_benchmarks_to_evals = ['Latency', 'Throughput']
    # dataset = create_data_set(input_names, all_benchmarks_to_evals)
    # dataset.record_data([3.0, 2.0], [3.234, 4.23])
    # print(dataset.find_corresponding_data((3.0, 2.0)))
    # read_data_from_txt('../object_functions/Dataset/NutShell.txt', ['Latency', 'Throughput'], [1, 1], [1, 1])