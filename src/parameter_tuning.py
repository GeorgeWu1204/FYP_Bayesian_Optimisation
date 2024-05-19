import re
import subprocess
import os
import shutil

class NutShell_parameter_tuning:
    def __init__(self, tunable_params, shift_amount, settings_file, generation_path, vivado_project_path, board_settings):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.settings_file = settings_file          # Path to the Scala settings file
        self.board_settings = board_settings        # Name of the Scala object containing the settings
        self.generation_path = generation_path      # Path to the directory where the Makefile is located
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/run_synthesis.tcl'
        self.ssh_address = 'george@192.168.129.128'
        self.ssh_password = '001204'
        self.bash_file_path = 'run_on_remote_site.sh'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../object_functions/Syn_Report/'
        self.stored_report_directory = '../object_functions/Syn_Report/dynamic_set/'
        self.generated_filename = 'NutShell_utilization_synth.rpt'
        self.generated_logfile = '../object_functions/Logs/'

    def tune_parameter(self, new_value):
        '''Tune the parameters in the Scala settings file.'''
        # Read the Scala file
        with open(self.settings_file, 'r') as file:
            scala_content = file.read()

        # Define a pattern to find the board settings object and its parameters
        object_pattern = re.compile(r'object ' + re.escape(self.board_settings) + r' \{(.+?)\}', re.DOTALL)
        
        # Find the board settings object in the content
        match = object_pattern.search(scala_content)
        if not match:
            raise ValueError(f"Board settings object '{self.board_settings}' not found in the Scala file.")

        # Extract the object content
        object_content = match.group(1)
        modified_object_content = object_content

        # Define a pattern to find and replace the specific parameter within the object
        for index in range(len(self.tunable_params)):
            def replacement_function(match):
                base_part = match.group(1)
                original_format = match.group(2)
                # Determine if the original value ends with 'L'
                has_L_suffix = original_format.endswith('L')
                # Calculate the new value after shifting
                shifted_value = round(new_value[index]) << self.shift_amount[index]
                # Format the new value according to the original format
                if has_L_suffix:
                    new_value_formatted = f'0x{shifted_value:X}L'
                else:
                    new_value_formatted = f'{shifted_value}'
                return f'{base_part}{new_value_formatted}'

            param_pattern = re.compile(r'(\"' + re.escape(self.tunable_params[index]) + r'\"\s*->\s*)(0x[0-9a-fA-F]+L?|\d+)', re.DOTALL)
        
            # Replace the parameter value within the object content
            modified_object_content, n = param_pattern.subn(replacement_function, modified_object_content)
            if n == 0:
                raise ValueError(f"Parameter '{self.tunable_params[index]}' not found in board settings object '{self.board_settings}'.")

        # Replace the old object content with the modified one in the scala content
        modified_scala_content = scala_content[:match.start(1)] + modified_object_content + scala_content[match.end(1):]

        # Write the modified content back to the Scala file
        with open(self.settings_file, 'w') as file:
            file.write(modified_scala_content)
        

    def regenerate_design_locally(self):
        # considering the case that in the current environment, the design could be directly regenerated by running the 'make' command
        '''Regenerate the design using the new parameters.'''
        try:
            # Run the 'make' command in the directory where the Makefile is located
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(['make', 'clean'], check=True, cwd=self.generation_path, stdout=f, stderr=f)
                subprocess.run(['make', 'verilog', 'BOARD=PXIe'], check=True, cwd=self.generation_path, stdout=f, stderr=f)
            return True
        except subprocess.CalledProcessError as e:
            return False

    def regenerate_design_by_virtual_machine(self):
        # Ensure ssh_address is in the format 'user@host'
        # Ensure bash_file_path is the correct path to the bash file on the remote machine
        # Command to execute the bash file remotely
        bash_command = f'bash {self.bash_file_path}'
        
        # Full SSH command as a single string
        ssh_command = f'ssh {self.ssh_address} "{bash_command}"'
        
        # Execute the command using subprocess
        try:
            # When using shell=True, the command should be a single string
            result = subprocess.run(ssh_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Bash file executed successfully. Output:")
            print(result.stdout.decode())  # Printing the output of the bash command
        except subprocess.CalledProcessError as e:
            print("An error occurred while executing the bash file.")
            print(e.stderr.decode())  # Printing the error output
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile + 'Synthesis.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
    
    def store_synthesis_report(self):
        '''Store the synthesis report in a file.'''
        name, extension = os.path.splitext(self.generated_filename)
        new_name = name + '_' + str(self.generated_report_num) + extension
        shutil.copy(self.generated_report_directory + self.generated_filename, self.stored_report_directory + new_name)
        self.generated_report_num += 1
    


class EL2_parameter_tuning:
    """This is the tuner for EL2 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.generation_path = generation_path      # Path to execute the generation command
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/EL2/run_EL2_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../object_functions/Syn_Report/'
        self.stored_report_directory = '../object_functions/Syn_Report/dynamic_set/'
        self.generated_filename = 'EL2_utilization_synth.rpt'
        self.generated_logfile = '../object_functions/Logs/'
        
    def tune_and_run_performance_simulation(self, new_value, benchmark):
        try:
            # Expand the environment variable
            rv_root = os.environ.get('RV_ROOT', '')  # Default to an empty string if RV_ROOT is not set
            if not rv_root:
                print("RV_ROOT environment variable is not set.")
                return False, None, None
            target = 'TEST=' + benchmark
            param_setting = 'CONF_PARAMS='
            for index, param in enumerate(self.tunable_params):
                if type(new_value[index]) == str:
                    # if the value is categorical
                    value = new_value[index]
                else:
                    value = str(round(new_value[index]) << self.shift_amount[index])
                param_setting+= '-set={param}={value} '.format(param=param, value=value)  
            param_setting += ''
            command = ['make', '-f', os.path.join(rv_root, 'tools/Makefile'), target, param_setting]
            # print(command)
            # Prepare the command with the expanded environment variable
            # Run the 'make' command in the directory where the Makefile is located
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
            minstret, mcycle = self.extract_minstret_mcycle(self.generated_logfile + 'Processor_Generation.log')
            if mcycle is None:
                return False, None, None
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None, None
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile + 'Synthesis.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
    
    def store_synthesis_report(self):
        '''Store the synthesis report in a file.'''
        name, extension = os.path.splitext(self.generated_filename)
        new_name = name + '_' + str(self.generated_report_num) + extension
        shutil.copy(self.generated_report_directory + self.generated_filename, self.stored_report_directory + new_name)
        self.generated_report_num += 1


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
    
# class CVA6_parameter_tuning:
#     """This is the tuner for CVA6 Cores, it could automatically customise the processor according to the param settings"""
#     def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
#         super().__init__(tunable_params, shift_amount, generation_path, vivado_project_path)


class SCR1_parameter_tuning:
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.generation_path = generation_path      # Path to execute the generation command
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/scr1/run_scr1_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../object_functions/Syn_Report/'
        self.stored_report_directory = '../object_functions/Syn_Report/dynamic_set/'
        self.generated_filename = 'scr1_utilization_synth.rpt'
        self.generated_logfile = '../object_functions/Logs/'
        self.configuration_file = '/home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/scr1/src/includes/scr1_arch_description.svh'

    def tune_and_run_performance_simulation(self, new_value, benchmark):
        try:
            # Expand the environment variable
            rv_root = os.environ.get('RV_ROOT', '')  # Default to an empty string if RV_ROOT is not set
            if not rv_root:
                print("RV_ROOT environment variable is not set.")
                return False, None, None
            target = 'TEST=' + benchmark
            param_setting = 'CONF_PARAMS='
            for index, param in enumerate(self.tunable_params):
                if type(new_value[index]) == str:
                    # if the value is categorical
                    value = new_value[index]
                else:
                    value = str(round(new_value[index]) << self.shift_amount[index])
                param_setting+= '-set={param}={value} '.format(param=param, value=value)  
            param_setting += ''
            command = ['make', '-f', os.path.join(rv_root, 'tools/Makefile'), target, param_setting]
            # print(command)
            # Prepare the command with the expanded environment variable
            # Run the 'make' command in the directory where the Makefile is located
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
            minstret, mcycle = self.extract_minstret_mcycle(self.generated_logfile + 'Processor_Generation.log')
            if mcycle is None:
                return False, None, None
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None, None




class rocket_tuning:
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.generation_path = generation_path      # Path to execute the generation command
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/RocketChip/run_RocketChip_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../object_functions/Syn_Report/'
        self.stored_report_directory = '../object_functions/Syn_Report/dynamic_set/'
        self.generated_filename = 'rocket_chip_utilization_synth.rpt'
        self.generated_logfile = '../object_functions/Logs/'
        self.configuration_file = '../object_functions/rocket-chip/src/main/scala/subsystem/Configs.scala'

    def modify_config_files(self, input_vals):
            with open(self.configuration_file, 'r') as file:
                scala_code = file.read()
            
            # Regular expression to find the WithCustomisedCore class definition
            class_pattern = re.compile(r'class WithCustomisedCore\((.*?)\)\s*extends\s*Config\((.*?)=>\s*{(.*?)case RocketTilesKey\s*=>\s*{(.*?)}\s*}\)', re.DOTALL)
            match = class_pattern.search(scala_code)
            
            if match:
                params = match.group(1)
                body = match.group(4)
                for var_name, var_val in zip(self.tunable_params, input_vals):
                    class_name, sub_name = var_name.split('_')
                    print(class_name, sub_name)
                    if class_name == 'icache':
                        pattern = re.compile(r'icache\s*=\s*Some\(ICacheParams\((.*?)\)\)', re.DOTALL)
                        match = pattern.search(body)
                    elif class_name == 'dcache':
                        pattern = re.compile(r'dcache\s*=\s*Some\(DCacheParams\((.*?)\)\)', re.DOTALL)
                        match = pattern.search(body)
                    if match:
                        params = match.group(1)
                        sub_pattern = re.compile(rf'{sub_name}\s*=\s*\d+')
                        if sub_pattern.search(params):
                            new_params = sub_pattern.sub(f'{sub_name} = {var_val}', params)
                            new_body = body.replace(params, new_params)
                            scala_code = scala_code.replace(body, new_body)
                            body = new_body  # update the body for subsequent iterations
                        else:
                            print(f"{sub_name} not found in {class_name} parameters.")
                    else:
                        print(f"{class_name} class not found in the body.")
                with open(self.configuration_file, 'w') as file:
                    file.write(scala_code)
            else:
                print("WithCustomisedCore class definition not found.")

    def extract_mcycle_minstret(self):
        # Initialize variables to store mcycle and minstret
        mcycle = None
        minstret = None
        
        # Define the regex patterns to match the desired lines
        mcycle_pattern = re.compile(r'mcycle\s*=\s*(\d+)')
        minstret_pattern = re.compile(r'minstret\s*=\s*(\d+)')
        
        # Open the file and read its contents
        with open(self.generated_logfile + 'Processor_Generation.log', 'r') as file:
            lines = file.readlines()
        
        # Iterate over the lines to find the section and extract values
        for line in lines:
            if 'Microseconds for one run through Dhrystone:' in line:
                # Once we find the section, we start looking for mcycle and minstret
                for subsequent_line in lines[lines.index(line):]:
                    mcycle_match = mcycle_pattern.search(subsequent_line)
                    minstret_match = minstret_pattern.search(subsequent_line)
                    
                    if mcycle_match:
                        mcycle = int(mcycle_match.group(1))
                    
                    if minstret_match:
                        minstret = int(minstret_match.group(1))
                    
                    # Break the loop once both values are found
                    if mcycle is not None and minstret is not None:
                        break
        
        return mcycle, minstret

    def tune_and_run_performance_simulation(self, new_value, benchmark):
        try:
            # generate the design
            rounded_value = [round(val) for val in new_value]   
            self.modify_config_files(rounded_value)
            clean_command = ["make", "clean"]
            subprocess.run(clean_command, cwd = self.generation_path, check=True)
            run_benchmark_command = ["make", "-j12", "CONFIG=freechips.rocketchip.system.CustomisedConfig", f"output/{benchmark}.riscv.run"]
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
            minstret, mcycle = self.extract_mcycle_minstret()
            if mcycle is None:
                return False, None, None
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None, None
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile + 'Synthesis.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
        


if __name__ == '__main__':
    rocket_test = rocket_tuning(['icache_nSets', 'dcache_nSets'], [0, 0], '../object_functions/rocket-chip/emulator', '../object_functions/Vivado_Prj/rocket_chip/')
    # rocket_test.tune_and_run_performance_simulation([32, 64], 'dhrystone')
    rocket_test.run_synthesis()