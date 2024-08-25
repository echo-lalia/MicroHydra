## lib.device.Device

`device` is an automatically generated module containing the `Device` class. This class provides access to device-specific constants (as set in the `device/DEVICENAME/definition.yml` file, and is designed to assist in building multi-platform apps.

The class has two main attributes:
`Device.vals` contains a dictionary of constants for this device.
`Device.feats` contains a tuple of features that this device has.

Usage examples:
``` Py
from lib.device import Device

# acess device constants
width = Device.display_width
height = Device.display_height
name = Device.name

# Check for device features
if 'touchscreen' in Device:
    get_touch()

if `keyboard` in Device or 'CARDPUTER' in device:
    keyboard_stuff()
```

> Note: `Device` is a singleton and can't be called or re-initialized after importing.
