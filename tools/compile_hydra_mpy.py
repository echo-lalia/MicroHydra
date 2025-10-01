"""
Compile .mpy version of MicroHydra for each device.
"""

import os
import yaml
import argparse
import subprocess
import shutil
from mh_build_config import NON_DEVICE_FILES


# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='compile_hydra_mpy',
description="""\
Parse MicroHydra device files into .mpy files.
"""
)

PARSER.add_argument('-s', '--source', help='Path to MicroHydra source to be parsed.')
PARSER.add_argument('-D', '--devices', help='Path to device definition folder.')
PARSER.add_argument('-M', '--mpy', help='Path to mpy-cross.')
PARSER.add_argument('-v', '--verbose', action='store_true')
SCRIPT_ARGS = PARSER.parse_args()

SOURCE_PATH = SCRIPT_ARGS.source
DEVICE_PATH = SCRIPT_ARGS.devices
MPY_PATH = SCRIPT_ARGS.mpy
VERBOSE = SCRIPT_ARGS.verbose

# files that shouldn't be compiled
NO_COMPILE = ('main.py', 'apptemplate.py')

# set defaults for args not given:
CWD = os.getcwd()
OG_DIRECTORY = CWD

if SOURCE_PATH is None:
    SOURCE_PATH = os.path.join(CWD, 'MicroHydra')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if MPY_PATH is None:
    MPY_PATH = os.path.join(CWD, 'MicroPython', 'mpy-cross', 'build')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """
    Main script body.
    
    This file is organized such that the "main" logic lives near the top,
    and all of the functions/classes used here are defined below.
    """
    os.chdir(MPY_PATH)

    # parse devices into list of Device objects
    devices = []
    for filepath in os.listdir(DEVICE_PATH):
        if filepath not in NON_DEVICE_FILES:
            devices.append(Device(filepath))


    for device in devices:
        print(f"{bcolors.OKBLUE}Compiling .mpy files for {device.name.title()}...{bcolors.ENDC}")

        source_path = os.path.join(SOURCE_PATH, device.name)
        dest_path = os.path.join(SOURCE_PATH, f"{device.name}_compiled")

        source_files = []
        for dir_entry in os.scandir(source_path):
            source_files += extract_file_data(dir_entry, '')
        
        for dir_entry, file_path in source_files:
            file_compiler = FileCompiler(dir_entry, file_path)

            if file_compiler.can_compile():
                file_compiler.compile(dest_path, device.march)
            else:
                file_compiler.copy_to(dest_path)

        shutil.make_archive(dest_path, 'zip', dest_path)
    
    print(f"{bcolors.OKGREEN}Finished making compiled archives.{bcolors.ENDC}")
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
        with open(os.path.join(DEVICE_PATH, name, "definition.yml"), 'r', encoding="utf-8") as device_file:
            device_def = yaml.safe_load(device_file.read())
            self.march = device_def['mpy_arch']
        self.name = name

    def __repr__(self):
        return f"Device({self.name})"



class FileCompiler:
    """Class contains methods for reading and parsing a given file."""
    def __init__(self, dir_entry, file_path):
        self.relative_path = file_path.removeprefix('/')
        self.dir_entry = dir_entry
        self.name = dir_entry.name
        self.path = dir_entry.path


    def can_compile(self) -> bool:
        """Check if we can actually parse this file (don't parse non-python data files.)"""
        if self.name.endswith('.py') and self.name not in NO_COMPILE:
            return True
        return False


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


    def compile(self, dest_path, mpy_arch):
        """Compile using mpy-cross."""
        dest_name = self.name.removesuffix('.py') + '.mpy'
        dest_path = os.path.join(dest_path, self.relative_path, dest_name)
        # make target directory:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        # compile with mpy-cross
        os.system(f'./mpy-cross "{self.path}" -o "{dest_path}" -march={mpy_arch}')


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



def launch_wsl():
    """Attempt to use WSL if run from Windows"""
    subprocess.call('wsl -e sh -c "python3 tools/compile_hydra_mpy.py"')

# build process is convoluted on Windows (and not supported by this script)
# so if we are on Windows, try launching WSL instead:
is_windows = os.name == 'nt'

if is_windows:
    print("Running in Windows, attempting to use WSL...")
    launch_wsl()
else:
    main()
