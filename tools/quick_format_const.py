"""
TODO: update this script to use yaml instead of json

This simple script is just designed to extract and print formatted constant declarations
from the device definition files.

example from default.json:
`"_MH_DISPLAY_WIDTH": "240",`

example output:
`_MH_DISPLAY_WIDTH = const(240)`

"""
import yaml
import os


# set a device name here to use that device
# (otherwise use default)
target_device = None


# ~~~~~~~~~ script: ~~~~~~~~~

# get path based on target device
if target_device is None:
    target_file = os.path.join("devices", "default.yml")
else:
    target_file = os.path.join("devices", target_device.upper(), "definition.yml")

# read lines from file
with open(target_file, "rb") as yml_file:
    data = yml_file.readlines()


for line in data:
    line = line.decode()

    # preserve spaces for readability
    if line.isspace():
        print()
    else:
        # try formatting into a valid json string
        line = line.strip()
        line = line.removesuffix("\n")
        line = line.removesuffix(",")

        # if json can be read, format it into a micropython const
        # else skip
        try:
            line_data = json.loads("{" + line + "}")
            for key, val in line_data.items():
                print(f"{key} = const({val})")
        except json.decoder.JSONDecodeError:
            pass