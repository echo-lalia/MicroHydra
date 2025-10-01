"""
This script mainly calls another build script, for building MicroPython firmware.
"""

import os
import yaml
import argparse
import subprocess
import shutil
from mh_tools_common import bcolors
from mh_build_config import NON_DEVICE_FILES


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

print(CWD)

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
        if filepath not in NON_DEVICE_FILES:
            devices.append(Device(filepath))

    # Run build script, passing each target device name.
    print(f"{bcolors.OKBLUE}Running builds for {', '.join([device.name.title() for device in devices])}...{bcolors.ENDC}")
    subprocess.call([os.path.join('tools', 'build_device_bin.sh')] + [device.name for device in devices])

    # Rename/move firmware bins for each device.
    for device in devices:
        os.chdir(OG_DIRECTORY)

        print(f'{bcolors.OKBLUE}Extracting "{device.name}.bin"...{bcolors.ENDC}')
        os.rename(
            os.path.join(SOURCE_PATH, f'build-{device.name}', 'firmware.bin'),
            os.path.join(OG_DIRECTORY, 'MicroHydra', f'{device.name}.bin'),
        )


    print(f"{bcolors.OKGREEN}Finished making compiled bins.{bcolors.ENDC}")
    os.chdir(OG_DIRECTORY)



        


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Classes ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


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
