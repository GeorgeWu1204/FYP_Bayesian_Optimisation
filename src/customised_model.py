from botorch.models import SingleTaskGP
from gpytorch.distributions.multivariate_normal import MultivariateNormal
import torch


# kernel transformation mapping

# def categorical_kernel_transformation(categorical_info, input_tensor):
#     """This function is used to transform the input tensor to a new tensor with categorical values"""
#     transformed_tensor = input_tensor.clone()
#     for var_name in categorical_info.keys():
#         index, _, categorical_vals = categorical_info[var_name]
#         transformed_tensor[:, index] = torch.tensor(list(map(lambda x: categorical_vals[int(x)], input_tensor[:, index].tolist())), dtype=torch.float64)
#     return transformed_tensor

def discretinize_input_data(input_tensor, rounding_factors):
    """This function is used to discretinize the input data, it is not used currently"""
    discretinized_input =  torch.round(input_tensor * rounding_factors) / rounding_factors
    return discretinized_input

class SingleTaskGP_transformed(SingleTaskGP):
    """
    version of SingleTaskGP where input data to kernel model is transformed
    """

    def __init__(
        self, scales, normalised_factors, categorical_info, train_X, train_Y, likelihood=None, outcome_transform=None, tensor_type=torch.float64, tensor_device=torch.device('cpu')
    ):
        super().__init__(train_X=train_X, train_Y=train_Y, likelihood=likelihood, outcome_transform=outcome_transform)
        self.rounding_factors = torch.tensor(list(map(lambda x, y: x * y, scales, normalised_factors)), dtype=tensor_type, device=tensor_device)
        self.categorical_info = categorical_info
    def forward(self, x):
        # x = self.transform_inputs(x)
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(
            discretinize_input_data(x, self.rounding_factors)
        )
        return MultivariateNormal(mean_x, covar_x)
    
