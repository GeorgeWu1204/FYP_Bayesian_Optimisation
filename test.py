import torch
import matplotlib.pyplot as plt

def smooth_step(x, condition):
    """Smooth, differentiable step function."""
    return 1 / (1 + torch.exp(-10 * (x - condition[1]))) - 1 / (1 + torch.exp(-10 * (x - condition[0]))) + 0.5

# Generate a range of values
x = torch.linspace(-2, 4, 100)

# Define lower and upper bounds for the transition
lower_bound = 0
upper_bound = 2

# Apply the smooth step function
y = smooth_step(x, [lower_bound, upper_bound])

# Plotting
plt.plot(x.numpy(), y.numpy())
plt.xlabel("x")
plt.ylabel("smooth_step(x)")
plt.title("Smooth Step Function")
plt.grid(True)
plt.show()