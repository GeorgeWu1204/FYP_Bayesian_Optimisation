from format_constraints import Input_Constraints
def fill_constraints(self_constraints, coupled_constraints):
    """this function is used to fill the constraints in the interface"""
    # self_constraints: {var_name: [lower_bound, upper_bound, scale]}
    # coupled_constraints: [{var_name: [lower_bound, upper_bound], var_name: [lower_bound, upper_bound]},... ]
    input_dim = len(self_constraints)
    input_scales = [1] * input_dim
    input_normalized_factor = [1] * input_dim
    for i, var_obj in enumerate(self_constraints.keys()):
        input_scales[i] = int(self_constraints[var_obj][2])
        input_normalized_factor[i] = int(self_constraints[var_obj][1] / input_scales[i])
    input_names = list(self_constraints.keys())
    constraint = Input_Constraints(input_dim)
    constraint.update_scale(input_scales)
    constraint.update_normalize_factor(input_normalized_factor)
    for i in range(input_dim):
        constraint.update_self_constraints(i, self_constraints[input_names[i]][:2])
    if len(coupled_constraints) != 0:
        format_coupled_constraint = []
        for or_constraint in range(len(coupled_constraints)):
            and_constraints = {}
            for and_constraint in coupled_constraints[or_constraint].keys():
                and_constraints[input_names.index(and_constraint)] = coupled_constraints[or_constraint][and_constraint]
            format_coupled_constraint.append(and_constraints)
        constraint.update_coupled_constraints(format_coupled_constraint)
    return (input_dim, input_scales, input_normalized_factor, input_names), constraint

def parse_constraints(filename):
    """this function is used to parse the constraints from the file"""
    # Define dictionaries to store the parsed data
    self_constraints = {}
    coupled_constraints = []
    output_objective = {}
    output_constraints = {}

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
            elif line.startswith('#output objective'):
                section = 'output_objective'
            elif line.startswith('#output constraint'):
                section = 'output_constraint'
            elif line.startswith('var:') and section:
                # Process the variable line based on the section
                parts = line.split()
                var_name = parts[1]
                range_values = parts[3].strip('[]').split(',')
                if section == 'self_constraint':
                    scale = int(parts[5])
                    self_constraints[var_name] = [int(range_values[0]), int(range_values[1]), scale]
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
                obj_name = parts[1]
                if section == 'output_objective':
                    obj_direction = parts[3]
                    output_objective[obj_name] = obj_direction
                elif section == 'output_constraint':
                    range_values = parts[3].strip('[]').split(',')
                    output_constraints[obj_name] = [int(range_values[0]), int(range_values[1])]

    return self_constraints, coupled_constraints, output_objective, output_constraints

if __name__ == '__main__':
    self_constraints, coupled_constraints, output_objective, output_constraints = parse_constraints('../data/input_constraint.txt')
    print(self_constraints)
    print(coupled_constraints)
    print(output_objective)
    print(output_constraints)
    (input_dim, input_scales, input_normalized_factor, input_names), constraint = fill_constraints(self_constraints, coupled_constraints)
    print(input_dim)
    print(input_scales)
    print(input_normalized_factor)
    print(input_names)
    print(constraint)