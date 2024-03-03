import re
import subprocess
import os
import matplotlib.pyplot as plt
import numpy as np


def plot_benchmark_performance(data, parameter_names):
    """
    Plots a bar chart with multiple bars for each parameter across different benchmarks, 
    only including parameters that have results larger than zero for any of the benchmark performances.

    Parameters:
    - data: Dictionary with benchmark names as keys and arrays of performance values as values.
    - parameter_names: Array of parameter names corresponding to the performance values in the data.
    """
    # Filter parameters that have results larger than zero in any benchmark
    filtered_indices = [i for i, values in enumerate(zip(*data.values())) if any(v > 0 for v in values)]
    filtered_parameter_names = [parameter_names[i] for i in filtered_indices]
    filtered_data = {benchmark: [performances[i] for i in filtered_indices] for benchmark, performances in data.items()}
    
    # Number of benchmarks
    n_benchmarks = len(filtered_data)
    # Number of parameters
    n_parameters = len(filtered_parameter_names)
    
    # Setting the bar width
    bar_width = 0.8 / n_benchmarks
    
    # Setting the position of the bars on the x-axis
    r = np.arange(n_parameters)
    
    # Creating the figure and the axes
    fig, ax = plt.subplots(figsize=(25, 5))
    
    for i, (benchmark, performances) in enumerate(filtered_data.items()):
        # Calculate the position for each benchmark
        positions = [x + i * bar_width for x in r]
        
        # Plot the bars
        ax.bar(positions, performances, width=bar_width, label=benchmark)

    # Adding the parameter names as x-ticks
    ax.set_xticks([r + bar_width * (n_benchmarks / 2 - 0.5) for r in range(n_parameters)])
    ax.set_xticklabels(filtered_parameter_names)
    
    # Adding the legend
    ax.legend()

    # Adding labels and title
    plt.xlabel('Parameters')
    plt.ylabel('Performance')
    plt.title('Performance of Benchmarks across Different Parameters')

    # Show the plot
    plt.savefig('../Core_Design_Space/Performance_of_Benchmarks_across_Different_Parameters.png')


