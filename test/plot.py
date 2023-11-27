import matplotlib.pyplot as plt

# Read the data from the text file
data = []

with open('record_result.txt', 'r') as file:
    lines = file.readlines()
    for line in lines[4:]:
        iteration, current_val, current_best_val, time = line.strip().split(',')
        data.append((int(iteration), float(current_best_val), float(time)))

# Extract the values for plotting
iterations = [d[0] for d in data]
current_best_val = [d[1] for d in data]
times = [d[2] for d in data]

# Plot iteration vs current_val
plt.figure(figsize=(10, 5))
plt.plot(iterations, current_best_val, marker='o')
plt.xlabel('Iteration')
plt.ylabel('Current Best Value')
plt.title('Iteration vs Current Best Value')

# Plot iteration vs time
plt.figure(figsize=(10, 5))
plt.plot(times, current_best_val, marker='o')
plt.xlabel('Time (s)')
plt.ylabel('Current Best Value')
plt.title('Time vs Current Best Value')

# Show the plots
plt.show()
