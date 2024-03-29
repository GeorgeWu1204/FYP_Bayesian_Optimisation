import matplotlib.pyplot as plt
import numpy as np

def plot_algorithm_performance(data):
    """
    Plots a bar chart for algorithm performance.

    Parameters:
    data (dict): A dictionary where keys are algorithm names and values are tuples of
                 (average cycles to converge, distance to best point).

    The function plots a bar chart with algorithms on the x-axis and the two metrics
    represented as side-by-side bars for each algorithm.
    """
    algorithms = list(data.keys())
    avg_cycles = [values[0] for values in data.values()]
    distances = [values[1] for values in data.values()]

    # Setting up the bar positions
    x = np.arange(len(algorithms))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    bars1 = ax.bar(x - width/2, avg_cycles, width, label='Avg Cycles to Converge')
    bars2 = ax.bar(x + width/2, distances, width, label='Distance to Best Point')

    # Adding some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Values')
    ax.set_title('Algorithm performance comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend()

    # Beautifying the plot
    ax.bar_label(bars1, padding=3)
    ax.bar_label(bars2, padding=3)
    fig.tight_layout()

    plt.show()

# Example usage
data = {
    'Algorithm A': (10, 0.5),
    'Algorithm B': (15, 0.3),
    'Algorithm C': (8, 0.6)
}
plot_algorithm_performance(data)
