import re
import subprocess

class parameter_tuning:
    def __init__(self, tunable_params, settings_file, generation_path, vivado_project_path, board_settings):
        self.tunable_params = tunable_params    # A dictionary or list of parameters that can be tuned
        self.settings_file = settings_file      # Path to the Scala settings file
        self.board_settings = board_settings    # Name of the Scala object containing the settings
        self.generation_path = generation_path    # Path to the directory where the Makefile is located
        self.vivado_project_path = vivado_project_path
        self.tcl_path = 'D:\\Imperial\\Year4\\MasterThesis\\FYP_Bayesian_Optimisation\\object_functions\\tools\\run_synthesis.tcl'


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
            param_pattern = re.compile(r'(\"' + re.escape(self.tunable_params[index]) + r'\"\s*->\s*)(0x[0-9a-fA-FL]+|\d+L?)', re.DOTALL)
            
            # Replace the parameter value within the object content
            modified_object_content, n = param_pattern.subn(r'\g<1>' + str(round(new_value[index])), modified_object_content)
            if n == 0:
                raise ValueError(f"Parameter '{self.tunable_params[index]}' not found in board settings object '{self.board_settings}'.")

        # Replace the old object content with the modified one in the scala content
        modified_scala_content = scala_content[:match.start(1)] + modified_object_content + scala_content[match.end(1):]

        # Write the modified content back to the Scala file
        with open(self.settings_file, 'w') as file:
            file.write(modified_scala_content)
        

    def regenerate_design(self):
        '''Regenerate the design using the new parameters.'''
        try:
            # Run the 'make' command in the directory where the Makefile is located
            subprocess.run(['make', 'verilog'], check=True, cwd=self.generation_path)
            print("Makefile executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing Makefile: {e}")
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-mode", "batch", "-source", self.tcl_path]
        try:
            # Run the 'make' command in the directory where the Makefile is located
            subprocess.run(command, check=True, cwd=self.vivado_project_path, shell=True)
            print("Vivado Start successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing Makefile: {e}")



if __name__ == '__main__':
    board_settings = 'DefaultSettings'
    tunable_params = ['MemMapBase', 'MemMapRegionBits']
    settings_file = '../object_functions/NutShell-master/src/main/scala/top/Settings.scala'
    generation_path = '../object_functions/NutShell-master/'
    new_value = ['0x10000000L', '0x0']
    vivado_project_path = 'D:\\Imperial\\Year4\\MasterThesis\\FYP_Bayesian_Optimisation\\object_functions\\NutShell_Prj\\'
    pt = parameter_tuning(tunable_params, settings_file, generation_path, vivado_project_path, board_settings)
    pt.run_synthesis()
    pt.tune_parameter(new_value)