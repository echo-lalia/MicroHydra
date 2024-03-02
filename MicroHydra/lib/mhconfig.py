
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DEFAULT_CONFIG = {"ui_color":53243, "bg_color":4421, "ui_sound":True, "volume":2, "wifi_ssid":'', "wifi_pass":'', 'sync_clock':True, 'timezone':0}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Config Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Config:
    def __init__(self):
        """
        This class aims to provide a convenient abstraction of the MicroHydra config.json
        The goal of this class is to prevent internal-MicroHydra scripts from reimplementing the same code repeatedly,
        and to provide easy to read methods for apps to access MicroHydra config values.
        """
        import json, gc
        # initialize the config object with the values from config.json
        self.config = DEFAULT_CONFIG
        try:
            with open("config.json", "r") as conf:
                self.config = json.loads(conf.read())
            # storing just the vals from the config lets us check later if any values have been modified
            self.initial_values = tuple( self.config.values() )
            # check for missing keys to prevent a keyerror
            for key in DEFAULT_CONFIG.keys():
                if key not in self.config.keys():
                    self.config[key] = DEFAULT_CONFIG[key]
            
        except:
            print("could not load settings from config.json. reloading default values.")
            with open("config.json", "w") as conf:
                self.config = DEFAULT_CONFIG
                conf.write(json.dumps(self.config))
            # storing just the vals from the config lets us check later if any values have been modified
            self.initial_values = tuple( self.config.values() )
                
        # generate an extended color palette
        self.generate_palette()
        
        # run a garbage collection because just did a lot of one-use object creation.
        del json
        gc.collect()

    def save(self):
        """If the config has been modified, save it to config.json"""
        if tuple( self.config.values() ) != self.initial_values:
            import json
            with open("config.json", "w") as conf:
                conf.write(json.dumps(self.config))

    def generate_palette(self):
        """
        Generate an expanded palette based on user-set UI/BG colors.
        """
        from lib.tincture import Tinct
        
        ui_tinct = Tinct(self.config['ui_color'])
        bg_tinct = Tinct(self.config['bg_color'])
        mid_tinct = bg_tinct.blend(ui_tinct)
        
        # this should maintain support for light themes
        if ui_tinct < bg_tinct:
            add_value = -4
        else:
            add_value = 4
            
        self.palette = (
            (bg_tinct.add_lightness(-add_value)).get_RGB565(), # darker bg color
            self.config['bg_color'], # bg color
            bg_tinct.blend(ui_tinct, 0.25).get_RGB565(), # low-mid color
            mid_tinct.get_RGB565(), # mid color
            bg_tinct.blend(ui_tinct, 0.75).get_RGB565(), # high-mid color
            self.config['ui_color'], # ui color
            (ui_tinct.add_lightness(add_value)).get_RGB565(), # lighter ui color
            )
        
        # Generate a further expanded palette, based on UI colors, shifted towards primary display colors.
        self.extended_colors = (
            (min(bg_tinct,mid_tinct) + (0.3,0,0)).get_RGB565(), # red color
            (ui_tinct + (-0.15,0.2,-0.15)).get_RGB565(), # green color
            (mid_tinct + (-0.1,-0.1,0.15)).get_RGB565() # blue color
            )
    def __getitem__(self, key):
        # get item passthrough
        return self.config[key]
    def __setitem__(self, key, newvalue):
        # set item passthrough
        self.config[key] = newvalue
    