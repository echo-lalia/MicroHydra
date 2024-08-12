User-set settings for the main launcher are stored in /config.json.   
These settings can be easily accessed using the built-in mhconfig module.

``` Python
import mhconfig

config = mhconfig.Config()
```

<br />

This Config object provides a simple wrapper for config.json. It automatically creates the file if it does not exist, and reads the file from flash. It also automatically generates an extended color palette based on the two user-set BG and UI colors in the config.   

Config variables can be accessed by key, like a dictionary:
``` Python
ui_color = config["ui_color"] # main UI color (16bit int/rgb 565)
bg_color = config["bg_color"] # main BG color (16bit int/rgb 565)

ui_sound = config["ui_sound"] # UI sound on/off
volume = config["volume"] # system volume from 0-10

wifi_ssid = config["wifi_ssid"]
wifi_pass = config["wifi_pass"]
```

<br />

And, you can access an extended color palette from config.palette, and config.rgb_colors.   
Here are the definitions for each of those colors:
``` Python
color0 = config.palette[0] # darker bg color
color1 = config.palette[1] # bg color
color2 = config.palette[2] # mix_color565(bg_color, ui_color, 0.25)
color3 = config.palette[3] # mix_color565(bg_color, ui_color, 0.50) (mid_color)
color4 = config.palette[4] # mix_color565(bg_color, ui_color, 0.75)
color5 = config.palette[5] # ui color
color6 = config.palette[6] # lighter ui color

# these colors are based on the above color palette, but shifted towards the 3 display primaries
# they will NOT always actually be red, green, and blue, 
# but they will be the color palette colors shifted toward red, green, and blue (in HSV).
red, green, blue = config.rgb_colors
```


-----

<br />

Apps can also easily create and use their own config files using the [json](https://docs.micropython.org/en/latest/library/json.html) module.   

Here's an example of reading from the main config using json:
``` Python
import json

with open("config.json", "r") as conf:
    config = json.loads(conf.read())
    wifi_ssid = config["wifi_ssid"]
    wifi_pass = config["wifi_pass"]
```

Other stored values can be read the same way.

**Note:** It's best if apps don't directly modify the config created by the launcher, as if they do, they risk preventing that config from being read by the launcher. If that happens, the launcher will assume the values are missing or corrupted in some way, and reset config.json with the default values.

Apps can create their own config using the same technique used in the launcher, but they should keep a separate file to prevent conflicts between them.

<br /><br />

For your reference, here's the block of code from the launcher (copied from v0.6) which is responsible for reading or initializing config.json

This code tries to unpack the values from config.json into variables, and if it encounters any issues, simply uses default values and saves a config.json with those values

``` Python
#load config
try:
    with open("config.json", "r") as conf:
        config = json.loads(conf.read())
        ui_color = config["ui_color"]
        bg_color = config["bg_color"]
        ui_sound = config["ui_sound"]
        volume = config["volume"]
        wifi_ssid = config["wifi_ssid"]
        wifi_pass = config["wifi_pass"]
        sync_clock = config["sync_clock"]
        timezone = config["timezone"]
except:
    print("could not load settings from config.json. reloading default values.")
    config_modified = True
    ui_color = default_ui_color
    bg_color = default_bg_color
    ui_sound = default_ui_sound
    volume = default_volume
    wifi_ssid = ''
    wifi_pass = ''
    sync_clock = True
    timezone = 0
    with open("config.json", "w") as conf:
        config = {"ui_color":ui_color, "bg_color":bg_color, "ui_sound":ui_sound, "volume":volume, "wifi_ssid":'', "wifi_pass":'', 'sync_clock':True, 'timezone':0}
        conf.write(json.dumps(config))
```

-----
Lastly, there also exists a builtin module for the ESP32 called [NVS](https://docs.micropython.org/en/latest/library/esp32.html#non-volatile-storage) (non volatile storage), which can also be used to read and store persistent information.   

Generally, I think using json makes more sense in most cases, as it is easier to view and edit those config values.   
However, there are definitely some reasonable uses for NVS. For example, for the app FlappyStamp, I'm using NVS to store the user high-score, because it allows the game to be contained in a single file, and makes it slightly more difficult to manually edit/fake a high score in the game. 