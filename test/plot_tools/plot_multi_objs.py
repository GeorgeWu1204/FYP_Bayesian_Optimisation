import matplotlib.pyplot as plt
# Read the data from the text file
data = []
optimised_obj_dim = 2

obj_normalized_factors = 4.668999999999999 * 1289581.0
max_value = 14.268 * 311063/obj_normalized_factors

objnames = ['Estimated clock period', 'ncycles Dijkstra']

# Join the names in the list with underscores and convert them to lowercase
output_string = "_".join(objnames).lower().replace(" ", "_")


def process_data(file_name):
    data = []
    objs = []
    with open(file_name, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:
            iteration, time, objs0, objs1 = line.strip().split(',')
            data.append((int(iteration), float(time), float(objs0), float(objs1)))
    iterations = [d[0] for d in data]
    times = [d[1] for d in data]
    objs.append([d[2] for d in data])
    objs.append([d[3] for d in data])
    return iterations, times, objs

def find_hyper_vol(objs, iterations):
    hyper_volume = []
    best_volume = 4
    for i in iterations:
        temp_volume = (objs[0][i] * objs[1][i])/obj_normalized_factors
        if temp_volume == 0:
            temp_volume = 1000
        if temp_volume < best_volume:
            best_volume = temp_volume
        hyper_volume.append(best_volume)
    return hyper_volume



# Extract the values for plotting
overall_iterations, times, objs = process_data('../test_results/'+output_string+'_record_result.txt')
hyper_volume_bo = find_hyper_vol(objs, overall_iterations)
max_values = [max_value for i in range(len(overall_iterations))]

iterations, times, objs = process_data('../test_results/'+output_string+'_brute_force_record_result.txt')
hyper_volume_brute_force = find_hyper_vol(objs, overall_iterations)


# Plot iteration vs current_val
plt.figure(figsize=(10, 5))
plt.plot(overall_iterations, max_values, color='red', label='Optimal Value')
plt.plot(overall_iterations, hyper_volume_bo, color='blue', label='Bayesian Optimisation')
plt.plot(overall_iterations, hyper_volume_brute_force,color='green', label='Brute Force')
plt.xlim(0, 150)
plt.ylim(max_value - 0.01, 0.8)
plt.xlabel('Iteration')
plt.ylabel('Normalised Estimated clock period * Dijkstra Cycle Count')
plt.legend()
plt.title('Optimisation Process for Estimated clock period * Dijkstra Cycle count')

# Show the plots
plt.savefig('../plot_results/' + output_string + '.png')
plt.show()
