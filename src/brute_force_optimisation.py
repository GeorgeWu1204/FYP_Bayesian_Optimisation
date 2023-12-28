
import data
import time
import utils
from colorama import Fore, Style
import random

from format_constraints import Constraints_Brute_Force
#Data_set 1
INPUT_DATA_DIM = 3
INPUT_DATA_SCALES = [1, 1, 1]
INPUT_NORMALIZED_FACTOR = [12, 6, 255]    # normalized_Factor = max_value / scale
RAW_DATA_FILE = '../data/ppa_v2.db'
INPUT_VARIABLES = [[1, 12], [5, 6], [4, 255]]

OBJECTIVES_TO_OPTIMISE = {'estimated_clock_period': 'minimise', 'ncycles_matmul': 'minimise'}
OBJECTIVES_TO_OPTIMISE_DIM = len(OBJECTIVES_TO_OPTIMISE)
OBJECTIVES_TO_OPTIMISE_INDEX = list(range(OBJECTIVES_TO_OPTIMISE_DIM))
#objective to evaluate
OUTPUT_OBJECTIVE_CONSTRAINT = {'lut': [0,20000], 'ff' : [0, 12000]}
OBJECTIVES_TO_EVALUATE = OBJECTIVES_TO_OPTIMISE_DIM + len(OUTPUT_OBJECTIVE_CONSTRAINT)

data_set = data.read_data_from_db(RAW_DATA_FILE, OBJECTIVES_TO_OPTIMISE, OUTPUT_OBJECTIVE_CONSTRAINT, INPUT_DATA_SCALES, INPUT_NORMALIZED_FACTOR)

#Constraints
constraint_set = Constraints_Brute_Force(INPUT_DATA_SCALES, OBJECTIVES_TO_OPTIMISE_DIM, len(OUTPUT_OBJECTIVE_CONSTRAINT))
constraint_set.update_self_constraints(0, [1, 12])
constraint_set.update_self_constraints(1, [5, 6])
constraint_set.update_self_constraints(2, [4, 255])
constraint_set.update_output_obj_constraint([0, 20000])
constraint_set.update_output_obj_constraint([0, 12000])

obj_normalized_factors = list(data_set.output_normalised_factors.values())
print("obj_normalized_factors: ", obj_normalized_factors)
verbose = True
record = True


# Global Best Values
best_volume = 100
best_sample = None  
best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
sample_inputs = utils.find_samples_brute_force(INPUT_VARIABLES)
random.shuffle(sample_inputs)
overall_iteration_required = len(sample_inputs)
print("overall_iteration_required: ", overall_iteration_required)

if record:
    results_record = utils.brute_force_training_result(OBJECTIVES_TO_OPTIMISE, overall_iteration_required, '../test/record_brute_force_result.txt')

#Optimisation Loop
for iteration in range(overall_iteration_required):
    t0 = time.monotonic()
    sample_input = sample_inputs[iteration]
    if constraint_set.check_meet_self_constraint_for_brute_force(sample_input) == True:
        result = data_set.find_single_ppa_result(sample_input)
        if result == None:
            continue
        if constraint_set.check_meet_output_obj_constraint_for_brute_force(result, OBJECTIVES_TO_OPTIMISE_DIM) == True:
            volume = utils.calculate_volumes_for_brute_force(result, obj_normalized_factors, OBJECTIVES_TO_OPTIMISE_DIM)
            if volume < best_volume:
                best_volume = volume
                best_sample = sample_input
                best_results = result
                print(f"{Fore.GREEN}best_volume: {best_volume}, best_sample: {best_sample}, best_results: {best_results}{Style.RESET_ALL}")
    t1 = time.monotonic()
    if record:
        results_record.record(iteration, best_results, t1-t0)
print("best_results: ", best_results)
if record:
    results_record.store()

