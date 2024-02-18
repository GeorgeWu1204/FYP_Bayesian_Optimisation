from format_constraints import Input_Constraints
from parameter_tuning import parameter_tuning
def fill_constraints(self_constraints, coupled_constraints, device):
    """this function is used to fill the constraints in the interface"""
    # self_constraints: {var_name: [lower_bound, upper_bound, scale]}
    # coupled_constraints: [{var_name: [lower_bound, upper_bound], var_name: [lower_bound, upper_bound]},... ]
    print(self_constraints)
    print(coupled_constraints)
    input_dim = len(self_constraints)
    input_scales = [1] * input_dim
    input_normalized_factor = [1] * input_dim
    input_offset = [0] * input_dim
    for i, var_obj in enumerate(self_constraints.keys()):
        input_scales[i] = int(self_constraints[var_obj][2])
        input_normalized_factor[i] = int((self_constraints[var_obj][1] - self_constraints[var_obj][0])/ input_scales[i])
        input_offset[i] = int(self_constraints[var_obj][0] / input_scales[i])
    input_names = list(self_constraints.keys())
    constraint = Input_Constraints(input_dim, device)
    constraint.update_scale_and_normalize_factor(input_scales, input_normalized_factor)

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
    return (input_dim, input_scales, input_normalized_factor, input_offset, input_names), constraint

def parse_constraints(filename):
    """this function is used to parse the constraints from the file"""
    # Define dictionaries to store the parsed data
    self_constraints = {}
    input_constant = {}
    input_shift_amount = {}
    coupled_constraints = []
    output_objective = {}
    output_constraints = {}
    objective_function_category = None
    # Open and read the file
    with open(filename, 'r') as file:
        lines = file.readlines()

        # Define a flag to track the section type
        section = None
        for line in lines:
            line = line.strip()
            # Update the section based on the line content
            if line.startswith('#input self constraint'):
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
                        self_constraints[var_name] = [int(range_values[0]), int(range_values[1]), scale]
                        input_shift_amount[var_name] = int(parts[7])
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
                        if parts[i] == 'obj_direct:' or parts[i] == 'range:':
                            obj_name_end_index = i
                            break
                obj_name = ' '.join(parts[1:obj_name_end_index])
                if section == 'output_objective':
                    obj_direction = parts[obj_name_end_index + 1]
                    output_objective[obj_name] = obj_direction
                elif section == 'output_constraint':
                    range_values = parts[obj_name_end_index+1].strip('[]').split(',')
                    output_constraints[obj_name] = [int(range_values[0]), int(range_values[1])]
            elif line.startswith('objective'):
                objective_function_category = line.split()[1]
            elif line.startswith('settings_path'):
                objective_function_setting_path = line.split()[1]
            elif line.startswith('vivado_project_path'):
                vivado_project_path = line.split()[1]
            elif line.startswith('generation_path'):
                generation_path = line.split()[1]
            elif line.startswith('board_settings'):
                board_settings = line.split()[1]
    if objective_function_category == 'real-time':
        parameter_tuning_obj = parameter_tuning(tuple(self_constraints.keys()), tuple(input_shift_amount.values()), objective_function_setting_path, vivado_project_path, generation_path, board_settings)
    else:
        parameter_tuning_obj = None
    return self_constraints, coupled_constraints, input_constant, output_objective, output_constraints, objective_function_category, parameter_tuning_obj

if __name__ == '__main__':
    self_constraints, coupled_constraints, input_constant, output_objective, output_constraints, objective_function_category, parameter_tuning_obj = parse_constraints('../data/input_spec2.txt')
    print(self_constraints)
    print(coupled_constraints)
    print(output_objective)
    print(output_constraints)
    # (input_dim, input_scales, input_normalized_factor, input_offset, input_names), constraint = fill_constraints(self_constraints, coupled_constraints)
    # print(input_dim)
    # print(input_scales)
    # print(input_normalized_factor)
    # print(input_names)
    # print(constraint)