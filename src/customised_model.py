from botorch.models import SingleTaskGP
from gpytorch.distributions.multivariate_normal import MultivariateNormal
from utils import recover_categorical_input_data
import torch

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
    
    def discretinize_input_data(self, input_tensor):
        """This function is used to discretinize the input data, it is not used currently"""
        discretinized_input =  torch.round(input_tensor * self.rounding_factors) / self.rounding_factors
        return discretinized_input
    
    def Kernel_Transform(self, input_tensor):
        """This function is used to transform the input data to the kernel model"""
        tmp_input = recover_categorical_input_data(input_tensor, self.categorical_info)
        transformed_input = self.discretinize_input_data(tmp_input)
        return transformed_input

    def forward(self, x):
        # x = self.transform_inputs(x)
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(
            self.Kernel_Transform(x)
        )
        return MultivariateNormal(mean_x, covar_x)
    
