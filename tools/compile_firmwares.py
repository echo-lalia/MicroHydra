"""
This script mainly calls another build script, for building MicroPython firmware.
"""

import os
import yaml
import argparse
import subprocess
import shutil
from mh_tools_common import bcolors, Device
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

MP_PATH = os.path.join(CWD, 'MicroPython')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if IDF_PATH is None:
    IDF_PATH = os.path.join(CWD, 'esp-idf')

Device.load_defaults(DEVICE_PATH)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """
    Main script body.
    
    This file is organized such that the "main" logic lives near the top,
    and all of the functions/classes used here are defined below.
    """

    # parse devices into list of Device objects
    esp32_devices = []
    rp2_devices = []
    for filepath in os.listdir(DEVICE_PATH):
        if filepath not in NON_DEVICE_FILES:
            device = Device(filepath)
            if device.mpy_port == 'esp32':
                esp32_devices.append(device)
            elif device.mpy_port == 'rp2':
                rp2_devices.append(device)
            else:
                raise ValueError(f"Unrecognized device.mpy_port: {device.mpy_port}")

    # Run build for rp2 devices
    print(f"{bcolors.OKBLUE}Running rp2 build for {', '.join([device.name.title() for device in rp2_devices])}...{bcolors.ENDC}")
    subprocess.call([os.path.join('tools', 'build_rp2_device_bin.sh')] + [device.name for device in rp2_devices])

    # Run build for esp32 devices, passing each target device name.
    print(f"{bcolors.OKBLUE}Running builds for {', '.join([device.name.title() for device in esp32_devices])}...{bcolors.ENDC}")
    subprocess.call([os.path.join('tools', 'build_esp32_device_bin.sh')] + [device.name for device in esp32_devices])

    # Rename/move firmware bins for each esp32 device.
    source_path = os.path.join(MP_PATH, 'ports', 'esp32')
    for device in esp32_devices:
        os.chdir(OG_DIRECTORY)

        print(f'{bcolors.OKBLUE}Extracting "{device.name}.bin"...{bcolors.ENDC}')
        os.rename(
            os.path.join(source_path, f'build-{device.name}', 'firmware.bin'),
            os.path.join(OG_DIRECTORY, 'MicroHydra', f'{device.name}.bin'),
        )

    # Rename/move firmware uf2 for each rp2 device.
    source_path = os.path.join(MP_PATH, 'ports', 'rp2')
    for device in rp2_devices:
        os.chdir(OG_DIRECTORY)

        print(f'{bcolors.OKBLUE}Extracting "{device.name}.uf2"...{bcolors.ENDC}')
        os.rename(
            os.path.join(source_path, f'build-{device.name}', 'firmware.uf2'),
            os.path.join(OG_DIRECTORY, 'MicroHydra', f'{device.name}.uf2'),
        )

    print(f"{bcolors.OKGREEN}Finished making compiled bins.{bcolors.ENDC}")
    os.chdir(OG_DIRECTORY)





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
