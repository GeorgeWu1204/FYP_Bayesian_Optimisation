import torch
import numpy as np
from itertools import product
from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
from utils import calculate_hypervolume, recover_categorical_input_data

class train_set_records():
    """This class is used to record the training set"""
    def __init__(self, normalised_factors, self_constraints, categorical_info, worst_ref_objective, objective_to_optimise_dim, train_set_modification_enable, acceptable_threshold = 0.0001, disturbance_threshold = 0.0001, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        
        self.normalised_factor = torch.tensor(normalised_factors, dtype=tensor_type, device=tensor_device)
        self.acceptable_threshold = acceptable_threshold
        self.disturbance_threshold = disturbance_threshold
        self.history_record = {}
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.samples_amount_threshold = 5
        self.neighbour_dist = 1
        self.self_constraint = self_constraints
        self.categorical_info = categorical_info
        self.worst_ref_objective = worst_ref_objective
        self.fake_worst_point = torch.tensor(worst_ref_objective.tolist() + [0.0], dtype = tensor_type, device = tensor_device).unsqueeze(0)
        self.objective_to_optimise_dim = objective_to_optimise_dim
        self.train_set_modification_enable = train_set_modification_enable

    def recover_input_data_for_storage(self, input_tensor):
        """This function is to find the real input from the x tensor in recording process"""
        results = torch.round(input_tensor * self.normalised_factor)
        return results
    
    def convert_tensor_to_tuple(self, input_tensor):
        """This function is to convert the tensor to tuple to make it hashable"""
        return tuple(input_tensor.tolist())
    
    def normalise_input_data(self, input_tensor):
        """This function is to normalise the  rounded vertex """
        return input_tensor / self.normalised_factor

    def reset_storage(self):
        """This function is used to reset the storage"""
        self.history_record = {}

    def get_close_neighbours(self, input_tensor):
        """This function is used to get the close neighbours"""
        recovered_input_tensor = self.convert_tensor_to_tuple(input_tensor.squeeze())
        close_neighbours = []
        ranges = [range(max(1, int(np.floor(x - self.neighbour_dist))), int(np.ceil(x + self.neighbour_dist)) + 1) for x in recovered_input_tensor]
        # Generate all possible points within the ranges
        possible_points = list(product(*ranges))
        # Filter points based on Euclidean distance and positivity
        for point in possible_points:
            if all(coord > 0 for coord in point):  # Check for positive coordinates
                if all(self.self_constraint[i][0] < coord < self.self_constraint[i][1] for i, coord in enumerate(point)):  # Check for coordinates within the constraint
                    distance = np.linalg.norm(np.array(point) - np.array(recovered_input_tensor))
                    if distance <= self.neighbour_dist:
                        close_neighbours.append(tuple(point))
        return close_neighbours

    def store_initial_data(self, train_x):
        """This function is used to store the initial data"""
        self.reset_storage()
        train_set_size = train_x.shape[0]
        recovered_train_x = recover_categorical_input_data(train_x, self.categorical_info)
        for i in range(train_set_size):
            recovered_sample = self.convert_tensor_to_tuple(recovered_train_x[i])
            if self.history_record.get(recovered_sample, None) == None:
                self.history_record[recovered_sample] = [recovered_train_x[i]]
            else:
                possible_neighbor =  self.get_close_neighbours(recovered_train_x[i])
                valid_initial_data = True
                for neighbour in possible_neighbor:
                    if self.history_record.get(neighbour, None) != None:
                        neighbour_samples = self.history_record[neighbour]
                        for sample in neighbour_samples:
                            if self.calculate_distance(recovered_train_x[i], sample) < self.acceptable_threshold:
                                valid_initial_data = False
                                break
                if valid_initial_data:
                    self.history_record[recovered_sample].append(recovered_train_x[i])
        
    def calculate_distance(self, x1, x2):
        """This function is used to calculate the distance between two points"""
        return torch.norm(x1 - x2)
    
    def add_disturb_to_data(self, data):
        """This function is used to add disturb to the data"""
        return torch.abs(data + self.disturbance_threshold * (torch.rand(data.shape, dtype = self.tensor_type, device = self.tensor_device) * 2 - 1))

    def store_new_data(self, valid_sample, new_train_x, new_train_y, new_hyper_vol, dataset):
        """This function is used to store the new data"""
        if self.train_set_modification_enable == False:
            return True, new_train_x, new_train_y, new_hyper_vol
        recovered_train_x = self.recover_input_data_for_storage(new_train_x)
        if valid_sample == True:
            # find all the stored samples that are close to the new data
            stored_samples = self.history_record.get(self.convert_tensor_to_tuple(recovered_train_x.squeeze()), None)
            # if the new data is not in the history record
            if stored_samples == None:
                # if the new data is aways from the rounded vertex  in the integer space, return together with the rounded vertex  to improve the quality of the dataset 
                normalised_vertex  = self.normalise_input_data(recovered_train_x)
                # if self.calculate_distance(new_train_x, normalised_vertex ).item() > self.acceptable_threshold:
                #     self.history_record[self.convert_tensor_to_tuple(recovered_train_x.squeeze())] = [normalised_vertex , new_train_x]
                #     return True,torch.cat([new_train_x, normalised_vertex ]), torch.cat([new_train_y, new_train_y]), torch.tensor([new_hyper_vol, new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device)
                self.history_record[self.convert_tensor_to_tuple(recovered_train_x.squeeze())] = [new_train_x]
                return True, new_train_x, new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device)
            else:
                if len(stored_samples) > self.samples_amount_threshold:
                    return False, None, None, None
                train_x_with_disturb = new_train_x
                for stored_sample in stored_samples:
                    ### if any point in the corresponding rounded vertex  set, check if the new data is away from the other points in the set
                    # potential_valid_point = train_x_with_disturb
                    # if the new data is close to the other points in the set, add disturb to the new data until it is away from the other points in the set and gurantee that the new data could be rouhnded to the corresponding vertex 
                    # while (self.calculate_distance(train_x_with_disturb, stored_sample).item() < self.acceptable_threshold) and (self.recover_input_data_for_storage(train_x_with_disturb) == recovered_train_x).all():      
                        # train_x_with_disturb = self.add_disturb_to_data(potential_valid_point)
                        # print("after adding the distrubance, modified train_x_with_disturb is ", train_x_with_disturb)
                    if self.calculate_distance(train_x_with_disturb, stored_sample).item() < self.acceptable_threshold:
                        print("The new data is too close to the other points in the set")
                        return False, None, None, None
                self.history_record[self.convert_tensor_to_tuple(recovered_train_x.squeeze())].append(train_x_with_disturb)
                return True, train_x_with_disturb, new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device) 
        else:
            neighbour_samples = self.get_close_neighbours(recovered_train_x)
            # print("recovered_train_x: ", recovered_train_x)
            # print("neighbour_samples: ", neighbour_samples)
            # neighbour_tensor = torch.empty((1, len(self.self_constraints)), dtype = self.tensor_type, device = self.tensor_device)
            for neighbour in neighbour_samples:
                neighbour_tensor = torch.tensor(neighbour, dtype = self.tensor_type, device = self.tensor_device)
                valid_neighbour, neighbor_obj = dataset.find_ppa_result(neighbour_tensor.unsqueeze(0))
                if valid_neighbour:
                    normalised_obj = dataset.normalise_output_data_tensor(neighbor_obj, self.obj_normalized_factors, self.tensor_device)
                    con_obj = dataset.check_obj_constraints(normalised_obj)
                    if con_obj.item() <= 0.0:
                        return True, neighbour_tensor, neighbor_obj, torch.tensor([calculate_hypervolume(self.worst_ref_objective, neighbor_obj, self.objective_to_optimise_dim)], dtype = self.tensor_type, device = self.tensor_device)

            
            return True, recovered_train_x, self.fake_worst_point, torch.tensor([0.0], dtype = self.tensor_type, device = self.tensor_device)
                

           

            
