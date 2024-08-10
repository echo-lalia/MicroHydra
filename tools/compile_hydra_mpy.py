"""
Compile .mpy version of MicroHydra for each device.
"""

import os
import yaml
import argparse
import re
import subprocess
import time


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



# set defaults for args not given:
CWD = os.getcwd()

if SOURCE_PATH is None:
    SOURCE_PATH = os.path.join(CWD, 'MicroHydra')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if MPY_PATH is None:
    MPY_PATH = os.path.join(CWD, 'MicroPython', 'mpy-cross', 'build', 'mpy-cross')

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


    for device in devices:
        source_path = os.path.join(SOURCE_PATH, device.name)
        dest_path = os.path.join(SOURCE_PATH, f"{device.name}_compiled")

        source_files = []
        for dir_entry in os.scandir(source_path):
            source_files += extract_file_data(dir_entry, '')
        
        for dir_entry, file_path in all_file_data:
            file_compiler = FileCompiler(dir_entry, file_path)

            if file_compiler.can_parse_file():
                file_compiler.compile(dest_path, device.march)
            else:
                file_compiler.copy_to(dest_path)

        print(source_files)
        


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


    def can_parse_file(self) -> bool:
        """Check if we can actually parse this file (don't parse non-python data files.)"""
        if self.name.endswith('.py'):
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


    def save(self, dest_path, device):
        """Save modified contents to given destination."""
        dest_path = os.path.join(dest_path, device.name, self.relative_path, self.name)
        # make target directory:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        # write our modified lines:
        with open(dest_path, 'w', encoding="utf-8") as file:
            file.writelines(self.lines)


    def compile(self, dest_path, mpy_arch):


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
