from scipy.stats import qmc
import torch
from utils import normalise_output_data
import time

class initial_sampler:
    def __init__(self, input_dim, output_dim, constraint_set=None, data_set=None, gen_type=torch.float, gen_device=torch.device('cpu')):
        self.input_dim = input_dim
        self.constraint_set = constraint_set
        self.data_set = data_set
        self.type = gen_type
        self.device = gen_device
        self.sample_counter = 0  # Introduce a sample counter to add variability to the seed
        self.output_dim = output_dim

    def generate_samples(self, num_samples):
        # Dynamic seeding mechanism: combine time and sample counter
        seed = int(time.time()) + self.sample_counter
        self.sample_counter += 1  # Increment counter to ensure different seeds in successive calls
        
        self.sampler = qmc.Sobol(d=self.input_dim, scramble=True, seed=seed)
        
        # Generate samples
        samples = torch.tensor(self.sampler.random(n=num_samples), device=self.device, dtype=self.type)
        return samples
    
    def generate_valid_initial_data(self, num_samples, data_set, obj_normalized_factors):
        """This function is used to generate valid initial data that meet the input constraints and also the output constraints"""
        train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
        exact_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
        con_objs = torch.empty((num_samples, 1), device=self.device, dtype=self.type)
        normalised_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
        valid_sample_index = 0
        # print("possible_initial_tensor: ", possible_initial_tensor)
        while (valid_sample_index) <= int(num_samples/2):
            possible_initial_tensor = self.generate_samples(num_samples)
            for i in range(num_samples):
                if self.constraint_set.check_single_point_meet_constraint(possible_initial_tensor[i,:]) == False:
                    continue
                if any(possible_initial_tensor[i,:] < 0) or any(possible_initial_tensor[i,:] > 1):
                    print("possible_initial_tensor[i,:]: ", possible_initial_tensor[i,:])
                    quit()
                # check internal constraints
                valid_sample, possible_obj = data_set.find_ppa_result(possible_initial_tensor[i:i+1,:])
                # if the generated desgin does not meet the internal constraints that are not disclosed in the spec.
                if valid_sample == False:
                    continue
                normalised_obj = normalise_output_data(possible_obj, obj_normalized_factors, self.device)
                con_obj = data_set.check_qNEHVI_constraints(normalised_obj)
                if con_obj.item() <= 0.0:
                    train_x[valid_sample_index] = possible_initial_tensor[i,:]
                    exact_objs[valid_sample_index] = possible_obj
                    con_objs[valid_sample_index] = con_obj
                    normalised_objs[valid_sample_index] = normalised_obj
                    valid_sample_index += 1
                    if valid_sample_index >= num_samples:
                        return train_x, exact_objs, con_objs, normalised_objs


        return train_x[:valid_sample_index, : ], exact_objs[:valid_sample_index, :], con_objs[:valid_sample_index, :], normalised_objs[:valid_sample_index, :]

    def generate_initial_data(self, num_samples):
        """This function is used to generate initial data"""
        train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
        valid_sample_index = 0
        # print("possible_initial_tensor: ", possible_initial_tensor)
        while (valid_sample_index) <= int(num_samples/2):
            possible_initial_tensor = self.generate_samples(num_samples)
            for i in range(num_samples):
                if self.constraint_set.check_single_point_meet_constraint(possible_initial_tensor[i,:]) == False:
                    continue
                if any(possible_initial_tensor[i,:] < 0) or any(possible_initial_tensor[i,:] > 1):
                    print("possible_initial_tensor[i,:]: ", possible_initial_tensor[i,:])
                    quit()
                train_x[valid_sample_index] = possible_initial_tensor[i,:]
                valid_sample_index += 1
                if valid_sample_index >= num_samples:
                    return train_x
        return train_x


        return train_x[:valid_sample_index, : ], exact_objs[:valid_sample_index, :], con_objs[:valid_sample_index, :], normalised_objs[:valid_sample_index, :]
