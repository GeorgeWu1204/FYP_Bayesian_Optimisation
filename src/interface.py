from format_constraints import Input_Constraints
from parameter_tuning import NutShell_parameter_tuning, EL2_parameter_tuning
from data import Input_Info, Output_Info
import math

def fill_constraints(self_constraints, coupled_constraints, device):
    """this function is used to fill the constraints in the interface"""
    # self_constraints: {var_name: [lower_bound, upper_bound, scale, exp]}
    # coupled_constraints: [{var_name: [lower_bound, upper_bound], var_name: [lower_bound, upper_bound]},... ]
    input_dim = len(self_constraints)
    input_scales = [1] * input_dim
    input_normalized_factor = [1] * input_dim
    input_offset = [0] * input_dim
    input_exp = [1] * input_dim
    for i, var_obj in enumerate(self_constraints.keys()):
        if self_constraints[var_obj][3] > 1:
            #has exps
            input_offset[i] = int(math.log(self_constraints[var_obj][0], self_constraints[var_obj][3]))
            #force the scales to be 1 if the exps is used
            self_constraints[var_obj][2] = 1
            input_normalized_factor[i] = int(math.log(self_constraints[var_obj][1], self_constraints[var_obj][3])) - input_offset[i]
            input_exp[i] = self_constraints[var_obj][3]
        else:
            input_scales[i] = int(self_constraints[var_obj][2])
            input_normalized_factor[i] = int((self_constraints[var_obj][1] - self_constraints[var_obj][0])/ input_scales[i])
            input_offset[i] = int(self_constraints[var_obj][0])
    input_names = list(self_constraints.keys())
    constraint = Input_Constraints(input_dim, device)
    constraint.update_scale_normalize_exp_factor(input_scales, input_normalized_factor, input_exp)

    for index, constraints in enumerate(self_constraints.values()):
        constraint.update_self_constraints(index, list(constraints))
    
    if len(coupled_constraints) != 0:
        format_coupled_constraint = []
        for or_constraint in range(len(coupled_constraints)):
            and_constraints = {}
            for and_constraint in coupled_constraints[or_constraint].keys():
                and_constraints[input_names.index(and_constraint)] = coupled_constraints[or_constraint][and_constraint]
            format_coupled_constraint.append(and_constraints)
        constraint.update_coupled_constraints(format_coupled_constraint)
    
    return Input_Info(input_dim, input_scales, input_normalized_factor, input_exp, input_offset, input_names, constraint, self_constraints, coupled_constraints) 

def parse_constraints(filename, device):
    """this function is used to parse the constraints from the file"""
    # Define dictionaries to store the parsed data
    self_constraints = {}
    input_constant = {}
    input_shift_amount = {}
    coupled_constraints = []
    output_objective = {}
    output_constraints = {}
    optimisation_target = None
    optimisation_name = None
    # Open and read the file
    with open(filename, 'r') as file:
        lines = file.readlines()

        # Define a flag to track the section type
        section = None
        for line in lines:
            line = line.strip()
            # Update the section based on the line content
            if line.startswith('#Name'):
                parts = line.split()
                optimisation_name = parts[1]
            elif line.startswith('#input self constraint'):
                section = 'self_constraint'
            elif line.startswith('#input coupled constraint'):
                section = 'coupled_constraint'
            elif line.startswith('#input constant'):
                section = 'input_constant'
            elif line.startswith('#output objective'):
                section = 'output_objective'
            elif line.startswith('#output constraint'):
                section = 'output_constraint'
            elif line.startswith('var:') and section:
                # Process the variable line based on the section
                if section == 'input_constant':
                    parts = line.split()
                    var_index = int(parts[5])
                    input_constant[var_index] = int(parts[3])
                else:
                    parts = line.split()
                    var_name = parts[1]
                    range_values = parts[3].strip('[]').split(',')
                    if section == 'self_constraint':
                        scale = int(parts[5])
                        exp = int(parts[7])
                        self_constraints[var_name] = [int(range_values[0]), int(range_values[1]), scale, exp]
                        input_shift_amount[var_name] = int(parts[9])
                    elif section == 'coupled_constraint':
                        coupled_parts = line.split('and')
                        coupled_data = {}
                        for part in coupled_parts:
                            var_parts = part.split()
                            var_name = var_parts[1]
                            range_values = var_parts[3].strip('[]').split(',')
                            coupled_data[var_name] = [int(range_values[0]), int(range_values[1])]
                        coupled_constraints.append(coupled_data)
            elif line.startswith('obj_name:') and section:
                # Process the objective line
                parts = line.split()
                for i in range(1, len(parts)):
                        if parts[i] == 'obj_direct:' or parts[i] == 'range:' or parts[i] == 'benchmark:':
                            obj_name_end_index = i
                            break
                obj_name = ' '.join(parts[1:obj_name_end_index])
                if section == 'output_objective':
                    if parts[obj_name_end_index] == 'benchmark:':
                        obj_name += '_' + parts[obj_name_end_index+1]
                        obj_direction = parts[obj_name_end_index+3]
                        range_values = parts[obj_name_end_index+5].strip('[]').split(',')
                        output_objective[obj_name] = [obj_direction, int(range_values[0]), int(range_values[1]), parts[obj_name_end_index+1]]
                    else:
                        obj_direction = parts[obj_name_end_index+1]
                        range_values = parts[obj_name_end_index+3].strip('[]').split(',')
                        output_objective[obj_name] = [obj_direction, int(range_values[0]), int(range_values[1]), 'NotBenchmark']
                elif section == 'output_constraint':
                    range_values = parts[obj_name_end_index+1].strip('[]').split(',')
                    output_constraints[obj_name] = [int(range_values[0]), int(range_values[1])]
            elif line.startswith('objective'):
                optimisation_target = line.split()[1]
            elif line.startswith('settings_path'):
                objective_function_setting_path = line.split()[1]
            elif line.startswith('vivado_project_path'):
                vivado_project_path = line.split()[1]
            elif line.startswith('generation_path'):
                generation_path = line.split()[1]
            elif line.startswith('board_settings'):
                board_settings = line.split()[1]
    if optimisation_target == 'NutShell':
        parameter_tuner = NutShell_parameter_tuning(tuple(self_constraints.keys()), tuple(input_shift_amount.values()), objective_function_setting_path, generation_path, vivado_project_path, board_settings)
    elif optimisation_target == 'EL2':
        parameter_tuner = EL2_parameter_tuning(tuple(self_constraints.keys()), tuple(input_shift_amount.values()), generation_path, vivado_project_path)
    else:
        parameter_tuner = None
    
    output_info = Output_Info(output_objective, output_constraints, optimisation_target)
    # Start to Fill in the constraints information
    input_info = fill_constraints(self_constraints, coupled_constraints, device)
    input_info.constants = input_constant
    return input_info, output_info, parameter_tuner, optimisation_name

if __name__ == '__main__':
    input_info, output_info, _ = parse_constraints('../specification/input_spec_optimisation_set_3.txt', )
    print(input_info.input_names)
    print(output_info.output_objective)