"""
Script tries to setup esp-idf for building MicroPython.
"""

import os
import yaml
import argparse
import subprocess
import shutil


# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='compile_hydra_mpy',
description="""\
Parse MicroHydra device files into .mpy files.
"""
)

PARSER.add_argument('-s', '--source', help='Path to MicroPython port folder.')
PARSER.add_argument('-i', '--idf', help='Path to esp-idf folder.')
PARSER.add_argument('-D', '--devices', help='Path to device definition folder.')
PARSER.add_argument('-v', '--verbose', action='store_true')
SCRIPT_ARGS = PARSER.parse_args()

SOURCE_PATH = SCRIPT_ARGS.source
DEVICE_PATH = SCRIPT_ARGS.devices
IDF_PATH = SCRIPT_ARGS.idf
VERBOSE = SCRIPT_ARGS.verbose

# set defaults for args not given:
CWD = os.getcwd()
OG_DIRECTORY = CWD

if SOURCE_PATH is None:
    SOURCE_PATH = os.path.join(CWD, 'MicroPython', 'ports', 'esp32')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if IDF_PATH is None:
    IDF_PATH = os.path.join(CWD, 'esp-idf')


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
        print(f"{bcolors.OKBLUE}Building for {device.name.title()}...{bcolors.ENDC}")
        subprocess.call(["tools/build_device_bin.sh", device.name])
        os.chdir(OG_DIRECTORY)
    
    print(f"{bcolors.OKGREEN}Finished making compiled bins.{bcolors.ENDC}")
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










def launch_wsl():
    """Attempt to use WSL if run from Windows"""
    subprocess.call('wsl -e sh -c "python3 tools/compile_firmwares.py"')

# build process is convoluted on Windows (and not supported by this script)
# so if we are on Windows, try launching WSL instead:
is_windows = os.name == 'nt'

if is_windows:
    print("Running in Windows, attempting to use WSL...")
    launch_wsl()
else:
    main()
