import matplotlib.pyplot as plt

# Read the data from the text file
data = []
output_string = 'coupled_constraints_dataset'
with open('../test_results/coupled_constraints_dataset.txt', 'r') as file:
    lines = file.readlines()
    max = float(lines[1].strip().split(' ')[1])
    print(max)
    for line in lines[4:]:
        iteration, current_best_val, _, time, random_best_val = line.strip().split(',')
        data.append((int(iteration), float(current_best_val), float(time), float(random_best_val)))
max_value = [max for i in range(len(data))]
# Extract the values for plotting
iterations = [d[0] for d in data]
current_best_val = [d[1] for d in data]
times = [d[2] for d in data]
random_best_val = [d[3] for d in data]

# Plot iteration vs current_val
plt.figure(figsize=(10, 5))
plt.plot(iterations, max_value, color='red', label='Optimal Value')
plt.plot(iterations, current_best_val, color='blue', label='Bayesian Optimisation')
plt.plot(iterations, random_best_val, color='green', label='Brute Force')
plt.xlabel('Iteration')
plt.ylabel('LUTs Value')
plt.legend()
plt.title('Optimisation Process for LUTs')

# Plot iteration vs time
# plt.figure(figsize=(10, 5))
# plt.plot(times, max_value, color='red', label='max_value')
# plt.plot(times, current_best_val, marker='o', label='current_best_val')
# plt.plot(iterations, random_best_val, marker='o', label='random_best_val')
# plt.yscale('log')
# plt.xlabel('Time (s)')
# plt.ylabel('Current Best Value')
# plt.xscale('log')
# plt.title('Time vs Current Best Value')
# plt.legend()
# Show the plots
plt.savefig('../plot_results/' + output_string + '.png')
plt.show()
