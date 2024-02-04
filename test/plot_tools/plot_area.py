import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

def plot_3d_from_file(file_path):
    # Read the dataset from a text file, assuming the data is comma-separated
    df = pd.read_csv(file_path, sep=', ', engine='python', header=0, 
                     names=['iteration', 'time', 'arch', 'btb', 'current_hyper_vol', 'estimated_clock_period', 'ncycles_dijkstra'])
    
    # Set up the 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # Set axes labels
    ax.set_xlabel('Architecture (arch)')
    ax.set_ylabel('Branch Target Buffer (btb)')
    ax.set_zlabel('Current Hyper Volume')
    ax.set_title('Estimated clock period * ncycles Dijkstra')
    # Plot the data
    ax.scatter(df['arch'], df['btb'], df['current_hyper_vol'], marker='o', linewidths=1)
    
    # Show the plot
    plt.show()

# File path to the text file containing the data
file_path = '../test_results/estimated_clock_period_ncycles_dijkstra_brute_force_record_result.txt'

# Call the function with the path to your text file
plot_3d_from_file(file_path)
