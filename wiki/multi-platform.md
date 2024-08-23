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



<br/> <br/> <br/>

## Hydra conditionals

It's really difficult to account for all the possible differences between devices just by using device constants, and separate driver files.  
This is especially true because of the limited memory available to work with on these devices *(assuming you don't have PSRAM)*, so you really don't want to have code you don't need just taking up memory space.

That's where this final (and most complicated) feature of `tools/parse_files.py` comes in.

<br/> <br/>

Hydra conditionals are used to selectively include or exclude blocks of code from `src/` based on device names, included features, and whether the code is 'frozen' or not.

These statements take the following form:  
``` Py
# mh_if {feature}:
my_code()
# mh_end_if
```
In the above example, if {feature} is in the device-specific `definition.yml` file, then the line `my_code()` will be included in the output code for that device. Otherwise, the entire line is removed.  
The `# mh_if...` and `# mh_end_if` lines will be removed regardless of whether or not {feature} matches a feature in the device definition.

<br/>

You can also use the "not" keyword:
``` Py
# mh_if not {feature}:
my_code()
# mh_end_if
```
Which, as expected, will exclude this line of code when {feature} exists on a device.

<br/>

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

<br/>

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

<br/> <br/>

Finally, here are some real examples from `src/` to illustrate these features further!  

> From launcher/launcher.py:
``` Py
DISPLAY = display.Display(
    # mh_if spi_ram:
    # use_tiny_buf=False,
    # mh_else:
    use_tiny_buf=True,
    # mh_end_if
    )
```
``` Py
    # add an appname for builtin file browser
    app_names.append("Files")
    # mh_if frozen:
    # app_paths["Files"] = ".frozen/launcher/files"
    # mh_else:
    app_paths["Files"] = "/launcher/files"
    # mh_end_if
```

<br/>

> From launcher/settings.py:
``` Py
# mh_if touchscreen:
def process_touch(keys):
    events = kb.get_touch_events()
    for event in events:
        if hasattr(event, 'direction'):
            # is a swipe
            keys.append(event.direction)
        
        elif _CONFIRM_MIN_X < event.x < _CONFIRM_MAX_X \
        and _CONFIRM_MIN_Y < event.y < _CONFIRM_MAX_Y:
            keys.append("ENT")
# mh_end_if
```
``` Py
while True:
    keys = kb.get_new_keys()
    
    # mh_if touchscreen:
    process_touch(keys)
    # mh_end_if
```

<br/>

> From lib/display/display.py:
``` Py
    def __init__(self, use_tiny_buf=False, **kwargs):
        # mh_if TDECK:
        # # Enable Peripherals:
        # machine.Pin(10, machine.Pin.OUT, value=1)
        # mh_end_if
```

<br/> <br/>

*Final note on hydra conditionals:*
> These conditionals can also be nested. However, this is discouraged because it becomes very hard to read (because indentation must be maintained to match the original code).
> It's an option in your toolkit, but please try to find another solution first if it comes to that.
