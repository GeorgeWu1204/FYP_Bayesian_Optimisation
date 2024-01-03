# FYP_Bayesian_Optimisation

This project is currently under development. The aim is to use Bayesian Optimisation to find the multi-objectives optimal solutions within the customised processor's design space.

To run this code, run the following command in the terminal: 

```cd src```
```python3 optimisation.py```

To run the brute force method, run the following command in the terminal: 

```cd src```
```python3 brute_force.py```

To change the objective and constraints, modify the file ```data/input_constraint.txt```
The test data is stored in ```test/test_results/```
The corresponding plots are stored in ```test/plot_results/```


Current Progress
- Formatted Input Constraints
- Built a simple model
- Modified the model to be able to optimise for multiple-objectives
- Modified the model to be aware of the output constraints, making it able to find design with the output within a range.
- Implemented constraint interface.

TODO
- Further optimise the efficiency of the model.
- Experiments in larger dataset.

Things to Improve
- Currently, the output constraints are considered as the last dimension of the objective functions.
