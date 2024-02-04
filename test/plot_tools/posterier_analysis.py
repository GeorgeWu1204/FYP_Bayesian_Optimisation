#------------------------------Only as a reference--------------------------------
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, RBF

# Generate sample data
X = np.random.rand(100, 2)
y = np.sin(2 * np.pi * X).sum(axis=1)

# Define the kernel with broader bounds
kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))

# Fit Gaussian Process with increased number of restarts to improve optimization
gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
gp.fit(X, y)

# Grid over which we will visualize the GP
x = np.linspace(0, 1, 100)
y = np.linspace(0, 1, 100)
X, Y = np.meshgrid(x, y)
print("X shape is ", X.shape)

XY = np.vstack([X.ravel(), Y.ravel()]).T

# Make predictions and compute uncertainty
mean_prediction, std_deviation = gp.predict(XY, return_std=True)
print("mean_prediction shape is ", mean_prediction.shape)
print("std_deviation shape is ", std_deviation.shape)
Z = mean_prediction.reshape(X.shape)
Uncertainty = std_deviation.reshape(X.shape)
print("z shape is ", Z.shape)
print("Uncertainty shape is ", Uncertainty.shape)

# Plot Mean
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.7)
print("X shape is ", X.shape)   
print("Y shape is ", Y.shape)
print("Z shape is ", Z.shape)

# Generate unique, strictly increasing contour levels
min_uncertainty, max_uncertainty = np.min(Uncertainty), np.max(Uncertainty)
levels = np.linspace(min_uncertainty, max_uncertainty, num=10)
levels = np.unique(levels)  # Ensure levels are unique
epsilon = np.diff(levels).min() * 0.1  # Small increment
levels[1:] += epsilon  # Avoid incrementing the first level to keep the minimum

# Plot Uncertainty using Contourf at the base
contour = ax.contourf(X, Y, Uncertainty, zdir='z', offset=Z.min()-1.5, levels=levels, cmap='inferno', alpha=0.5)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Mean Prediction')
ax.set_title('Gaussian Process Mean and Uncertainty')

# Add a color bar for the contour plot
fig.colorbar(contour, shrink=0.5, aspect=5, label='Uncertainty (Std Dev)')

plt.show()

print("done")