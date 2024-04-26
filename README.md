# FYP Bayesian Optimisation

This project is currently under development. The aim is to use Bayesian Optimisation to find the multi-objectives optimal solutions within the customised processor's design space.

## Prerequisite 

```git submodule init``` 

Do the modifications as shown in [Processor Setup](object_functions/README.md)

## Run the model

To run this code, run the following command in the terminal:

```cd src``` \
```python3 optimisation.py```

The model settings are all in ```src/optimisation.py```

To run the brute force method, run the following command in the terminal:

```cd src``` \
```python3 brute_force.py```

To change the objective and constraints, modify the file ```data/input_constraint.txt```

## Record Results

To record the results, change the record flag in ```optimisation.py``` to be true. The record data will be stored in ```test/test_results/```

To plot the results, the tools are provided in ```test/plot_tools/```

The corresponding plots are stored in ```test/plot_results/```

## Data Format

### Input Variables

To improve the performance of the model, the input variables are downscaled by their step size and then extracted by there offset. For example, if a variable is to select from [4, 8, 12, 16], the step size is 4, the offset is 4. The input variable is then scaled to [0, 1, 2, 3] and then extracted by the offset 4.

### Output Variables

To add the constraints to the objectives of the model, the train_obj is extended by one dimension to represent the validity of the design. The value of the last dimension is negative if the design is valid, positive otherwise.

Apart from that, the train_obj only considers the objectives that need to optimise and ignore te objectives for constraints purposes.

## Current Progress

- Formatted Input Constraints
- Built a simple model
- Modified the model to be able to optimise for multiple-objectives
- Modified the model to be aware of the output constraints, making it able to find design with the output within a range.
- Implemented constraint interface.
- Implemented the brute force method to compare the efficiency of the model.
- Apply transformation to the tensor for forward pass to the covariance kernel.
- Improve the initial Sampling method.
- Select the sample point to decide whether it shoud be integrated to the training set.
- Connect the model with the real customisable processor.
- Complete the overall optimisation flow.
- Enable the model to accept categorical variables.

## TODO

- Categorical Variable Kernel Optimisation.
- Invalid designs handling.

## Things to Improve

- Currently, the output constraints are considered as the last dimension of the objective functions.
- Discreteness problem, many samples map to the same outcomes, driving the model easily to the local optimum.
