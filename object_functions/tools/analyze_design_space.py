import matplotlib.pyplot as plt
import numpy as np
# def analyze_variable_impact(file_path, variable_of_interest):
#     # Step 1: Read the Dataset
#     df = pd.read_csv(file_path, delimiter=',')  # Adjust delimiter if necessary
    
#     # The input variables (excluding the variable of interest)
#     input_vars = ['btb_size', ' lsu_num_nbload', ' btb_enable', ' lsu_stbuf_depth']
#     if variable_of_interest in input_vars:
#         input_vars.remove(variable_of_interest)
#     print(input_vars)
#     # The objectives
#     objectives = [' mcycle_cmark', ' mcycle_dhry', ' LUT as Logic']
    
#     # Results dictionary to store the average differences
#     results = {obj: [] for obj in objectives}

#     # Step 2: Group by the other input variables
#     grouped = df.groupby(input_vars)
#     # Step 3: Calculate the average difference in objectives for each group
#     for _, group in grouped:
#         if len(group) > 1:  # Ensure there's variation in the variable of interest
#             for objective in objectives:
#                 # Calculate the average difference for this objective in the current group
#                 average_diff = group[objective].diff().abs().mean()
#                 results[objective].append(average_diff)
#     print(results)

#     # return overall_avg_diff
import pandas as pd
from itertools import combinations

def reorganize_dict(original_dict):
    # Initialize the new dictionary with objectives as keys and empty lists as values
    new_dict = {' mcycle_cmark': [], ' mcycle_dhry': [], ' LUT as Logic': []}
    
    # Iterate over the original dictionary
    for key in original_dict:
        # For each objective, append the value to the corresponding list in the new dictionary
        for objective in new_dict:
            # Strip leading/trailing whitespace from the objective keys in the original dictionary
            if objective in original_dict[key]:
                new_dict[objective].append(original_dict[key][objective])
    
    return new_dict

def plot_bar_chart(data, variables, var_name):
    # Number of variables
    n_vars = len(variables)
    
    # Number of objectives (and groups in the bar chart)
    n_groups = len(data[next(iter(data))])

    # Create a figure and a set of subplots
    fig, ax = plt.subplots()

    # Set the positions for the groups
    index = np.arange(n_groups)

    # Width of a bar
    bar_width = 0.2

    # Set the positions of the bars on the x-axis
    positions = [index - bar_width, index, index + bar_width]

    # Plotting each objective
    for i, (objective, values) in enumerate(data.items()):
        plt.bar(positions[i], values, bar_width, label=objective.strip())

    # Adding labels, title, and legend
    ax.set_xlabel(f'{var_name} values')
    ax.set_ylabel('Difference in objectives')
    ax.set_title(f'{var_name} impact on the performance of different benchmark')
    ax.set_xticks(index)
    ax.set_xticklabels(variables)
    ax.legend()

    # Show the plot
    plt.tight_layout()
    plt.savefig(f'../Core_Design_Space/Figures/{var_name}_analysis.png')

def analyze_variable_impact(file_path, variable_of_interest, freeze_var=None, freeze_val=None):
    # Step 1: Read the Dataset
    df = pd.read_csv(file_path, delimiter=',')  # Adjust delimiter if necessary
    if freeze_var and freeze_val is not None:
        df = df[df[freeze_var] == freeze_val]
    # Define the input variables and objectives
    input_vars = ['btb_size', ' lsu_num_nbload', ' btb_enable', ' lsu_stbuf_depth']  # Adjust based on your dataset
    input_vars.remove(variable_of_interest)  # Exclude the variable of interest from the grouping variables
    objectives = [' mcycle_cmark', ' mcycle_dhry', ' LUT as Logic']  # Objectives

    # Dictionary to store the differences for each value of the variable of interest
    diffs = {value: {obj: [0.0] for obj in objectives} for value in df[variable_of_interest].unique()}

    # Step 2: Find groups and calculate differences
    for _, group in df.groupby(input_vars):
        # Only proceed if there are at least 2 rows to compare
        if len(group) > 1:
            # Iterate over all combinations of rows in the group
            # quit()
            min_value = group[variable_of_interest].min()
            base_case_rows = group[group[variable_of_interest] == min_value]
            for _, row in group.iterrows():
                value = row[variable_of_interest]
                # Skip the row if it's the base case itself
                # Calculate and store the absolute differences in objectives compared to the base case
                for objective in objectives:
                    # Calculate the difference with each base case row and take the average
                    diff_sum = sum(abs(row[objective] - base_case_row[objective]) for _, base_case_row in base_case_rows.iterrows())
                    avg_diff = diff_sum / len(base_case_rows)
                    diffs[value][objective].append(avg_diff)
    # Step 3: Calculate average differences for each value of the variable of interest
    avg_diffs = {value: {obj: sum(diffs[value][obj]) / len(diffs[value][obj]) if diffs[value][obj] else 0 
                         for obj in objectives} 
                 for value in diffs}
    return avg_diffs

# Usage example:
file_path = '../Dataset/EL2_dataset_record_4_3_btb_focus.txt'
variable_of_interest = ' lsu_stbuf_depth'
result = analyze_variable_impact(file_path, variable_of_interest)
plot_bar_chart(reorganize_dict(result), [2, 4, 8], 'LSU_stbuf_depth')

# Usage example:
# analyze_dataset('../Dataset/EL2_dataset_record_4_3_btb_focus.txt')
