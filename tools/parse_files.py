"""MicroHydra file parser is a script designed to enable multiplatform development for MicroHydra.

This script pulls source code from /src and turns it into
device-specific MicroHydra code for the each defined device.

Device definitions are stored in /devices, in yaml format.

Hydra "magic" Constants:
- Constants declared with the "_MH_" prefix, and
  which match a platform-specific value from the device yaml definition.
- Are replaced automatically with their device specific value.
- Initial value can be anything (for testing purposes).
Example:
`_MH_DISPLAY_WIDTH = const(1234)`
on CARDPUTER becomes:
`_MH_DISPLAY_WIDTH = const(240)`

Hydra Conditionals:
- Conditional 'if' statements that can include or exclude a block of code
  based on a given feature.
- Can also be used to match a device name, or whether or not a module is "frozen".
- Follow this syntax: `# mh_if {feature}:` or `# mh_if not {feature}:`
- "else"/"elif" supported using `# mh_else_if {feature}:` or `# mh_else:`
- Are closed with this phrase: `# mh_end_if`
- If the conditional passes and is commented out, uncomments it.
- If the conditional fails and is not commented out, it comments it out.
- Can be nested, but this is discouraged
  (It's hard to read because Python indentation must be maintained)
Example:
```
# mh_if touchscreen:
print("this device has a touchscreen!")
# mh_else:
# print("this device has no touchscreen!")
# mh_end_if
```
On CARDPUTER this becomes:
```
# mh_if touchscreen:
# print("this device has a touchscreen!")
# mh_else:
print("this device has no touchscreen!")
# mh_end_if
```
"""

import os
import yaml
import argparse
import re
import shutil
import time


# just used for printing the script time on completion:
START_TIME = time.time()

# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='MHParser',
description="""\
Parse MicroHydra source files using device descriptions to create device-specific 'builds' of MicroHydra.
""",
epilog='This program is designed to enable multi-platform support in MicroHydra.'
)

PARSER.add_argument('-s', '--source', help='Path to MicroHydra source to be parsed.')
PARSER.add_argument('-D', '--devices', help='Path to device definition folder.')
PARSER.add_argument('-d', '--dest', help='Destination path for parsed MicroHydra files.')
PARSER.add_argument('-v', '--verbose', action='store_true')
PARSER.add_argument('-z', '--zip', action='store_true', help='Put output device files into zip archives.')
PARSER.add_argument('--frozen', action='store_true')
SCRIPT_ARGS = PARSER.parse_args()

SOURCE_PATH = SCRIPT_ARGS.source
DEVICE_PATH = SCRIPT_ARGS.devices
DEST_PATH = SCRIPT_ARGS.dest
ZIP = SCRIPT_ARGS.zip
FROZEN = SCRIPT_ARGS.frozen
VERBOSE = SCRIPT_ARGS.verbose


# set defaults for args not given:
CWD = os.getcwd()

if SOURCE_PATH is None:
    SOURCE_PATH = os.path.join(CWD, 'src')
if DEVICE_PATH is None:
    DEVICE_PATH = os.path.join(CWD, 'devices')
if DEST_PATH is None:
    if FROZEN:
        DEST_PATH = os.path.join(CWD, 'MicroPython', 'ports', 'esp32', 'boards')
    else:
        DEST_PATH = os.path.join(CWD, 'MicroHydra')



with open(os.path.join(DEVICE_PATH, 'default.yml'), 'r', encoding="utf-8") as default_file:
    default = yaml.safe_load(default_file.read())
DEFAULT_CONSTANTS = default['constants']
DEFAULT_FEATURES = default['features']

# Only include these files in the "frozen" MicroHydra firmware
ONLY_INCLUDE_IF_FROZEN = [
    os.path.join(SOURCE_PATH, 'font', 'utf8_8x8.py')
]
# Only include these files in the non-frozen MicroHydra firmware
DONT_INCLUDE_IF_FROZEN = [
    os.path.join(SOURCE_PATH, 'font', 'utf8_8x8.bin')
]



# These file/dir names in `devices/` should not define new devices
NON_DEVICE_FILES = ['default.yml', 'esp32_mpy_build', 'README.md']


# Designate unicode "noncharacter" as representation of completed mh conditional
# 1-byte noncharacters = U+FDD0..U+FDEF, choosing from these arbitrarily.
CONDITIONAL_PARSED_FLAG = chr(0xFDD1)
CONDITIONAL_PARSED_ORIGINAL_DELIMITER = chr(0xFDD2)

