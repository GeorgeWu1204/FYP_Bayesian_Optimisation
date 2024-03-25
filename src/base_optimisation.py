import torch
import data
import time
import utils
import warnings
import random
from colorama import Fore, Style

from interface import parse_constraints
from format_constraints import Simpler_Constraints
from optimisation_models import brute_force, hill_climbing

# Tensor Settings
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
t_type = torch.float64

# Input Settings
CONSTRAINT_FILE = '../specification/input_spec_btb_lsu.txt'
input_info, output_info, param_tuner, optimisation_name = parse_constraints(CONSTRAINT_FILE, device)
# Dataset Settings
if output_info.optimisation_target == 'synthetic':
    RAW_DATA_FILE = '../specification/ppa_v2.db'
    data_set = data.read_data_from_db(RAW_DATA_FILE, input_info, output_info, t_type, device)
elif output_info.optimisation_target == 'NutShell':
    data_set = data.NutShell_Data(input_info, output_info, param_tuner, t_type, device)
elif output_info.optimisation_target == 'EL2':
    data_set = data.EL2_Data(input_info, output_info, param_tuner, optimisation_name, t_type, device)


print("<-------------- Optimisation Settings -------------->")
print(f"Input Names: {input_info.input_names}")
print(f"Input Self Constraints: {input_info.self_constraints}")
print(f"Input Offset: {input_info.input_offsets}")
print(f"Input Scales: {input_info.input_scales}")
print(f"Input Normalised Factor: {input_info.input_normalized_factor}")
print(f"Input Exponential: {input_info.input_exp}")
print(f"Optimisation Device : {output_info.optimisation_target}")
print(f"Objectives to Optimise: {output_info.obj_to_optimise}")
print(f"Output Objective Constraint: {output_info.output_constraints}")
print("<--------------------------------------------------->")

#Building simpler constraints
ref_points = utils.find_ref_points(output_info.obj_to_optimise_dim, data_set.objs_direct, t_type, device)
overall_iteration_required = 50
verbose = True
record = True
if record:
    record_file_name = '../test/test_results/'
    for obj_name in output_info.obj_to_optimise.keys():
        record_file_name = record_file_name + obj_name + '_'
    record_file_name = record_file_name + 'brute_force_record_result.txt'
    results_record = utils.other_model_training_result(input_info.input_names, output_info.obj_to_optimise, overall_iteration_required, record_file_name)

# Optimisation Loop
brute_force(output_info, ref_points, data_set, record, results_record)
hill_climbing(output_info, ref_points, data_set, record, results_record, max_iterations=30, step_size=0.01)



