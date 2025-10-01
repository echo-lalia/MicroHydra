"""A class for reading, storing, and writing device information."""
import os
import yaml


class Device:
    device_path = None
    defaults = None
    default_constants = None

    @classmethod
    def load_defaults(cls, device_path: str):
        cls.device_path = device_path
        with open(os.path.join(device_path, 'default.yml'), 'r', encoding="utf-8") as default_file:
            cls.defaults = yaml.safe_load(default_file.read())
        cls.default_constants = cls.defaults['constants']

    def __init__(self, name):
        if Device.device_path is None or Device.default_constants is None:
            raise ValueError("Device.load_defaults must be called before loading any individual devices.")

        self.constants = self.default_constants.copy()
        with open(os.path.join(self.device_path, name, "definition.yml"), 'r', encoding="utf-8") as device_file:
            device_def = yaml.safe_load(device_file.read())
            self.constants.update(device_def['constants'])
            self.source_board = device_def['source_board']
            self.march = device_def['mpy_arch']
            self.mpy_port = device_def['mpy_port']
            self.features = device_def['features']
        self.name = name

    def __repr__(self):
        return f"Device({self.name})"

    def create_device_module(self, dest_path, mh_version: tuple[int, int, int]):
        """Create lib.device.py file containing device-specific values."""
        # reformat device constants into plain 'snake case'
        new_dict = {'name': self.name, 'mh_version': mh_version}
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