# TODO: This information, along with much of the information listed above,
# should probably be moved into a separate config file.
MICROHYDRA_VERSION = (2, 3, 0)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """
    Main script body.
    
    This file is organized such that the "main" logic lives near the top,
    and all of the functions/classes used here are defined below.
    """

    # parse source files into list of file data
    all_file_data = []
    for dir_entry in os.scandir(SOURCE_PATH):
        all_file_data += extract_file_data(dir_entry, '')
    
    # include/exclude files based on frozen/non-frozen
    if not FROZEN:
        exclude_given_files(all_file_data, ONLY_INCLUDE_IF_FROZEN)
    else:
        exclude_given_files(all_file_data, DONT_INCLUDE_IF_FROZEN)

    # parse devices into list of Device objects
    devices = []
    for filepath in os.listdir(DEVICE_PATH):
        if filepath not in NON_DEVICE_FILES:
            devices.append(Device(filepath))

    # print status information
    print("\n")
    vprint(f"CWD: {bcolors.OKBLUE}{CWD}{bcolors.ENDC}")
    print(f"Parsing files in {bcolors.OKBLUE}{SOURCE_PATH}{bcolors.ENDC}")
    print(f"Destination: {bcolors.OKBLUE}{DEST_PATH}{bcolors.ENDC}")
    vprint(f"Found devices: {bcolors.OKCYAN}{devices}{bcolors.ENDC}")
    print("")

    # iterate over every file, and every device
    for dir_entry, file_path in all_file_data:
        file_parser = FileParser(dir_entry, file_path)
        vprint(f"{bcolors.OKGREEN}Parsing {file_parser.relative_path}/{file_parser.name}...{bcolors.ENDC}")

        # initialize and parse this file for each device 
        for device in devices:
            if file_parser.can_parse_file():
                vprint(f"    {bcolors.OKCYAN}{device}{bcolors.ENDC}")
                file_parser.init_lines()
                file_parser.parse_constants(device)
                file_parser.parse_conditionals(device, frozen=FROZEN)
                file_parser.save(DEST_PATH, device)
            else:
                # This script is only designed for .py files.
                # unsupported files should just be copied instead.
                vprint(f"    {bcolors.OKCYAN}copying directly...{bcolors.ENDC}")
                file_parser.save_unparsable_file(DEST_PATH, device)
    
    # for each device, copy device-specific source files to output folder
    for device in devices:
        device_file_data = get_device_files(device)
        for dir_entry, file_path in device_file_data:
            # definition file does not need to be copied over
            if dir_entry.name != "definition.yml":
                file_parser = FileParser(dir_entry, file_path)
                file_parser.save_unparsable_file(DEST_PATH, device)
        device.create_device_module(DEST_PATH)

    # when --zip is specified, also put device files into a zip archive.
    if ZIP:
        for device in devices:
            shutil.make_archive(
                os.path.join('MicroHydra', f"{device.name}_raw"),
                'zip',
                os.path.join('MicroHydra', device.name),
                )


    print_completed()


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
        self.constants = DEFAULT_CONSTANTS.copy()
        with open(os.path.join(DEVICE_PATH, name, "definition.yml"), 'r', encoding="utf-8") as device_file:
            device_def = yaml.safe_load(device_file.read())
            self.constants.update(device_def['constants'])
            self.features = device_def['features']
        self.name = name

    def __repr__(self):
        return f"Device({self.name})"

    def create_device_module(self, dest_path):
        """Create lib.device.py file containing device-specific values."""
        # reformat device constants into plain 'snake case'
        new_dict = {'name': self.name, 'mh_version': MICROHYDRA_VERSION}
        for key, val in self.constants.items():
            key = key.removeprefix('_MH_').lower()

            # convert None's
            if val == 'None':
                val = None
            else:
                # attempt conversion to int:
                try:
                    val = int(val)
                except:
                    pass

            new_dict[key] = val
        
        new_feats = self.features.copy()
        new_feats.append(self.name)

        # find target path
        destination = os.path.join(dest_path, self.name, 'lib', 'device.py')

        file_str = f'''\
"""This is an automatically generated module that contains the MH config for this specific device.

`Device.vals` contains a dictionary of constants for this device.
`Device.feats` contains a tuple of features that this device has, with the final value being the device name.

Usage examples:
```
width = Device.display_width
height = Device.display_height

if 'touchscreen' in Device:
    get_touch()
```
"""

class Device:
    vals = {new_dict}
    feats = {tuple(new_feats)}

    @staticmethod
    def __getattr__(name:str):
        return Device.vals[name]

    @staticmethod
    def __contains__(val:str):
        return val in Device.feats

Device = Device()
'''
        with open(destination, 'w') as file:
            file.write(file_str)



