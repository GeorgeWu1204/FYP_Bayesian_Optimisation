def find_max_objectives(dataset):
    max_objectives = {}
    for point in dataset.__dict__.keys():
        for obj in dataset[point].PPA:
            if obj not in max_objectives:
                max_objectives[obj] = dataset[point].PPA[obj]
            else:
                if dataset[point].PPA[obj] > max_objectives[obj]:
                    max_objectives[obj] = dataset[point].PPA[obj]
    return max_objectives