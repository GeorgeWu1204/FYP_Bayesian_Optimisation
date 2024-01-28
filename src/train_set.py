import torch

class train_set_records():
    """This class is used to record the training set"""
    def __init__(self, normalised_factors, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        
        self.normalised_factor = torch.tensor(normalised_factors, dtype=tensor_type, device=tensor_device)
        self.acceptable_threshold = 0.0001
        self.history_record = {}
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device

    def recover_input_data_for_storage(self, input_tensor):
        """This function is to find the real input from the x tensor in recording process"""
        results = torch.round(input_tensor * self.normalised_factor)
        return results
    
    def normalise_input_data(self, input_tensor):
        """This function is to normalise the  rounded vertice"""
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
            self.history_record[recovered_train_x[i]] = [self.normalise_input_data(recovered_train_x[i])]
        
    def calculate_distance(self, x1, x2):
        """This function is used to calculate the distance between two points"""
        return torch.norm(x1 - x2)
    
    def add_disturb_to_data(self, data, disturb_factor):
        """This function is used to add disturb to the data"""
        return data + disturb_factor * torch.rand(data.shape, dtype=data.dtype, device=data.device)

    def store_new_data(self, new_train_x, new_train_y, new_hyper_vol):
        """This function is used to store the new data"""
        recovered_train_x = self.recover_input_data_for_storage(new_train_x)
        stored_samples = self.history_record.get(recovered_train_x, None)
        # if the new data is not in the history record
        if stored_samples == None:
            # if the new data is aways from the rounded vertice in the integer space, return together with the rounded vertice to improve the quality of the dataset 
            normalised_vertice = self.normalise_input_data(recovered_train_x)
            if self.calculate_distance(new_train_x, normalised_vertice).item() > self.acceptable_threshold:
                self.history_record[recovered_train_x] = [normalised_vertice, new_train_x]
                return torch.cat([new_train_x, normalised_vertice]), torch.cat([new_train_y, new_train_y]), torch.tensor([new_hyper_vol, new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device)
            self.history_record[recovered_train_x] = [new_train_x]
            return new_train_x, new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device)
        else:
            away_from_oter_samples = True
            for stored_sample in stored_samples:
                # if any point in the corresponding rounded vertice set, check if the new data is away from the other points in the set
                if self.calculate_distance(new_train_x, stored_sample).item() > self.acceptable_threshold:    
                    away_from_oter_samples = False
                    #TODOTODO
                    return self.add_disturb_to_data(new_train_x, self.acceptable_threshold), new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device) 
            # if the new data is away from the other points in the set, add the new data to the set
            if away_from_oter_samples:
                self.history_record[recovered_train_x].append(recovered_train_x)
                return new_train_x, new_train_y, torch.tensor([new_hyper_vol], dtype = self.tensor_type, device = self.tensor_device)
