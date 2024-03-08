import random
import time
from utils import calculate_volumes_for_brute_force, find_samples_brute_force
from colorama import Fore, Style

def brute_force(INPUT_VARIABLES, data_set, constraint_set, obj_normalized_factors, OBJECTIVES_TO_OPTIMISE_DIM, record, results_record, INPUT_CONSTANT):
    # Global Best Values
    best_volume = 100
    best_sample = None  
    best_results = [data_set.worst_value[obj] for obj in data_set.objs_direct]
    sample_inputs = find_samples_brute_force(INPUT_VARIABLES)
    random.shuffle(sample_inputs)
    overall_iteration_required = len(sample_inputs)
    print("overall_iteration_required: ", overall_iteration_required)
    #Optimisation Loop
    for iteration in range(overall_iteration_required):
        t0 = time.monotonic()
        sample_input = sample_inputs[iteration]
        if constraint_set.check_meet_self_constraint_for_brute_force(sample_input) == True:
            result = data_set.find_single_ppa_result_for_unnormalised_sample(sample_input)
            if result == None:
                continue
            if constraint_set.check_meet_output_obj_constraint_for_brute_force(result, OBJECTIVES_TO_OPTIMISE_DIM) == True:
                volume = calculate_volumes_for_brute_force(result, obj_normalized_factors, OBJECTIVES_TO_OPTIMISE_DIM)
                if volume < best_volume:
                    best_volume = volume
                    best_sample = sample_input
                    best_results = result
            else:
                continue
        t1 = time.monotonic()
        if record:
            for index in INPUT_CONSTANT.keys():
                del sample_input[index]
            results_record.record(iteration, sample_input, 1-volume, best_results, t1-t0)
    print(f"{Fore.GREEN}best_volume: {best_volume}, best_sample: {best_sample}, best_results: {best_results}{Style.RESET_ALL}")
    if record:
        results_record.store()





def hill_climbing(var_ranges, objective_function, max_iterations=1000, step_size=1):
    # Generate initial solution
    current_solution = {var: random.uniform(range_[0], range_[1]) for var, range_ in var_ranges.items()}
    current_value = objective_function(current_solution)
    
    for _ in range(max_iterations):
        # Generate a neighbor solution
        neighbor_solution = current_solution.copy()
        for var in neighbor_solution:
            # Randomly decide whether to increase or decrease the variable value
            direction = random.choice([-1, 1])
            # Adjust the variable value within its range
            neighbor_solution[var] = max(min(neighbor_solution[var] + direction * step_size, var_ranges[var][1]), var_ranges[var][0])
        
        # Evaluate the neighbor solution
        neighbor_value = objective_function(neighbor_solution)
        
        # Check if the neighbor solution is better
        if neighbor_value > current_value:
            current_solution, current_value = neighbor_solution, neighbor_value
        # If the objective function returns zero, we've hit a boundary condition
        elif neighbor_value == 0:
            break
    
    return current_solution, current_value
