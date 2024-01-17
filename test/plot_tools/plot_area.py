import torch
import sys
sys.path.insert(0, '../../src')
import data
import utils
from interface import fill_constraints, parse_constraints
from format_constraints import Constraints_Brute_Force
import matplotlib.pyplot as plt

CONSTRAINT_FILE = '../../data/input_constraint.txt'
self_constraints, coupled_constraints, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT = parse_constraints(CONSTRAINT_FILE)
(INPUT_DATA_DIM, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_NAMES), _ = fill_constraints(self_constraints, coupled_constraints, torch.device('cpu'))
OBJECTIVES_TO_OPTIMISE_DIM = len(OBJECTIVES_TO_OPTIMISE)
OBJECTIVES_TO_OPTIMISE_INDEX = list(range(OBJECTIVES_TO_OPTIMISE_DIM))
OBJECTIVES_TO_EVALUATE = OBJECTIVES_TO_OPTIMISE_DIM + len(OUTPUT_OBJECTIVE_CONSTRAINT)

RAW_DATA_FILE = '../../data/ppa_v2.db'
INPUT_VARIABLES = []
for input_name in INPUT_NAMES:
    INPUT_VARIABLES.append(self_constraints[input_name][:2])

data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR)

#Constraints
constraint_set = Constraints_Brute_Force(INPUT_DATA_SCALES, OBJECTIVES_TO_OPTIMISE_DIM, len(OUTPUT_OBJECTIVE_CONSTRAINT))
constraint_set.update_self_constraints(0, [1, 12])
constraint_set.update_self_constraints(1, [5, 6])
constraint_set.update_self_constraints(2, [4, 255])
constraint_set.update_output_obj_constraint([0, 20000])
constraint_set.update_output_obj_constraint([0, 12000])

obj_normalized_factors = list(data_set.output_normalised_factors.values())

# Global Best Values
sample_inputs = utils.find_samples_brute_force(INPUT_VARIABLES)
overall_iteration_required = len(sample_inputs)
records_to_plot = {}
#Optimisation Loop
for iteration in range(overall_iteration_required):
    sample_input = sample_inputs[iteration]
    if constraint_set.check_meet_self_constraint_for_brute_force(sample_input) == True:
        result = data_set.find_single_ppa_result(sample_input)
        if result == None:
            continue
        if constraint_set.check_meet_output_obj_constraint_for_brute_force(result, OBJECTIVES_TO_OPTIMISE_DIM) == True:
            volume = utils.calculate_volumes_for_brute_force(result, obj_normalized_factors, OBJECTIVES_TO_OPTIMISE_DIM)
            if sample_input[1] == 5 and volume < 1.05:
                records_to_plot[(sample_input[0], sample_input[2])] = volume


x_coords = [key[0] for key in records_to_plot.keys()]
y_coords = [key[1] for key in records_to_plot.keys()]
values = [value for value in records_to_plot.values()]

# Create the scatter plot
plt.scatter(x_coords, y_coords, c=values, cmap='viridis')
plt.colorbar(label='Values')
plt.xlabel('arch')
plt.ylabel('btb')
# plt.title('2D Dot Plot with Color Indication')
plt.grid(True)

plt.show()
