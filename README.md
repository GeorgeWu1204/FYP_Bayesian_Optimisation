# FYP_Bayesian_Optimisation

This project is currently under development. The aim is to use Bayesian Optimisation to find the multi-objectives optimal solutions within the customised processor's design space.

To run this code, run the following command in the terminal: 

```python3 src/optimisation.py```

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
- The multiple-objectives optimisation now takes every objective as the same weight. This is not ideal as some objectives are more important than others.
- Regarding the normalisation of the objective, not sure if it is correct to normalised as x/(a-b) for [a, b], considering the ref_points.