class FileParser:
    """Class contains methods for reading and parsing a given file."""
    def __init__(self, dir_entry, file_path):
        self.relative_path = file_path.removeprefix('/')
        self.dir_entry = dir_entry
        self.name = dir_entry.name
        self.path = dir_entry.path

        if self.can_parse_file():
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
        pattern = r'^\s*_MH_[A-Z0-9_]+\s*=\s*const\s*\(.+\)\s*(#.*)?$'

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
        pattern = r'^\s*(_MH_[A-Z0-9_]+)\s*=\s*const\s*\(.+\)\s*(#.*)?$'

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
        count_constants = 0
        for idx, line in enumerate(self.lines):
            # check if it looks like a constant first, so we can warn
            if self._looks_like_constant(line):
                const_name = self._get_constant_name(line)

                if const_name in device.constants.keys():
                    # replace the valid Hydra constant!
                    count_constants += 1
                    new_value = device.constants[const_name]
                    self.lines[idx] = self.replace_constant_value(line, new_value)

                else:
                    print(f"{bcolors.WARNING}WARNING: '{const_name}' "
                          "looks like a Hydra constant, but is not in device definition."
                          f"{bcolors.ENDC}"
                          )

        vprint(f"{bcolors.OKBLUE}        Parsed {count_constants} constants.{bcolors.ENDC}")


    @staticmethod
    def _is_hydra_conditional(line:str) -> bool:
        """Check if line contains a hydra conditional statement."""
        # early return for marked lines
        if CONDITIONAL_PARSED_FLAG in line:
            return False
        
        if "#" in line \
        and "mh_if" in line \
        and ":" in line:
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
    def _is_conditional_else(line:str) -> bool|str:
        """Check if line is an else OR elif statement."""
        # early return for marked lines
        if CONDITIONAL_PARSED_FLAG in line:
            return False

        if "#" in line and "mh_else" in line:
            found_comment = False
            while line:
                if line.startswith('#'):
                    found_comment = True
                elif found_comment and line.startswith('mh_else_if'):
                    return "mh_else_if"
                elif found_comment and line.startswith('mh_else'):
                    return "mh_else"
                elif found_comment and (not line[0].isspace()):
                    return False
                line = line[1:]
        return False


    @staticmethod
    def _is_conditional_end(line:str, includes_else=True) -> bool:
        """Check if line contains a conditional end. 
        (Includes else/elif by default!)
        """
        # early return for marked lines
        if CONDITIONAL_PARSED_FLAG in line:
            return False

        if "#" in line and ("mh_end_if" in line or ("mh_else" in line and includes_else)):
            found_comment = False
            while line:
                if line.startswith('#'):
                    found_comment = True
                elif found_comment and includes_else and line.startswith(('mh_end_if', 'mh_else')):
                    return True
                elif found_comment and (not line[0].isspace()):
                    return False
                line = line[1:]
        return False


    def _uncomment_conditional(self, start_idx, end_idx):
        """If a conditional is kept but all elements are commented out, uncomment those!"""
        relevant_slice = self.lines[start_idx:end_idx + 1]

        # check if all lines are commented
        for line in relevant_slice:
            # ignore blank lines!
            if not (line == "" or line.isspace()):
                # remove leading spaces to look for '#'
                if not line.strip().startswith('#'): 
                    return
        
        # check if comment has "# " or "#"
        # (again, allow blank lines)
        is_properly_spaced = all([('# ' in line or line == "" or line.isspace()) for line in relevant_slice])
        # if not properly spaced (not using `# <code>`) warn and exit
        # this is because proper indentation can't be guaranteed 
        # without consistent spacing.
        if not is_properly_spaced:
            print(
                f"{bcolors.WARNING}WARNING: Couldn't remove comments in lines "
                f"{start_idx} - {end_idx} due to incorrect spacing in one or more lines. "
                f"Make sure you include a space after the hash in your comments.{bcolors.ENDC}"
                )
            return

        # track nested conditionals
        condition_depth = 0
        # assume we can actually remove all the comments, now
        for i, line in enumerate(relevant_slice):

            # track nested conditionals
            if self._is_hydra_conditional(line):
                condition_depth += 1
            elif self._is_conditional_end(line, includes_else=False):
                condition_depth -= 1

            # if not inside a nested conditional, then remove the comments
            if condition_depth <= 0:
                idx = i + start_idx
                # replace only a single comment in every line (to preserve actual comments)
                self.lines[idx] = line.replace("# ", "", 1)


    def _comment_out_conditional(self, start_idx, end_idx):
        """If a conditional is excluded and isn't already commented out, comment it out!"""
        relevant_slice = self.lines[start_idx:end_idx + 1]

        # check if any lines are not commented
        any_uncommented = False
        for line in relevant_slice:
            # ignore blank lines!
            if not (line == "" or line.isspace()):
                # remove leading spaces to look for '#'
                if not line.strip().startswith('#'): 
                    any_uncommented = True
                    break

        # if all lines are commented, we shouldn't comment them again.
        if not any_uncommented:
            return

        # find the length of the minimum indentation. This will be the place we insert "#"s
        insert_idx = self._minimum_indentation(relevant_slice)
        # track nested conditionals
        condition_depth = 0
        # assume we can actually remove all the comments, now
        for i, line in enumerate(relevant_slice):

            # track nested conditionals
            if self._is_hydra_conditional(line):
                condition_depth += 1
            elif self._is_conditional_end(line, includes_else=False):
                condition_depth -= 1

            # if not inside a nested conditional, then remove the comments
            if condition_depth <= 0:
                # only add comments to non-empty (and non-space) lines
                if line and not line.isspace():
                    idx = i + start_idx
                    # add comment after indentation (preserve formatting)
                    # indentation, right_split = self._split_indentation(line)
                    self.lines[idx] = line[:insert_idx] + "# " + line[insert_idx:]


    @staticmethod
    def _minimum_indentation(lines) -> int:
        """Return the length of the shortest indentation from the given lines"""
        indents = []
        for line in lines:
            # ignore blank or space lines
            if line and not line.isspace():
                indents.append(FileParser._split_indentation(line)[0])

        min_line = min(indents, key=len)
        return len(min_line)


    @staticmethod
    def _split_indentation(right_split) -> tuple:
        """
        Split all space before characters, and the rest of the string.
        Returns (left_split:str, right_split:str)
        """
        left_split = ""
        while right_split and right_split[0].isspace():
            left_split += right_split[0]
            right_split = right_split[1:]
        
        return left_split, right_split


    @staticmethod
    def slice_str_to_char(string:str, stop_char:str) -> str:
        """Slice a given string from 0 to the given character (not inclusive)."""
        output = ""
        while string and not string.startswith(stop_char):
            output += string[0]
            string = string[1:]
        return output


    def _handle_expand_else(self, index, feature, has_not, else_type):
        """
        Given an index and the previously decoded "if" statement, 
        expand an else into a new if statement.
        """
        target_line = self.lines[index]

        if else_type == "mh_else":
            # if it's a regular else statment, 
            # all we have to do is invert the presence of "not"
            has_not = not has_not

        else:
            # if it's an elif statement, we should extract the new conditional.
            *conditional, feature = target_line.replace(":", "", 1).split()
            has_not = conditional[-1] == "not"
    
        # assemble new conditional
        new_line = self.slice_str_to_char(target_line, "#")
        not_str = " not" if has_not else ""
        new_line = f"{new_line}# mh_if{not_str} {feature}:\n"
        # store original line alongside modified line for formatting preservation
        self.lines[index] = new_line + CONDITIONAL_PARSED_ORIGINAL_DELIMITER + self.lines[index]


    
    def _process_one_conditional(self, device, frozen=False) -> bool:
        """
        Find and process a single Hydra conditional.
        Returns False if no conditional found,
        Returns True if conditional is processed. 

        The logic used by this method (and its helper methods):
        - Search for an "mh_if" statement, extract the named feature

        - Compare the feature to the device features, 
          invert the result if the "not" keyword is also present.

        - Find the matching "mh_end_if" by scanning each line.

        - If this conditional passes, uncomment the lines,
          or comment them out if it doesn't

        - Conditional lines we've seen are marked with noncharacters 
          so we remember to ignore them on the next cycle.

        - "mh_else" / "mh_else_if" statements are converted into normal "if" statements.
          The original text is preserved by appending the original line to the modified line,
          delimited with a noncharacter.
        
        - Once there are no conditionals remaining restore the converted else/elif lines,
          and remove all added noncharacters.
        """
        # search for the start and end of one conditional
        cond_start_idx = None
        cond_line = None
        cond_end_idx = None
        # also track how many ifs we've found (to allow nesting)
        conditional_opens = 0

        for idx, line in enumerate(self.lines):

            if self._is_hydra_conditional(line):
                conditional_opens += 1
                if cond_start_idx is None:
                    cond_start_idx = idx
                    cond_line = line

            elif cond_start_idx is not None \
            and self._is_conditional_end(line):
                conditional_opens -= 1
                if conditional_opens == 0:
                    cond_end_idx = idx
                    break
                # if this is an "else" statement, then the line also starts a new conditional.
                if self._is_conditional_else(line):
                    conditional_opens += 1

        if cond_start_idx is None or cond_end_idx is None:
            return False
        
        # Remove stored "original data" if present
        cond_line, *og_line = cond_line.split(CONDITIONAL_PARSED_ORIGINAL_DELIMITER)
        og_line = ''.join(og_line)

        # get feature string
        *conditional, feature = cond_line.replace(":", "", 1).split()
        # as in, has the "not" keyword
        if conditional[-1] == "not":
            has_not = True
        else:
            has_not = False


        if (feature == "frozen" and frozen) \
        or feature in device.features \
        or feature == device.name:
            keep_section = True
        else:
            keep_section = False
        
        if has_not:
            keep_section = not keep_section

        # mark this conditional completed
        self.lines[cond_start_idx] += CONDITIONAL_PARSED_FLAG

        if keep_section:
            # expand else/elif statement, or just remove a normal "end if"
            conditional_else = self._is_conditional_else(self.lines[cond_end_idx])
            if conditional_else:
                self._handle_expand_else(cond_end_idx, feature, has_not, conditional_else)
            else:
                # mark normal mh_end_if as completed
                self.lines[cond_end_idx] += CONDITIONAL_PARSED_FLAG

            # check if all kept lines are commented out. We can uncomment them if they are.
            self._uncomment_conditional(cond_start_idx + 1, cond_end_idx - 1)

        else:
            # comment out entire section
            # but if the final line is an elif, just reformat it
            conditional_else = self._is_conditional_else(self.lines[cond_end_idx])
            if conditional_else:
                self._handle_expand_else(cond_end_idx, feature, has_not, conditional_else)
            else:
                self.lines[cond_end_idx] += CONDITIONAL_PARSED_FLAG

            self._comment_out_conditional(cond_start_idx + 1, cond_end_idx - 1)

        return True





    def parse_conditionals(self, device, frozen=False):
        """Find conditional statements to include or exclude from lines based on device features/name"""
        conditionals = 0
        # this syntax is weird, but _process_one_conditional 
        # returns true until all conditionals are gone.
        while self._process_one_conditional(device, frozen):
            conditionals += 1
        
        # clean noncharacter flags
        self.lines = [line.replace(CONDITIONAL_PARSED_FLAG, "") for line in self.lines]
        # restore original lines
        self.lines = [line.split(CONDITIONAL_PARSED_ORIGINAL_DELIMITER)[-1] for line in self.lines]

        vprint(f"        {bcolors.OKBLUE}Parsed {conditionals} conditionals.{bcolors.ENDC}")


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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Other funcitons ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def extract_file_data(dir_entry, path_dir):
    """Recursively extract DirEntry objects and relative paths for each file in directory."""
    if dir_entry.is_dir():
        output = []
        for r_entry in os.scandir(dir_entry):
            output += extract_file_data(r_entry, f"{path_dir}/{dir_entry.name}")
        return output
    else:
        return [(dir_entry, path_dir)]
    

