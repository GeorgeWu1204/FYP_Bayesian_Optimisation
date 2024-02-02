import torch

class train_set_records():
    """This class is used to record the training set"""
    def __init__(self, normalised_factors, acceptable_threshold = 0.0001, disturbance_threshold = 0.0001, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        
        self.normalised_factor = torch.tensor(normalised_factors, dtype=tensor_type, device=tensor_device)
        self.acceptable_threshold = acceptable_threshold
        print("Acceptable threshold for train_set similarity is ", self.acceptable_threshold)
        self.disturbance_threshold = disturbance_threshold
        self.history_record = {}
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.samples_amount_threshold = 5

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

    def store_initial_data(self, train_x):
        """This function is used to store the initial data"""
        self.reset_storage()
        train_set_size = train_x.shape[0]
        recovered_train_x = self.recover_input_data_for_storage(train_x)
        for i in range(train_set_size):
            self.history_record[self.convert_tensor_to_tuple(recovered_train_x[i])] = [self.normalise_input_data(recovered_train_x[i])]
        
    def calculate_distance(self, x1, x2):
        """This function is used to calculate the distance between two points"""
        return torch.norm(x1 - x2)
    
    def add_disturb_to_data(self, data):
        """This function is used to add disturb to the data"""
        return torch.abs(data + self.disturbance_threshold * (torch.rand(data.shape, dtype = self.tensor_type, device = self.tensor_device) * 2 - 1))

    def store_new_data(self, new_train_x, new_train_y, new_hyper_vol):
        """This function is used to store the new data"""
        recovered_train_x = self.recover_input_data_for_storage(new_train_x)
        stored_samples = self.history_record.get(self.convert_tensor_to_tuple(recovered_train_x.squeeze()), None)
        # if the new data is not in the history record
        if stored_samples == None:
            # if the new data is aways from the rounded vertex  in the integer space, return together with the rounded vertex  to improve the quality of the dataset 
            normalised_vertex  = self.normalise_input_data(recovered_train_x)
            print("Distance is ", self.calculate_distance(new_train_x, normalised_vertex ).item())
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
                potential_valid_point = train_x_with_disturb
                # if the new data is close to the other points in the set, add disturb to the new data until it is away from the other points in the set and gurantee that the new data could be rouhnded to the corresponding vertex 
                while (self.calculate_distance(train_x_with_disturb, stored_sample).item() < self.acceptable_threshold) and (self.recover_input_data_for_storage(train_x_with_disturb) == recovered_train_x).all():    
                    return False, None, None, None
                    # train_x_with_disturb = self.add_disturb_to_data(potential_valid_point)
                    # print("after adding the distrubance, modified train_x_with_disturb is ", train_x_with_disturb)
            self.history_record[self.convert_tensor_to_tuple(recovered_train_x.squeeze())].append(train_x_with_disturb)
            return True, train_x_with_disturb, new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device) 
           

            
