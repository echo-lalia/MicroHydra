import os
import json
import argparse
from pathlib import Path



# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='MHParser',
description="""\
Parse MicroHydra source files using device descriptions to create device-specific 'builds' of MicroHydra.
""",
epilog='This program is designed to enable multi-platform support in MicroHydra.'
)

PARSER.add_argument('-s', '--source', help='Path to MicroHydra source to be parsed.')
PARSER.add_argument('-D', '--devices', help='Path to device JSON definition folder.')
PARSER.add_argument('-d', '--dest', help='Destination path for parsed MicroHydra files.')
SCRIPT_ARGS = PARSER.parse_args()

SOURCE_PATH = SCRIPT_ARGS.source
DEVICE_PATH = SCRIPT_ARGS.devices
DEST_PATH = SCRIPT_ARGS.dest

# set defaults for args not given:
CWD = os.getcwd()

if SOURCE_PATH is None:
    SOURCE_PATH = f"{CWD}/../src"
if DEVICE_PATH is None:
    DEVICE_PATH = f"{CWD}/devices"
if DEST_PATH is None:
    DEST_PATH = f"{CWD}/../MicroHydra"




with open(CWD + '/devices/default', 'r', encoding="utf-8") as default_file:
    default = json.loads(default_file.read())
DEFAULT_CONSTANTS = default['constants']
DEFAULT_FEATURES = default['features']




def main():
    """Main script body."""

    # parse source files into list of file data
    all_file_data = []
    for dir_entry in os.scandir(SOURCE_PATH):
        all_file_data += extract_file_data(dir_entry, '')

    # parse devices into list of Device objects
    devices = []
    for filename in os.listdir(DEVICE_PATH):
        if filename != 'default':
            devices.append(Device(filename))

    # print status information
    print(f"Parsing files in {SOURCE_PATH}.")
    print(f"Destination: {DEST_PATH}")
    print(f"Found devices: {devices}")

    # iterate over every file, and every device
    for dir_entry, file_path in all_file_data:
        file_parser = FileParser(dir_entry, file_path)
        print(f"Parsing {file_parser.relative_path}/{file_parser.name}...")

        for device in devices:
            file_parser.init_lines()
            file_parser.parse_constants(device)
            file_parser.parse_conditionals(device, frozen=False)
            file_parser.save(DEST_PATH, device)




class Device:
    """Store/parse device/platform details."""
    def __init__(self, name):
        self.constants = DEFAULT_CONSTANTS.copy()
        with open(os.path.join(DEVICE_PATH, name), 'r', encoding="utf-8") as device_file:
            device_def = json.loads(device_file.read())
            self.constants.update(device_def['constants'])
            self.features = device_def['features']
        self.name = name

    def __repr__(self):
        return f"Device({self.name})"


class FileParser:
    """Class contains methods for reading and parsing a given file."""
    def __init__(self, dir_entry, file_path):
        self.relative_path = file_path
        self.dir_entry = dir_entry
        self.name = dir_entry.name
        self.path = dir_entry.path

        with open(self.path, 'r', encoding='utf-8') as src_file:
            self.src_lines = src_file.readlines()
        self.lines = []

    def __repr__(self):
        return f"FileParser({self.name})"

    def init_lines(self):
        """Copy src lines to be modified in lines"""
        self.lines = self.src_lines.copy()

    def parse_constants(self, device):
        """Read constants from device description, and replace constants in lines with device constants"""
        pass

    def parse_conditionals(self, device, frozen=False):
        """Find conditional statements to include or exclude from lines based on device features/name"""
        pass

    def save(self, dest_path, device):
        """Save modified contents to given destination."""
        pass


def extract_file_data(dir_entry, path_dir):
    """Recursively extract DirEntry objects and relative paths for each file in directory."""
    if dir_entry.is_dir():
        output = []
        for r_entry in os.scandir(dir_entry):
            output += extract_file_data(r_entry, f"{path_dir}/{dir_entry.name}")
        return output
    else:
        return [(dir_entry, path_dir)]


# run script
main()
