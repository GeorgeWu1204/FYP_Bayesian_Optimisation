
class Data_Sample:
    def __init__(self, data, obj):
        self.Constraints = data[0]
        self.Cycle_count = data[1]
        self.PPA = data[2][obj]
    def print_constraints(self):
        print("Constraints:")
        for k, v in self.Constraints.items():
            print(f"{k} = {v}")

    def print_cycle_count(self):
        print("Cycle count:")
        for k, v in self.Cycle_count.items():
            print(f"{k} = {v}")
    
    def print_ppa(self):
        print("PPA:")
        for k, v in self.PPA.items():
            print(f"{k} = {v}")

class Data_Set:
    def __init__(self, data, input_constraints):
        # self.data_net = [[0]*n for _ in range(m)]

        for i in range(len(data)):
            self.__dict__[i] = Data_Sample(data[i])
    
    def __len__(self):
        return len(self.__dict__)
    
    def list_all_contraints(self):
        constraints = []
        for i in range(len(self)):
            constraints.append(self.__dict__.get(i).Constraints)
        return constraints
    
    def find_BTB_constraints(self, constraint):
        Pre_Type = []
        for i in range(len(self)):
            tmp_constraint = self.__dict__.get(i).Constraints
            if tmp_constraint['BTB'] == constraint:
                Pre_Type.append(tmp_constraint['Pre_Type'])
        return Pre_Type
    
    def find_Pre_Type_constraints(self, constraint):
        BTB = []
        for i in range(len(self.__dict__)):
            tmp_constraint = self.__dict__.get(i).Constraints
            if tmp_constraint['Pre_Type'] == constraint:
                BTB.append(tmp_constraint['BTB'])
        return BTB
    
    def find_ppa_result(self, constraints):
        PPA = []
        for i in range(len(self)):
            print("Checking:", self.__dict__.get(i).Constraints)
            tmp_constraint = self.__dict__.get(i).Constraints
            if tmp_constraint == constraints:
                PPA.append(self.__dict__.get(i).PPA)
                print("New PPA found!")
                print("PPA:", self.__dict__.get(i).PPA)
        return PPA
    


    
