import torch
import data
import time
import utils
import warnings
import random
from colorama import Fore, Style

from interface import fill_constraints, parse_constraints
from format_constraints import Constraints_Brute_Force


# Tensor Settings
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
t_type = torch.float64

# Input Settings
CONSTRAINT_FILE = '../specification/input_spec_optimisation_set_3.txt'
self_constraints, coupled_constraints, INPUT_CONSTANT, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, objective_function_category, parameter_tuning_obj = parse_constraints(CONSTRAINT_FILE)
(INPUT_DATA_DIM, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_EXP, INPUT_OFFSETS, INPUT_NAMES), constraint_set = fill_constraints(self_constraints, coupled_constraints, device)
OBJECTIVES_TO_OPTIMISE_DIM = len(OBJECTIVES_TO_OPTIMISE)
OBJECTIVE_DIM = OBJECTIVES_TO_OPTIMISE_DIM + len(OUTPUT_OBJECTIVE_CONSTRAINT)
OBJECTIVES_TO_OPTIMISE_INDEX = list(range(OBJECTIVES_TO_OPTIMISE_DIM))

# Dataset Settings
if objective_function_category == 'synthetic':
    RAW_DATA_FILE = '../specification/ppa_v2.db'
    data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_CONSTANT , t_type, device)
elif objective_function_category == 'NutShell':
    data_set = data.NutShell_Data(INPUT_NAMES, OBJECTIVES_TO_OPTIMISE, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_CONSTANT, OUTPUT_OBJECTIVE_CONSTRAINT, parameter_tuning_obj, t_type, device)
elif objective_function_category == 'EL2':
    data_set = data.EL2_Data(INPUT_NAMES, OBJECTIVES_TO_OPTIMISE, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR, INPUT_OFFSETS, INPUT_CONSTANT, INPUT_EXP, OUTPUT_OBJECTIVE_CONSTRAINT, parameter_tuning_obj, t_type, device)

print("<-------------- Optimisation Settings -------------->")
print(f"Input Names: {INPUT_NAMES}")
print(f"Input Self Constraints: {self_constraints}")
print(f"Input Offset: {INPUT_OFFSETS}")
print(f"Input Scales: {INPUT_DATA_SCALES}")
print(f"Input Normalised Factor: {INPUT_NORMALIZED_FACTOR}")
print(f"Input Exponential: {INPUT_EXP}")
print(f"Optimisation Device : {objective_function_category}")
print(f"Objectives to Optimise: {OBJECTIVES_TO_OPTIMISE}")
print(f"Output Objective Constraint: {OUTPUT_OBJECTIVE_CONSTRAINT}")
print("<--------------------------------------------------->")

#Constraints
constraint_set = Constraints_Brute_Force( OBJECTIVES_TO_OPTIMISE_DIM, len(OUTPUT_OBJECTIVE_CONSTRAINT))
for input_constraint in self_constraints:
    constraint_set.update_self_constraints(input_constraint)

for constraint_range in OUTPUT_OBJECTIVE_CONSTRAINT.keys():
    constraint_set.update_output_obj_constraint(OUTPUT_OBJECTIVE_CONSTRAINT[constraint_range])

obj_normalized_factors = list(data_set.output_normalised_factors.values())
print("obj_normalized_factors: ", obj_normalized_factors)

overall_iteration_required = 50
verbose = True
record = True
if record:
    record_file_name = '../test/test_results/'
    for obj_name in OBJECTIVES_TO_OPTIMISE.keys():
        record_file_name = record_file_name + obj_name + '_'
    record_file_name = record_file_name + 'brute_force_record_result.txt'
    results_record = utils.brute_force_training_result(INPUT_NAMES, OBJECTIVES_TO_OPTIMISE, overall_iteration_required, record_file_name)



