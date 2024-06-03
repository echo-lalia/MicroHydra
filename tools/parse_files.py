"""
MicroHydra file parser is a script inspired by PlatformIO,
designed to enable multiplatform development for MicroHydra.

This script pulls source code from /src and turns it into 
device-specific MicroHydra code for the each defined device.

Device definitions are stored in /devices, in json format.

Hydra Constants:
- Constants declared with the "_MH_" prefix, and
  which match a platform-specific value from the device json.
- Are replaced automatically with their device specific value.
- Initial value can be anything (for testing purposes).
Example:
`_MH_DISPLAY_WIDTH = const(240)`

Hydra Conditionals:
- Conditional 'if' statements that can include or exclude a block of code
  based on a given feature.
- Can also be used to match a device name, or whether or not a module is "frozen".
- Follow this syntax: `# mh_if {feature}:` or `# mh_if not {feature}:`
- Are closed with this syntax: `# mh_end_if`
- If the entire conditional is commented out, 
  automatically uncomments it (for easier development)
Example:
```
# mh_if touchscreen:
enable_touch = True,
# mh_end_if
```
"""

import os
import json
import argparse
import re
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
    SOURCE_PATH = os.path.join(CWD, 'src')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if DEST_PATH is None:
    DEST_PATH = os.path.join(CWD, 'MicroHydra')



with open(os.path.join(DEVICE_PATH, 'default'), 'r', encoding="utf-8") as default_file:
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
    print("\n")
    print(f"CWD: {bcolors.OKBLUE}{CWD}{bcolors.ENDC}")
    print(f"Parsing files in {bcolors.OKBLUE}{SOURCE_PATH}{bcolors.ENDC}")
    print(f"Destination: {bcolors.OKBLUE}{DEST_PATH}{bcolors.ENDC}")
    print(f"Found devices: {bcolors.OKCYAN}{devices}{bcolors.ENDC}")
    print("\n")

    # iterate over every file, and every device
    for dir_entry, file_path in all_file_data:
        file_parser = FileParser(dir_entry, file_path)
        print(f"{bcolors.OKGREEN}Parsing {file_parser.relative_path}/{file_parser.name}...{bcolors.ENDC}")

        for device in devices:
            if file_parser.can_parse_file():
                file_parser.init_lines()
                file_parser.parse_constants(device)
                file_parser.parse_conditionals(device, frozen=False)
                file_parser.save(DEST_PATH, device)
            else:
                file_parser.save_unparsable_file(DEST_PATH, device)


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
        self.relative_path = file_path.removeprefix('/')
        self.dir_entry = dir_entry
        self.name = dir_entry.name
        self.path = dir_entry.path


        with open(self.path, 'r', encoding='utf-8') as src_file:
            self.src_lines = src_file.readlines()
        self.lines = []


    def can_parse_file(self) -> bool:
        """Check if we can actually parse this file (don't parse non-python data files.)"""
        if self.name.endswith('.py'):
            return True
        return False


    def __repr__(self):
        return f"FileParser({self.name})"

    def init_lines(self):
        """Copy src lines to be modified in lines"""
        self.lines = self.src_lines.copy()


    @staticmethod
    def _looks_like_constant(line) -> bool:
        """
        Use regex to check that the given line is a Hydra constant declaration.
        """
        # This patten should (hopefully):
        # match only lines with constants that start with "_MH_"
        # not care about valid spacing around the constant
        # not care about comments after the constant
        pattern = r'^\s*_MH_[A-Z_]+\s*=\s*const\s*\(.+\)\s*(#.*)?$'

        # Use the regex to check if the line matches the pattern
        match = re.match(pattern, line)
        return bool(match)


    @staticmethod
    def _get_constant_name(line) -> str|None:
        """
        Assuming we have already checked that this looks like a Hydra constant,
        extract the name of that constant from the line.
        """
        # Same pattern as "_looks_like_constant" but with capture.
        pattern = r'^\s*(_MH_[A-Z_]+)\s*=\s*const\s*\(.+\)\s*(#.*)?$'

        match = re.match(pattern, line)
        if match:
            return match.group(1)
        else:
            return None


    @staticmethod
    def replace_constant_value(line, new_value) -> str:
        """Replace the value of constant in given line with a new value."""
        prefix_portion = ''

        # extract everything before const
        while not line.startswith('const('):
            prefix_portion += line[0]
            line = line[1:]
        
        
        # count parenthesis. 
        # This is being done just for edge cases where a parenthesis might appear around a const
        open_p_count = prefix_portion.count('(')

        suffix_portion = ''
        while suffix_portion.count(')') <= open_p_count:
            suffix_portion = line[-1] + suffix_portion
            line = line[:-1]

        return f"{prefix_portion}const({new_value}{suffix_portion}"


    def parse_constants(self, device):
        """Read constants from device description, and replace constants in lines with device constants"""
        for idx, line in enumerate(self.lines):
            # check if it looks like a constant first, so we can warn
            if self._looks_like_constant(line):
                const_name = self._get_constant_name(line)

                if const_name in device.constants.keys():
                    # replace the valid Hydra constant!
                    new_value = device.constants[const_name]
                    self.lines[idx] = self.replace_constant_value(line, new_value)

                else:
                    print(f"{bcolors.WARNING}WARNING: '{const_name}' "
                          "looks like a Hydra constant, but is not in device definition."
                          f"{bcolors.ENDC}"
                          )

    @staticmethod
    def _is_hydra_conditional(line:str) -> bool:
        """Check if line contains a hydra conditional statement."""
        if "#" in line and "mh_if" in line:
            found_comment = False
            while line:
                if line.startswith('#'):
                    found_comment = True
                elif found_comment and line.startswith('mh_if'):
                    return True
                elif found_comment and (not line[0].isspace()):
                    return False
                line = line[1:]
        return False


    @staticmethod
    def _is_conditional_end(line:str) -> bool:
        """Check if line contains a conditional end."""
        if "#" in line and "mh_end_if" in line:
            found_comment = False
            while line:
                if line.startswith('#'):
                    found_comment = True
                elif found_comment and line.startswith('mh_end_if'):
                    return True
                elif found_comment and (not line[0].isspace()):
                    return False
                line = line[1:]
        return False


    def parse_conditionals(self, device, frozen=False):
        """Find conditional statements to include or exclude from lines based on device features/name"""
        for idx, line in enumerate(self.lines):
            if self._is_hydra_conditional(line):
                pass
        


    def save_unparsable_file(self, dest_path, device):
        """For file types that shouldn't be modified, just copy instead."""
        dest_path = os.path.join(dest_path, device.name, self.relative_path, self.name)
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
