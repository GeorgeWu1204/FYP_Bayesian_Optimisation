import ast
import utils

# Read the file
def read_from_data(file_name):
    with open(file_name, 'r') as f:
        content = f.read()
        raw_data = ast.literal_eval(content)
        data_set = utils.Data_Set(raw_data)
    return data_set


if __name__ == '__main__':
<<<<<<< Updated upstream:data.py
    data_set = read_from_data('ppa.txt')
    print(data_set.find_BTB_constraints(4))
=======
    data_set = read_from_data('../ppa.txt')
    data_set.find_ppa_result({'Pre_Type': 2, 'BTB': 4})
>>>>>>> Stashed changes:src/data.py
