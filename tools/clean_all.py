"""
Clean MicroHydra build folders for a clean run.
"""

import os
import shutil




CWD = os.getcwd()
OG_DIRECTORY = CWD

PARSE_PATH = os.path.join(CWD, 'MicroHydra')
DEVICE_PATH = os.path.join(CWD, 'devices')
ESP32_PATH = os.path.join(CWD, 'MicroPython', 'ports', 'esp32')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """
    Main script body.
    
    This file is organized such that the "main" logic lives near the top,
    and all of the functions/classes used here are defined below.
    """

    # parse devices into list of Device objects
    devices = []
    for filepath in os.listdir(DEVICE_PATH):
        if filepath != 'default.yml':
            devices.append(Device(filepath))


    # remove everything in ./MicroHydra
    print(f"{bcolors.OKBLUE}Cleaning ./MicroHydra...{bcolors.ENDC}")
    shutil.rmtree(PARSE_PATH)

    # remove each device build folder
    for device in devices:
        print(f"{bcolors.OKBLUE}Cleaning files for {device.name.title()}...{bcolors.ENDC}")
        device_build_path = os.path.join(ESP32_PATH, f"build-{device.name}")

        shutil.rmtree(device_build_path)
        
    
    print(f"{bcolors.OKGREEN}Finished cleaning MicroPython build files.{bcolors.ENDC}")
    os.chdir(OG_DIRECTORY)

        


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Classes ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class bcolors:
    """Small helper for print output coloring."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Device:
    """Store/parse device/platform details."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Device({self.name})"



class FileCopier:
    """Class contains methods for reading and parsing a given file."""
    def __init__(self, dir_entry, file_path):
        self.relative_path = file_path.removeprefix('/')
        self.dir_entry = dir_entry
        self.name = dir_entry.name
        self.path = dir_entry.path


    def __repr__(self):
        return f"FileParser({self.name})"


    def copy_to(self, dest_path):
        """For file types that shouldn't be modified, just copy instead."""
        dest_path = os.path.join(dest_path, self.relative_path, self.name)
        # make target directory:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        # write our original file data:
        with open(self.path, 'rb') as source_file:
            with open(dest_path, 'wb') as new_file:
                new_file.write(source_file.read())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def extract_file_data(dir_entry, path_dir):
    """Recursively extract DirEntry objects and relative paths for each file in directory."""
    if dir_entry.is_dir():
        output = []
        for r_entry in os.scandir(dir_entry):
            output += extract_file_data(r_entry, f"{path_dir}/{dir_entry.name}")
        return output
    else:
        return [(dir_entry, path_dir)]



main()
