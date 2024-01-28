from scipy.stats import qmc
import torch
from utils import normalise_output_data

class initial_sampler:
    def __init__(self, input_dim, constraint_set=None, data_set=None, gen_type=torch.float, gen_device=torch.device('cpu')):    
        # self.dim_ranges = constraint_set.get_self_bounds()
        self.input_dim = input_dim
        # The reason to use this sampler is that it could guarantee to only generate unique points.
        self.sampler = qmc.Sobol(d=self.input_dim, scramble=True)
        self.constraint_set = constraint_set
        self.data_set = data_set
        self.type = gen_type
        self.device = gen_device

    def generate_samples(self, num_samples):
        # Generate samples
        samples = torch.tensor(self.sampler.random(n=num_samples), device=self.device, dtype=self.type)
        return samples
    
    def generate_valid_initial_data(self, num_samples,output_dim, data_set, obj_normalized_factors):
        """This function is used to generate valid initial data that meet the input constraints and also the output constraints"""
        train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
        exact_objs = torch.empty((num_samples, output_dim), device=self.device, dtype=self.type)
        con_objs = torch.empty((num_samples, 1), device=self.device, dtype=self.type)
        normalised_objs = torch.empty((num_samples, output_dim), device=self.device, dtype=self.type)
        valid_sample_index = 0
        possible_initial_tensor = self.generate_samples(num_samples)
        # print("possible_initial_tensor: ", possible_initial_tensor)
        for i in range(num_samples):
            if self.constraint_set.check_single_point_meet_constraint(possible_initial_tensor[i,:]) == False:
                continue
            # check internal constraints
            possible_obj = data_set.find_ppa_result(possible_initial_tensor[i:i+1,:], self.type)
            normalised_obj = normalise_output_data(possible_obj, obj_normalized_factors, self.device)
            con_obj = data_set.check_qNEHVI_constraints(normalised_obj)
            if con_obj.item() <= 0.0:
                train_x[valid_sample_index] = possible_initial_tensor[i,:]
                exact_objs[valid_sample_index] = possible_obj
                con_objs[valid_sample_index] = con_obj
                normalised_objs[valid_sample_index] = normalised_obj
                valid_sample_index += 1
        return train_x[:valid_sample_index + 1, : ], exact_objs[:valid_sample_index + 1, :], con_objs[:valid_sample_index + 1, :], normalised_objs[:valid_sample_index + 1, :]