def is_in_dir(file, in_dir):
    """Check if `file` path is inside of `in_dir`"""
    # convert all to absolute paths to prevent them from becoming empty strings
    in_dir = os.path.abspath(in_dir)
    file = os.path.abspath(file)

    # if the file is inside the given directory, 
    # the last path segment they have in common should be the directory name. 
    dir_base, dir_name = os.path.split(in_dir)

    return os.path.relpath(
        os.path.commonpath((file, in_dir)),
        dir_base,
        ) == dir_name


def vprint(text):
    """Wrapper for print() that only prints if VERBOSE"""
    if VERBOSE:
        print(text)


def print_completed():
    """Print a handy little completion message"""
    elapsed = time.time() - START_TIME
    print(f"{bcolors.OKBLUE}Files parsed in {elapsed * 1000:.2f}ms.{bcolors.ENDC}")


def get_device_files(device):
    """Fetch the device-specific files for given device."""
    source_path = os.path.join(DEVICE_PATH, device.name)
    lib_path = os.path.join(source_path, 'lib')

    device_file_data = []
    for dir_entry in os.scandir(source_path):
        device_file_data += extract_file_data(dir_entry, '')

    # we only need the files in `lib/`
    device_file_data = [x for x in device_file_data if is_in_dir(x[0], lib_path)]

    return device_file_data


def exclude_given_files(file_list:list, exclude_list:list):
    """
    Remove files in given list that are defined in exclude_list
    """

    for filetuple in file_list:
        dir_entry, _ = filetuple
        
        if any(os.path.samefile(dir_entry, frozen_file)
        for frozen_file in exclude_list):
            file_list.remove(filetuple)
            

            


# run script
if __name__ == "__main__":
    main()
