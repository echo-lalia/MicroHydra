"""A class for reading, storing, and writing device information."""
import os
import yaml
from .bcolors import bcolors


class Device:
    device_path = None
    defaults = None
    default_constants = None
    all_features = None

    @classmethod
    def load_defaults(cls, device_path: str):
        cls.device_path = device_path
        with open(os.path.join(device_path, 'default.yml'), 'r', encoding="utf-8") as default_file:
            cls.defaults = yaml.safe_load(default_file.read())
        cls.default_constants = cls.defaults['constants']
        cls.all_features = cls.defaults['features']

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
        self.validate_def()

    def validate_def(self):
        """Check to ensure device/defaults make sense."""
        for const in self.constants:
            if const not in Device.default_constants:
                print(f"{bcolors.WARNING}WARNING: the constant '{const}' from device '{self.name}' does not appear in 'default.yml'!{bcolors.ENDC}")
            if not str(const).startswith("_MH_"):
                print(f"{bcolors.WARNING}WARNING: the constant '{const}' from device '{self.name}' doesn't start with '_MH_' (will not work with 'parse_files.py')!{bcolors.ENDC}")
        for feat in self.features:
            if feat not in Device.all_features:
                print(f"{bcolors.WARNING}WARNING: the feature '{feat}' from device '{self.name}' does not appear in 'default.yml'!{bcolors.ENDC}")

    def __repr__(self):
        return f"Device({self.name})"

    def get_source_path(self) -> str:
        """Get the path the this device's definition source folder."""
        return os.path.join(self.device_path, self.name)

    def get_source_board_path(self, micropython_path: str) -> str:
        """Return the path to this device's source/basis micropython board folder."""
        return os.path.join(micropython_path, 'ports', self.mpy_port, 'boards', self.source_board)

    def get_unique_board_path(self, micropython_path: str) -> str:
        """Return the path to this device's unique/output board micropython folder."""
        return os.path.join(micropython_path, 'ports', self.mpy_port, 'boards', self.name)

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
        destination = os.path.join(dest_path, 'lib', 'device.py')

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