class Find_all_combinations_of_parameters:
    def __init__(self):
        self.tunable_params = {
            'ret_stack_size': [2, 3, 4, 5, 6, 7, 8],
            'btb_enable': [0, 1],
            'btb_fullya': [0, 1],
            'btb_size': [8, 16, 32, 64, 128, 256, 512],
            'bht_size': [32, 64, 128, 256, 512, 1024, 2048],
            'div_bit': [1, 2, 3, 4],
            'div_new': [0, 1],
            'dccm_enable': [0, 1],
            'dccm_num_banks': [2, 4],
            'dccm_region': [i for i in range(0x0, 0xf + 1)],  # Assuming continuous range from 0x0 to 0xf
            # 'dccm_offset': This requires specific handling due to its hexadecimal nature and alignment requirements
            'dccm_size': [4, 8, 16, 32, 48, 64, 128, 256, 512],  # Assuming the sizes are in kB
            'dma_buf_depth': [2, 4, 5],
            'fast_interrupt_redirect': [0, 1],
            'iccm_enable': [0, 1],
            'icache_enable': [0, 1],
            'icache_waypack': [0, 1],
            'icache_ecc': [0, 1],
            'icache_size': [8, 16, 32, 64, 128, 256],  # Assuming the sizes are in kB
            'icache_2banks': [0, 1],
            'icache_num_ways': [2, 4],
            'icache_bypass_enable': [0, 1],
            'icache_num_bypass': [i for i in range(1, 8 + 1)],
            'icache_num_tag_bypass': [i for i in range(1, 8 + 1)],
            'icache_tag_bypass_enable': [0, 1],
            'iccm_region': [i for i in range(0x0, 0xf + 1)],  # Assuming continuous range from 0x0 to 0xf
            # 'iccm_offset': This requires specific handling due to its hexadecimal nature and alignment requirements
            'iccm_size': [4, 8, 16, 32, 64, 128, 256, 512],  # Assuming the sizes are in kB
            'iccm_num_banks': [2, 4, 8, 16],
            'lsu_stbuf_depth': [2, 4, 8],
            'lsu_num_nbload': [2, 4, 8],
            'load_to_use_plus1': [0, 1],
            'pic_2cycle': [0, 1],
            'pic_region': [i for i in range(0x0, 0xf + 1)],  # Assuming continuous range from 0x0 to 0xf
            # 'pic_offset': This requires specific handling due to its hexadecimal nature and alignment requirements
            'pic_size': [32, 64, 128, 256],  # Assuming the sizes are in kB
            'pic_total_int': [i for i in range(1, 255 + 1)],
            'timer_legal_en': [0, 1],
            'bitmanip_zba': [0, 1],
            'bitmanip_zbb': [0, 1],
            'bitmanip_zbc': [0, 1],
            'bitmanip_zbe': [0, 1],
            'bitmanip_zbf': [0, 1],
            'bitmanip_zbp': [0, 1],
            'bitmanip_zbr': [0, 1],
            'bitmanip_zbs': [0, 1],
            'fpga_optimize': [0, 1],
            'text_in_iccm': [0, 1],
            'pmp_entries': [0, 16, 64]
        }
        self.generation_path = '../Cores-VeeR-EL2'      # Path to execute the generation command
        self.generated_logfile = '../Logs/'
        self.benchmarks = ['hello_world', 'cmark', 'pmp', 'dhry']
        self.benchmark_minstret =  {'hello_world': 329, 'cmark': 282995, 'pmp': 181441, 'dhry': 343110}

    def find_and_record_all_combinations_of_single_param(self):
        for param_name in self.tunable_params.keys():
            print(f"Testing parameter: {param_name}")
            print(f"Possible values: {self.tunable_params[param_name]}")
            print(f"Benchmark: {self.benchmarks}")
            path = '../Core_Design_Space/' + param_name
            with open(path + '.txt', 'w') as f:
                f.write(f"{param_name}")
                for benchmark in self.benchmarks:
                    f.write(f", {benchmark}_minstret, {benchmark}_mcycle")
                f.write('\n')
                for value in self.tunable_params[param_name]:
                    f.write(f"{value}")
                    for benchmark in self.benchmarks:
                        valid, minstret, mcycle = self.tune_and_run_performance_simulation_for_single_param(param_name, value, benchmark)
                        if valid:
                            f.write(f", {minstret}, {mcycle}")
                        else:
                            f.write(f", Invalid, Invalid")
                    f.write('\n')

    def find_and_record_all_combinations_of_all_params_of_additional_benchmarks(self, append_benchmarks):
        for param_name in self.tunable_params.keys():
            print(f"Testing parameter: {param_name}")
            print(f"Possible values: {self.tunable_params[param_name]}")
            print(f"Additional Benchmark: {append_benchmarks}")
            path = '../Core_Design_Space/' + param_name
            copy_path = '../Core_Design_Space/Copy/' + param_name
            modified_lines = []
            with open(copy_path + '.txt', 'r') as file:
                lines = file.readlines()
                modified_line = lines[0].strip('\n')
                for benchmark in append_benchmarks:
                    modified_line += f", {benchmark}_minstret, {benchmark}_mcycle"
                modified_lines.append(modified_line)
                line_index = 1
                for value in self.tunable_params[param_name]:
                    modified_line = lines[line_index]
                    modified_line = modified_line.strip('\n')
                    for benchmark in append_benchmarks:
                        valid, minstret, mcycle = self.tune_and_run_performance_simulation_for_single_param(param_name, value, benchmark)
                        if valid:
                            modified_line += f", {minstret}, {mcycle}"
                        else:
                            modified_line += f", Invalid, Invalid"
                    modified_lines.append(modified_line)
                    line_index += 1
            print(modified_lines)
            
            with open(path + '.txt', 'w') as file:
                for line in modified_lines:
                    # Write each modified line back to the file with a newline character at the end
                    file.write(line + '\n')
           
        
    def tune_and_run_performance_simulation_for_single_param(self, param_name, param_value, benchmark):
        try:
            # Expand the environment variable
            rv_root = os.environ.get('RV_ROOT', '')  # Default to an empty string if RV_ROOT is not set
            if not rv_root:
                print("RV_ROOT environment variable is not set.")
                return False, None, None
            target = 'TEST=' + benchmark
            param_setting = 'CONF_PARAMS=\''
            param_setting+= '-set={param}={value} '.format(param=param_name, value=param_value)  
            param_setting += '\''
            print(param_setting)
            print(target)
            command = ['make', '-f', os.path.join(rv_root, 'tools/Makefile'), target, param_setting]
            # Prepare the command with the expanded environment variable
            # Run the 'make' command in the directory where the Makefile is located
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.generation_path, stdout=f, stderr=f)
            minstret, mcycle = self.extract_minstret_mcycle(self.generated_logfile + 'Processor_Generation.log')
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None, None
    


    def extract_minstret_mcycle(self, log_file_path):
        """
        Extracts minstret and mcycle values from a log file.
        """
        # Regular expression to match the specific line and capture minstret and mcycle values
        pattern = r'Finished : minstret = (\d+), mcycle = (\d+)'

        # Initialize variables to store the extracted values
        minstret = None
        mcycle = None

        # Open the log file and read line by line
        try:
            with open(log_file_path, 'r') as file:
                for line in file:
                    # Search for the pattern in each line
                    match = re.search(pattern, line)
                    # If a match is found, extract the values
                    if match:
                        minstret = int(match.group(1))
                        mcycle = int(match.group(2))
                        # Break the loop after finding the first match
                        break
        except FileNotFoundError:
            print(f"Error: The file {log_file_path} was not found.")
            return None, None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None, None
        return minstret, mcycle
    
    def plot_design_space_of_single_param(self, parameter_name):
        with open('../Core_Design_Space/' + parameter_name + '.txt', 'r') as f:
            lines = f.readlines()
            lines = lines[1:]
            results = {benchmark: [] for benchmark in self.benchmarks}
            input_var = {benchmark: [] for benchmark in self.benchmarks}
            for line in lines:
                values = line.split(',')
                for i in range(len(self.benchmarks)):
                    if values[2*i+1] == ' Invalid' or values[2*i+1] == ' None':
                        continue
                    results[self.benchmarks[i]].append((int(values[2*i+2])))
                    input_var[self.benchmarks[i]].append(int(values[0]))
        plt.figure(figsize=(18, 4))
        for i in range(len(self.benchmarks)):
            plt.subplot(1, 3, i+1)
            plt.plot(input_var[self.benchmarks[i]], results[self.benchmarks[i]])
            plt.xlabel(parameter_name)
            plt.ylabel(self.benchmarks[i] + ' Performance')
        plt.savefig('../Core_Design_Space/Individual_Plots/' + parameter_name + '.png')
    
    def plot_design_space_parameters(self):
        for param_name in self.tunable_params.keys():
            self.plot_design_space_of_single_param(param_name)
    
    def extract_min_max_of_params(self):
        difference_in_benchmark_performance = {benchmark: [] for benchmark in self.benchmarks}

        for param_name in self.tunable_params.keys():
            with open('../Core_Design_Space/' + param_name + '.txt', 'r') as f:
                lines = f.readlines()
                lines = lines[1:]
                results = {benchmark: [] for benchmark in self.benchmarks}

                for line in lines:
                    values = line.split(',')
                    for i in range(len(self.benchmarks)):
                        if values[2*i+1] == ' Invalid' or values[2*i+1] == ' None':
                            continue
                        results[self.benchmarks[i]].append((int(values[2*i+2])))
                
                for benchmark in self.benchmarks:
                    if len(results[benchmark]) > 0:
                        difference_in_benchmark_performance[benchmark].append((max(results[benchmark]) - min(results[benchmark]))/(self.benchmark_minstret[benchmark]))
                        print(f"Parameter: {param_name}, Benchmark: {benchmark}, Difference: {difference_in_benchmark_performance[benchmark][-1]}")
                    else:
                        print(f"Parameter: {param_name}, Benchmark: {benchmark}, No valid results")
                        difference_in_benchmark_performance[benchmark].append(0)
        plot_benchmark_performance(difference_in_benchmark_performance, list(self.tunable_params.keys()))
if __name__ == '__main__':
    pt = Find_all_combinations_of_parameters()
    pt.extract_min_max_of_params()
    # pt.find_and_record_all_combinations_of_single_param()
    # pt.find_and_record_all_combinations_of_all_params_of_additional_benchmarks(['dhry'])