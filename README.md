# FYP_Bayesian_Optimisation

This project is currently under development. The aim is to use Bayesian Optimisation to find the multi-objectives optimal solutions within the customised processor's design space.

To run this code, run the following command in the terminal: 

```cd src``` \
```python3 optimisation.py```

The model settings are all in ```src/optimisation.py```


To run the brute force method, run the following command in the terminal: 

```cd src``` \
```python3 brute_force.py```

To change the objective and constraints, modify the file ```data/input_constraint.txt``` \
The test data is stored in ```test/test_results/``` \
To plot the results, the tools are provided in ```test/plot_tools/``` \ 
The corresponding plots are stored in ```test/plot_results/``` \


Current Progress
- Formatted Input Constraints
- Built a simple model
- Modified the model to be able to optimise for multiple-objectives
- Modified the model to be aware of the output constraints, making it able to find design with the output within a range.
- Implemented constraint interface.
- Implemented the brute force method to compare the efficiency of the model.
- Introduce Noise to the model to mitigate the discreteness problem.

TODO
- Examine the feasibility of converting the input discrete input to vector of continuous input though one-hot encoding. This will allow the model to be able to find the optimal solution within the discrete design space.
- Try to modify the Covariance Kernel to be able to handle the discrete input.
- Experiments in larger dataset.

Things to Improve
- Currently, the output constraints are considered as the last dimension of the objective functions.
- Discreteness problem, many samples map to the same outcomes, driving the model easily to the local optimum.