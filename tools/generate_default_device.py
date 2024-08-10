"""
This simple script populates the default.yml file with defaults based on the content of all device definition.yml files.
"""

import yaml
import os
from collections import Counter



DEVICE_PATH = "devices"



def extract_file_data(dir_entry, path_dir):
    """Recursively extract DirEntry objects and relative paths for each file in directory."""
    if dir_entry.is_dir():
        output = []
        for r_entry in os.scandir(dir_entry):
            output += extract_file_data(r_entry, f"{path_dir}/{dir_entry.name}")
        return output
    else:
        return [(dir_entry, path_dir)]
    
def fill_device_data():
    """Get each device definition"""
    all_file_data = []

    for dir_entry in os.scandir(DEVICE_PATH):
        if dir_entry.is_dir():

            for subdir_entry in os.scandir(dir_entry):
                if subdir_entry.name == "definition.yml":
                    all_file_data.append(subdir_entry)

    return all_file_data


def combine_constants(dict_list):
    """Combine list of dicts of device constants into one most common dict."""
    combined_dict = {}
    
    # Collect all keys
    all_keys = set()
    for d in dict_list:
        all_keys.update(d.keys())
    
    # For each key, find the most common value
    for key in all_keys:
        # list of all vals for this key:
        values = [each_dict[key] for each_dict in dict_list if key in each_dict]

        most_common_value = Counter(values).most_common(1)[0][0]
        combined_dict[key] = most_common_value
    
    return combined_dict

def add_line_break(string, breakpoint):
    return string.replace(breakpoint, f'\n{breakpoint}')

def add_line_breaks(string, breaks):
    for breakpoint in breaks:
        string = add_line_break(string, breakpoint)
    return string


def main():
    device_data = fill_device_data()
    all_features = set()
    all_constants = []

    for dir_entry in device_data:
        with open(dir_entry, 'r') as def_file:
            device_def = yaml.safe_load(def_file.read())
        # add features
        for feat in device_def['features']:
            all_features.add(feat)

        all_constants.append(device_def['constants'])

    default_def = {
        "constants": combine_constants(all_constants),
        "features": list(all_features),
        "mpy_arch": 'xtensawin',
        }
    
    default_file_text = """\
# This file contains MicroHydra defaults that are dynamically generated from 
# each DEVICE/definition.yml file.
# This is mainly provided for reference, but also, any values missing from a 
# device definition will be loaded from here instead.
#
# 'constants' contains all the existing hydra constants from device definitions,
# plus the most common value.
#
# 'features' contains every single feature that exists in a device definition.

""" + add_line_breaks(
    yaml.dump(default_def), 
    ("features:", "mpy_arch:", "constants:")
    )

    with open(os.path.join(DEVICE_PATH, "default.yml"), "w") as default_file:
        default_file.write(default_file_text)

if __name__ == "__main__":
    main()
    