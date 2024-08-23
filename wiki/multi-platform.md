MicroHydra 2.0 brings a major overhaul to the structure of the project, all with the intention of expanding the code to work on multiple different devices, and develop for them all simultaneously.

This is an overview of how this currently works.


<br/> <br/>

## Main directory structure

*MicroHydra (base repository)*  
│  
├── **src/**  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  \  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; *This is where the majority of the source code for the program lives*  
│  
│  
├── **devices/**  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  \  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; *This is where the device definitions, and device specific drivers come from*  
│  
│  
├── **tools/**  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  \  
│ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; *`parse_files.py`, and other useful scripts live in here*  
│  
│  
└── **MicroHydra/**  
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  \  
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; *`parse_files.py` creates this directory by combining the source code in `src/`,*  
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; *with the definitions and drivers from `devices/`, for each device.*  


<br/> <br/>

## devices/

The `devices/` directory contains a `default.yml` file with the following structure:  
``` Yaml
# 'constants' contains all the existing hydra constants from device definitions,
# plus the most common value from the devices.
# The values are all strings representing MicroPython code to put in a `const()` declaration
# The keys follow a "_CONST_CASE" naming convention, and always start with "_MH_"
constants:
  _MH_CAPS_CASE_KEY_NAME: 'value'
  _MH_DISPLAY_BACKLIGHT: '38'
  _MH_BATT_ADC: 'None'

# 'features' contains a list of every single feature that exists in any device definition.
# The entries here follow  
features:
- display
- wifi
- keyboard
- any_other_feature

# This is the MicroPython arch to use when compiling code for the device.
# It is "xtensawin" for any ESP32-S3 based device.
mpy_arch: xtensawin

# This is the starting point to use when creating a firmware `.bin` file for the device.
# It specifies the name of a directory under `MicroPython/ports/esp32/boards/`
source_board: ESP32_GENERIC_S3
```

Then, each device has its own directory containing a `definition.yml` file, along with MicroPython build files and any device-specific drivers.  

*DEVICENAME*  
├── definition.yml  
├── manifest.py  
├── mpconfigboard.cmake  
└── *lib/*  
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; └── device_drivers.py  

The `definition.yml` file has the exact same structure as the `default.yml` file, but the values are tailored to that specific device.  
Any "constants" that are not in `definition.yml` use the defaults set in `default.yml` instead.  
Any "features" that are not in `definition.yml` are assumed to not exist on that device.

Any additional driver files in this folder are coppied over to the device-specific MicroHydra output folder (after copying the `src` files over)


<br/> <br/>

## Magic Constants

MicroHydra's 'magic' constants, are device constants that will be automatically replaced with the apropriate device-specific value by `tools/parse_files.py`.  
These constants are declared in the device `definition.yml` file, and they can used in any file in `src/`.

For example, if I write a file `src/lib/example.py`, and include the following line:  
``` Py
_MH_DISPLAY_WIDTH = const(1234)
```
When I run `parse_files.py`, the corrisponding output file for the Cardputer will be created in `MicroHydra/CARDPUTER/lib/example.py`, and the line will now look like this:  
``` Py
_MH_DISPLAY_WIDTH = const(240)
```

*Side note:*
> Because MicroPython supports 'real' constants, this functionality can be especially useful for MicroHydra.  
> When a MicroPython program is run, it must first be compiled into bytecode. At this time, the MicroPython compiler actually replaces the constants with hard-coded values.  
> This can slightly increase speed (no need to look-up the values), and can decrease RAM usage (no need to store the value name).  



<br/> <br/>

## Hydra conditionals

It's really difficult to account for all the possible differences between devices just by using device constants, and separate driver files.  
This is especially true because of the limited memory available to work with on these devices *(assuming you don't have PSRAM)*, so you really don't want to have code you don't need just taking up memory space.

That's where this final (and most complicated) feature of `tools/parse_files.py` comes in.

<br/>

Hydra conditionals are used to selectively include or exclude blocks of code from `src/` based on device names, included features, and whether the code is 'frozen' or not.

These statements take the following form:  
``` Py
# mh_if {feature}:
my_code()
# mh_end_if
```
In the above example, if {feature} is in the device-specific `definition.yml` file, then the line `my_code()` will be included in the output code for that device. Otherwise, the entire line is removed.  
The `# mh_if...` and `# mh_end_if` lines will be removed regardless of whether or not {feature} matches a feature in the device definition.

You can also use the "not" keyword:
``` Py
# mh_if not {feature}:
my_code()
# mh_end_if
```
Which, as expected, will exclude this line of code when {feature} exists on a device.

If/elif/else statements are also supported:  
``` Py
# mh_if {feature}:
feature_code()
# mh_else_if {other_feature}:
other_feature_code()
# mh_else:
no_features_code()
# mh_end_if
```

In order to make testing this code directly a bit easier, these conditionals also work on 'commented-out' code.  
In this example, the commented out code will be uncommented if the device has no touchscreen:
``` Py
# mh_if touchscreen:
print("this device has a touchscreen!")
# mh_else:
# print("this device has no touchscreen!")
# mh_end_if
```

> Note the spacing after the `#`. In order for the commenting/uncommenting to work correctly, this extra space needs to be there.
> This is because Python cares a lot about indentation, and without this space, the `parse_files` script might not correctly guess what the actual indentation was meant to be.



<br/> <br/><br/> <br/><br/> <br/>

Hydra Conditionals:
- Conditional 'if' statements that can include or exclude a block of code
  based on a given feature.
- Can also be used to match a device name, or whether or not a module is "frozen".
- Follow this syntax: `# mh_if {feature}:` or `# mh_if not {feature}:`
- elif supported using `# mh_else_if {feature}:`
- Are closed with this syntax: `# mh_end_if`
- If the entire conditional is commented out, 
  automatically uncomments it (for easier development/testing)
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
print("this device has no touchscreen!")
```
