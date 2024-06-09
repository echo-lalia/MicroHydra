import json
from lib.display.palette import Palette

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DEFAULT_CONFIG = const("""{
"24h_clock": false,
"wifi_ssid": "",
"bg_color": 2051,
"volume": 2,
"wifi_pass": "",
"ui_color": 65430,
"ui_sound": true,
"timezone": 0,
"sync_clock":
true
}""")


def mix(val2, val1, fac=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * fac) + (val2 * (1.0 - fac))
    return output


def mix_angle_float(angle1, angle2, factor=0.5):
    """take two angles as floats (range 0.0 to 1.0) and average them to the weight of factor.
    Mainly for blending hue angles."""
    # Ensure hue values are in the range [0, 1)
    angle1 = angle1 % 1
    angle2 = angle2 % 1

    # Calculate the angular distance between hue1 and hue2
    angular_distance = (angle2 - angle1 + 0.5) % 1 - 0.5
    # Calculate the middle hue value
    blended = (angle1 + angular_distance * factor) % 1

    return blended


def separate_color565(color):
    """
    Separate a 16-bit 565 encoding into red, green, and blue components.
    """
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return red, green, blue


def combine_color565(red, green, blue):
    """
    Combine red, green, and blue components into a 16-bit 565 encoding.
    """
    # Ensure color values are within the valid range
    red = max(0, min(red, 31))
    green = max(0, min(green, 63))
    blue = max(0, min(blue, 31))

    # Pack the color values into a 16-bit integer
    return (red << 11) | (green << 5) | blue


def rgb_to_hsv(r, g, b):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v


def hsv_to_rgb(h, s, v):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    if s == 0.0:
        return v, v, v
    i = int(h*6.0)
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    # Cannot get here


def mix_color565(color1, color2, mix_factor=0.5, hue_mix_fac=None, sat_mix_fac=None):
    """
    High quality mixing of two rgb565 colors, by converting through HSV color space.
    This function is probably too slow for running constantly in a loop, but should be good for occasional usage.
    """
    if hue_mix_fac == None:
        hue_mix_fac = mix_factor
    if sat_mix_fac == None:
        sat_mix_fac = mix_factor

    # separate to components
    r1, g1, b1 = separate_color565(color1)
    r2, g2, b2 = separate_color565(color2)
    # convert to float 0.0 to 1.0
    r1 /= 31
    r2 /= 31
    g1 /= 63
    g2 /= 63
    b1 /= 31
    b2 /= 31
    # convert to hsv 0.0 to 1.0
    h1, s1, v1 = rgb_to_hsv(r1, g1, b1)
    h2, s2, v2 = rgb_to_hsv(r2, g2, b2)

    # mix the hue angle
    hue = mix_angle_float(h1, h2, factor=hue_mix_fac)
    # mix the rest
    sat = mix(s1, s2, sat_mix_fac)
    val = mix(v1, v2, mix_factor)

    # convert back to rgb floats
    red, green, blue = hsv_to_rgb(hue, sat, val)
    # convert back to 565 range
    red = int(red * 31)
    green = int(green * 63)
    blue = int(blue * 31)

    return combine_color565(red, green, blue)


def darker_color565(color, mix_factor=0.5):
    """
    Get the darker version of a 565 color.
    """
    # separate to components
    r, g, b = separate_color565(color)
    # convert to float 0.0 to 1.0
    r /= 31
    g /= 63
    b /= 31
    # convert to hsv 0.0 to 1.0
    h, s, v = rgb_to_hsv(r, g, b)

    # higher sat value is percieved as darker
    s *= 1 + mix_factor
    v *= 1 - mix_factor

    # convert back to rgb floats
    r, g, b = hsv_to_rgb(h, s, v)
    # convert back to 565 range
    r = int(r * 31)
    g = int(g * 63)
    b = int(b * 31)

    return combine_color565(r, g, b)


def lighter_color565(color, mix_factor=0.2):
    """
    Get the lighter version of a 565 color.
    """
    # separate to components
    r, g, b = separate_color565(color)
    # convert to float 0.0 to 1.0
    r /= 31
    g /= 63
    b /= 31
    # convert to hsv 0.0 to 1.0
    h, s, v = rgb_to_hsv(r, g, b)

    # higher sat value is percieved as darker
    s *= 1 - (mix_factor / 2)
    v *= 1 + mix_factor

    # convert back to rgb floats
    r, g, b = hsv_to_rgb(h, s, v)
    # convert back to 565 range
    r = int(r * 31)
    g = int(g * 63)
    b = int(b * 31)

    return combine_color565(r, g, b)


def color565_shiftred(color, mix_factor=0.4, hue_mix_fac=0.8, sat_mix_fac=0.8):
    """
    Simple convenience function which shifts a color toward red.
    This was made for displaying 'negative' ui elements, while sticking to the central color theme.
    """
    _RED = const(63488)
    return mix_color565(color, _RED, mix_factor, hue_mix_fac, sat_mix_fac)


def color565_shiftgreen(color, mix_factor=0.1, hue_mix_fac=0.4, sat_mix_fac=0.1):
    """
    Simple convenience function which shifts a color toward green.
    This was made for displaying 'positive' ui elements, while sticking to the central color theme.
    """
    _GREEN = const(2016)
    return mix_color565(color, _GREEN, mix_factor, hue_mix_fac, sat_mix_fac)


def color565_shiftblue(color, mix_factor=0.1, hue_mix_fac=0.4, sat_mix_fac=0.2):
    """
    Simple convenience function which shifts a color toward blue.
    """
    _BLUE = const(31)
    return mix_color565(color, _BLUE, mix_factor, hue_mix_fac, sat_mix_fac)


def compliment_color565(color):
    """Generate a complimentary color from given RGB565 color."""
    r,g,b = separate_color565(color)
    r /= 31; g /= 63; b /= 31
    
    h,s,v = rgb_to_hsv(r,g,b)
    
    # opposite hue
    h += 0.5
    r,g,b = hsv_to_rgb(h,s,v)
    r *= 31; g *= 63; b *= 31
    
    return combine_color565(int(r), int(g), int(b))



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
                #= json.loads(conf.read())
                # in case config schema was updated, local config should be also updated
#                 for key, value in DEFAULT_CONFIG.items():
#                     self.config[key] = self.config.get(key, value)
        except:
            print("could not load settings from config.json. reloading default values.")
            with open("config.json", "w") as conf:
                conf.write(json.dumps(self.config))
                
        self._modified = False
        # generate an extended color palette
        self.generate_palette()


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
        self.palette[13] = color565_shiftblue(darker_color565(mid_color))
        
        self.palette[14] = compliment_color565(bg_color)
        self.palette[15] = compliment_color565(ui_color)


    def __getitem__(self, key):
        # get item passthrough
        return self.config[key]


    def __setitem__(self, key, new_val):
        self._modified = True
        # item assignment passthrough
        self.config[key] = new_val
