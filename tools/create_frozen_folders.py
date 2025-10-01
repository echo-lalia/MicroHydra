"""
Copy device files to MicroPython boards folder for building firmwares.
"""

import os
import yaml
import argparse
import subprocess
import shutil
from mh_tools_common import bcolors, Device
from mh_build_config import NON_DEVICE_FILES, MPY_BUILD_COPY_FOLDERS


# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='create_frozen_folders',
description="""\
Copy device files to MicroPython boards folder.
"""
)

PARSER.add_argument('-d', '--dest', help='Path to MicroPython boards folder.')
PARSER.add_argument('-D', '--devices', help='Path to device definition folder.')
PARSER.add_argument('-M', '--micropython', help='Path to MicroPython source.')
PARSER.add_argument('-v', '--verbose', action='store_true')
SCRIPT_ARGS = PARSER.parse_args()

DEST_PATH = SCRIPT_ARGS.dest
DEVICE_PATH = SCRIPT_ARGS.devices
VERBOSE = SCRIPT_ARGS.verbose
MP_PATH = SCRIPT_ARGS.micropython


# set defaults for args not given:
CWD = os.getcwd()
OG_DIRECTORY = CWD

if MP_PATH is None:
    MP_PATH = os.path.join(CWD, 'MicroPython')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')


Device.load_defaults(DEVICE_PATH)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """
    Main script body.
    
    This file is organized such that the "main" logic lives near the top,
    and all of the functions/classes used here are defined below.
    """

    # start by copying over custom MicroHydra build files for each port
    for source_path, dest_path in MPY_BUILD_COPY_FOLDERS:
        print(f"Copying port files: {source_path} -> {dest_path}")
        port_source_path = os.path.join(DEVICE_PATH, source_path)
        port_dest_path = os.path.join(MP_PATH, dest_path)
        shutil.copytree(port_source_path, port_dest_path, dirs_exist_ok=True)

    # parse devices into list of Device objects
    devices = []
    for filepath in os.listdir(DEVICE_PATH):
        if filepath not in NON_DEVICE_FILES:
            devices.append(Device(filepath))


    for device in devices:
        print(f"Copying board files for {device.name.title()}...")

        # copy 'source board' as a baseline
        source_files = []

        device_source_path = device.get_source_path()
        print(f"\t - {device_source_path=}")
        source_board_path = device.get_source_board_path(MP_PATH)
        print(f"\t - {source_board_path=}")
        unique_board_path = device.get_unique_board_path(MP_PATH)
        print(f"\t - {unique_board_path=}")

        for dir_entry in os.scandir(source_board_path):
            source_files += extract_file_data(dir_entry, '')
        
        for dir_entry, file_path in source_files:
            file_copier = FileCopier(dir_entry, file_path)
            file_copier.copy_to(unique_board_path)

        # copy device-specific board files
        source_files = []
        for dir_entry in os.scandir(device_source_path):
            source_files += extract_file_data(dir_entry, '')
        
        for dir_entry, file_path in source_files:
            file_copier = FileCopier(dir_entry, file_path)
            file_copier.copy_to(unique_board_path)

    
    print("Finished copying MicroPython board files.")
    os.chdir(OG_DIRECTORY)

        


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Classes ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



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
