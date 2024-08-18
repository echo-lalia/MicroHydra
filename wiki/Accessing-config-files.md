# hydra.config

User-set settings for the main launcher are stored in /config.json.   
These settings can be easily accessed using the built-in hydra.config module.

``` Python
from lib.hydra.config import Config

config = Config()
```

<br />

This Config object provides a simple wrapper for `config.json`. It automatically creates the file if it does not exist, and reads the file from flash. It also automatically generates an extended color palette based on the two user-set BG and UI colors in the config.   

Config variables can be accessed by key, like a dictionary:
``` Python
wifi_ssid = config["wifi_ssid"]
wifi_pass = config["wifi_pass"]
```

<br />

And, you can access the configured color palette from `config.palette` *(this is the same as lib.display.palette)*

Here is a quick reference of the color indices: 
``` Python
# 0-10 main user colors
black = config.palette[0]
bg_color = config.palette[2]
ui_color = config.palette[8]
white = config.palette[10]

# 11-13 primary colors
reddish = config.palette[11]
greenish = config.palette[12]
blueish = condfig.palette[13]

# 14-15 opposite hues of bg_color and ui_color:
bg_compliment = config.palette[14]
ui_complement = config.palette[15]
```
For a more complete overview, take a look at the wiki for [lib.display.palette](https://github.com/echo-lalia/Cardputer-MicroHydra/wiki/Palette)

-----

<br /><br />

# json files

Apps can also easily create and use their own, separate config files using the [json](https://docs.micropython.org/en/latest/library/json.html) module.   

Here's an example of reading from the main config using json:
``` Python
import json

with open("config.json", "r") as conf:
    config = json.loads(conf.read())
    wifi_ssid = config["wifi_ssid"]
    wifi_pass = config["wifi_pass"]
```

Other stored values can be read the same way.

**Note:** *It's best if apps don't directly modify the config created by the launcher, as if they do, they risk preventing that config from being read by the launcher. If that happens, the launcher will assume the values are missing or corrupted in some way, and reset config.json with the default values.*

Apps can create their own config using the same technique used in the launcher, but they should keep a separate file to prevent conflicts between them.

-----

<br /><br />

# NVS

Lastly, there also exists a builtin module for the ESP32 called [NVS](https://docs.micropython.org/en/latest/library/esp32.html#non-volatile-storage) *(non volatile storage)*, which can also be used to read and store persistent information.   

Generally, I think using json makes more sense in most cases, as it is easier to view and edit those config values.   
However, there are definitely some reasonable uses for NVS. For example, for the app FlappyStamp, I'm using NVS to store the user high-score, because it allows the game to be contained in a single file, and makes it *slightly* more difficult to manually edit/fake a high score in the game. 