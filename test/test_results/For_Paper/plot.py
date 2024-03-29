import matplotlib.pyplot as plt

with open('FPGA1_Coremark.txt', 'r') as file:
    data = file.read()
# Convert the string data into a list of lists, each containing integers
data_lines = data.strip().split('\n')
data_list = [[int(value) for value in line.split(',')] for line in data_lines[1:]]

# Extract columns, ignoring zeros for the first two columns
x_indexes = range(len(data_list))
bo_with_cat = [y if y != 0 else None for x, y, z in data_list]
bo_without_cat = [y if y != 0 else None for x, z, y in data_list]
hill_climbing = [z for x, y, z in data_list]

# Plotting
plt.figure(figsize=(10, 6))

plt.plot(x_indexes, bo_with_cat, label='BO with Categorical', marker='o', linestyle='-', markersize=5)
plt.plot(x_indexes, bo_without_cat, label='BO without Categorical', marker='o', linestyle='-', markersize=5)
plt.plot(x_indexes, hill_climbing, label='Hill Climbing', marker='o', linestyle='-', markersize=5)

plt.title('Performance Comparison')
plt.xlabel('Iteration')
plt.ylabel('Value')
plt.legend()

plt.show()