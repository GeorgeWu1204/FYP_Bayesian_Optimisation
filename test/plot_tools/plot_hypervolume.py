import pandas as pd
import matplotlib.pyplot as plt

def plot_max_hyper_vol(file_path):
    # Try reading the file with a specified delimiter, assuming the first row contains headers
    try:
        data = pd.read_csv(file_path, delimiter=',')
    except Exception as e:
        print(f"Error reading the file: {e}")
        return
    
    # Check if 'hyper_vol' column exists
    if ' hyper_vol' not in data.columns:
        print("Column 'hyper_vol' not found in the data.")
        return
    
    # Calculate the cumulative maximum of the 'hyper_vol' column
    max_values = data[' hyper_vol'].cummax()
    # Plot the results
    plt.figure(figsize=(10, 6))  # Set a larger figure size for better visibility
    plt.plot(max_values, marker='o', linestyle='-')  # Add markers for each point
    plt.xlabel('Index')
    plt.ylabel('Cumulative Maximum of hyper_vol')
    plt.title('Cumulative Maximum of hyper_vol Over Indices')
    plt.grid(True)
    plt.savefig('../plot_results/optimisation_results.png')


# Replace 'your_file_path.txt' with the actual path to your data file
plot_max_hyper_vol('../test_results/mcycle_cmark_mcycle_dhry_mcycle_cmark_iccm_mcycle_cmark_dccm_record_input.txt')
