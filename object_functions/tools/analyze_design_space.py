import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def reorganize_dict(original_dict, objectives):
    # Initialize the new dictionary with objectives as keys and empty lists as values
    new_dict = {obj: [] for obj in objectives}
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
    ax.set_ylabel('Variation in percentage of objectives')
    ax.set_title(f'{var_name} impact on the performance of different benchmark')
    ax.set_xticks(index)
    ax.set_xticklabels(variables)
    ax.legend()

    # Show the plot
    plt.tight_layout()
    plt.savefig(f'../Core_Design_Space/Figures/{var_name}_analysis.png')

def analyze_variable_impact(file_path, input_vars_set, objectives, variable_of_interest, freeze_var=None, freeze_val=None):
    with open(file_path, 'r') as file:
        header = file.readline().strip().split(',')  # Read the header and determine the number of columns
        num_columns = len(header)
        
        # Read the rest of the file and keep only rows with the correct number of columns
        valid_lines = [header]  # Start with the header
        for line in file:
            row = line.strip().split(',')
            if len(row) == num_columns:  # Check if the row has the correct number of columns
                valid_lines.append([float(x) for x in line.strip().split(',')])
    # Convert the list of valid lines into a DataFrame
    df = pd.DataFrame(valid_lines[1:], columns=valid_lines[0])
    print(variable_of_interest)
    
    if freeze_var and freeze_val is not None:
        df = df[df[freeze_var] == freeze_val]
    # Define the input variables and objectives
    input_vars = input_vars_set.copy() # Adjust based on your dataset
    input_vars.remove(variable_of_interest)  # Exclude the variable of interest from the grouping variables

    # Dictionary to store the differences for each value of the variable of interest
    diffs = {value: {obj: [0.0] for obj in objectives} for value in df[variable_of_interest].unique()}

    # Step 2: Find groups and calculate differences
    for _, group in df.groupby(input_vars):
        # Only proceed if there are at least 2 rows to compare
        if len(group) > 1:
            min_value = group[variable_of_interest].min()
            base_case_rows = group[group[variable_of_interest] == min_value]
            for _, row in group.iterrows():
                value = row[variable_of_interest]
                # Skip the row if it's the base case itself
                # Calculate and store the absolute differences in objectives compared to the base case
                for objective in objectives:
                    diff_sum = sum(abs(row[objective] - base_case_row[objective]) for _, base_case_row in base_case_rows.iterrows())
                    avg_diff = diff_sum / len(base_case_rows)
                    diffs[value][objective].append(avg_diff)
    # Step 3: Calculate average differences for each value of the variable of interest
    avg_diffs = {value: {obj: sum(diffs[value][obj]) / len(diffs[value][obj]) if diffs[value][obj] else 0 
                         for obj in objectives} 
                 for value in diffs}
    return avg_diffs, df[variable_of_interest].unique()

# Usage example:
file_path = '../Dataset/EL2_dataset_record_4_3_Piccm_dccm.txt'

input_vars = ['dccm_size', ' dccm_num_banks', ' iccm_size', ' iccm_num_banks']

# normalisation_factor = {' mcycle_cmark': 282995, ' mcycle_dhry': 343110, ' LUT as Logic': 30000}
normalisation_factor = {' mcycle_cmark_iccm': 282995, ' mcycle_cmark_dccm': 282995, ' LUT as Logic': 30000}

input_valus = {'dccm_size': [4, 8, 16, 32, 64, 128, 256, 512], ' dccm_num_banks': [2, 4], ' iccm_size': [4, 8, 16, 32, 64, 128, 256, 512], ' iccm_num_banks': [2, 4, 8]}
for var_of_interest in input_vars:
    if var_of_interest == 'btb_size':
        result, available_interest_var_range = analyze_variable_impact(file_path, input_vars, list(normalisation_factor.keys()), var_of_interest, ' btb_enable', 1)
    else:
        result, available_interest_var_range = analyze_variable_impact(file_path, input_vars, list(normalisation_factor.keys()), var_of_interest)
    for value in result:
        for obj in result[value]:
            result[value][obj] = (result[value][obj] / normalisation_factor[obj]) * 100
    print(reorganize_dict(result, list(normalisation_factor.keys())))
    plot_bar_chart(reorganize_dict(result, list(normalisation_factor.keys())), available_interest_var_range, var_of_interest.strip())


