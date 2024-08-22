import json
from lib.display.palette import Palette
from lib.hydra.color import *



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DEFAULT_CONFIG = const(
"""{
"""
# mh_if kb_light:
'"kb_light": false,'
# mh_end_if
"""
"24h_clock": false,
"wifi_ssid": "",
"bg_color": 2051,
"volume": 2,
"wifi_pass": "",
"ui_color": 65430,
"ui_sound": true,
"timezone": 0,
"sync_clock": true
}""")




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Config Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Config:
    def __init__(self):
        """
        This class aims to provide a convenient abstraction of the MicroHydra config.json
        The goal of this class is to prevent internal-MicroHydra scripts from reimplementing the same code repeatedly,
        and to provide easy to read methods for apps to access MicroHydra config values.
        """
        self.config = json.loads(DEFAULT_CONFIG)
        # initialize the config object with the values from config.json
        try:
            with open("config.json", "r") as conf:
                self.config.update(
                    json.loads(conf.read())
                    )
        except:
            print("could not load settings from config.json. reloading default values.")
            with open("config.json", "w") as conf:
                conf.write(json.dumps(self.config))

        self._modified = False
        # generate an extended color palette
        self.generate_palette()


    def __new__(cls):
        """Config is singleton; only one needs to exist."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance


    def save(self):
        """If the config has been modified, save it to config.json"""
        if self._modified:
            with open("config.json", "w") as conf:
                conf.write(json.dumps(self.config))


    def generate_palette(self):
        """
        Generate an expanded palette based on user-set UI/BG colors.
        """
        ui_color = self.config['ui_color']
        bg_color = self.config['bg_color']
        mid_color = mix_color565(bg_color, ui_color, 0.5)

        self.palette = Palette()

        # self.palette[0] = 0 # black
        self.palette[1] = darker_color565(bg_color)  # darker bg color

        # user colors
        for i in range(2, 9):
            fac = (i - 2) / 6
            self.palette[i] = mix_color565(bg_color, ui_color, fac)

        self.palette[9] = lighter_color565(ui_color)
        self.palette[10] = 65535 # white

        # Generate a further expanded palette, based on UI colors, shifted towards primary display colors.
        self.palette[11] = color565_shiftred(lighter_color565(bg_color))
        self.palette[12] = color565_shiftgreen(mid_color)
        self.palette[13] = color565_shiftblue(darker_color565(ui_color))

        self.palette[14] = compliment_color565(bg_color)
        self.palette[15] = compliment_color565(ui_color)


    def __getitem__(self, key):
        # get item passthrough
        return self.config[key]


    def __setitem__(self, key, new_val):
        self._modified = True
        # item assignment passthrough
        self.config[key] = new_val
