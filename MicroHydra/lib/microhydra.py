import math, time


'''

This is a collection of utility functions and classes for MicroHydra.

This module was created to prevent 'launcher.py' from becoming too large,
and to provide easy access to any other scripts or apps who want to use these same utilities.

'''

# ~~~~~~~~~~~~~~~~~~~~~~~~~  CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DEFAULT_CONFIG = {"ui_color":53243, "bg_color":4421, "ui_sound":True, "volume":2, "wifi_ssid":'', "wifi_pass":'', 'sync_clock':True, 'timezone':0}
BACKLIGHT_MAX = const(65535)
BACKLIGHT_MIN = const(22000)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~         function definitions:          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~  math stuff  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def remap(value, in_min, in_max, clamp=True):
    if clamp == True:
        if value < in_min:
            return 0.0
        elif value > in_max:
            return 1.0
    # Scale the value to be in the range 0.0 to 1.0
    return (value - in_min) / (in_max - in_min)

def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod

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
    blended = (angle1 + angular_distance * factor) % 360

    return blended

# ~~~~~~~~~~~~~~~~~~~~~~~~~  string stuff  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def split_lines(text, max_length=27):
    """Split a string into multiple lines, based on max line-length."""
    lines = []
    current_line = ''
    words = text.split()

    for word in words:
        if len(word) + len(current_line) >= max_length:
            lines.append(current_line)
            current_line = word
        else:
            current_line += ' ' + word
        
    lines.append(current_line) # add final line
        
    return lines
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~  color stuff  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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



def avg_color565(color1, color2):
    """
    Combine two colors in color565 format, 50/50.
    """
    r1,g1,b1 = separate_color565(color1)
    r2,g2,b2 = separate_color565(color2)
    
    r = r1 + r2
    r = r // 2
    g = g1 + g2
    g = g // 2
    b = b1 + b2
    b = b // 2
    
    return combine_color565(r,g,b)

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
    i = math.floor(h*6.0)
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
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
    

def mix_color565(color1, color2, mix_factor=0.5):
    """
    High quality mixing of two rgb565 colors, by converting through HSV color space.
    This function is probably too slow for running constantly in a loop, but should be good for occasional usage.
    """
    #separate to components
    r1,g1,b1 = separate_color565(color1)
    r2,g2,b2 = separate_color565(color2)
    #convert to float 0.0 to 1.0
    r1 /= 31; r2 /= 31
    g1 /= 63; g2 /= 63
    b1 /= 31; b2 /= 31
    #convert to hsv 0.0 to 1.0
    h1,s1,v1 = rgb_to_hsv(r1,g1,b1)
    h2,s2,v2 = rgb_to_hsv(r2,g2,b2)
    
    #mix the hue angle
    hue = mix_angle_float(h1,h2,factor=mix_factor)
    #average the rest
    sat = (s1 + s2) / 2
    val = (v1 + v2) / 2
    
    #convert back to rgb floats
    red,green,blue = hsv_to_rgb(hue,sat,val)
    #convert back to 565 range
    red = math.floor(red * 31)
    green = math.floor(green * 63)
    blue = math.floor(blue * 31)
    
    return combine_color565(red,green,blue)



def darker_color565(color,mix_factor=0.5):
    """
    Get the darker version of a 565 color.
    """
    #separate to components
    r,g,b = separate_color565(color)
    #convert to float 0.0 to 1.0
    r /= 31; g /= 63; b /= 31
    #convert to hsv 0.0 to 1.0
    h,s,v = rgb_to_hsv(r,g,b)
    
    #higher sat value is percieved as darker
    s *= 1 + mix_factor
    v *= 1 - mix_factor
    
    #convert back to rgb floats
    r,g,b = hsv_to_rgb(h,s,v)
    #convert back to 565 range
    r = math.floor(r * 31)
    g = math.floor(g * 63)
    b = math.floor(b * 31)
    
    return combine_color565(r,g,b)


def lighter_color565(color,mix_factor=0.5):
    """
    Get the lighter version of a 565 color.
    """
    #separate to components
    r,g,b = separate_color565(color)
    #convert to float 0.0 to 1.0
    r /= 31; g /= 63; b /= 31
    #convert to hsv 0.0 to 1.0
    h,s,v = rgb_to_hsv(r,g,b)
    
    #higher sat value is percieved as darker
    s *= 1 - mix_factor
    v *= 1 + mix_factor
    
    #convert back to rgb floats
    r,g,b = hsv_to_rgb(h,s,v)
    #convert back to 565 range
    r = math.floor(r * 31)
    g = math.floor(g * 63)
    b = math.floor(b * 31)
    
    return combine_color565(r,g,b)


def color565_shiftred(color, mix_factor=0.5):
    """
    Simple convenience function which shifts a color toward red.
    This was made for displaying 'negative' ui elements, while sticking to the central color theme.
    """
    red = const(63488)
    return mix_color565(color, red, mix_factor)
    

def color565_shiftgreen(color, mix_factor=0.5):
    """
    Simple convenience function which shifts a color toward green.
    This was made for displaying 'positive' ui elements, while sticking to the central color theme.
    """
    green = const(2016)
    return mix_color565(color, green, mix_factor)
    


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~           class definitions:           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        try:
            with open("config.json", "r") as conf:
                self.config = json.loads(conf.read())
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
        mid_tinct = bg_tinct % ui_tinct
        
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
    
        

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UI_Overlay Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UI_Overlay:
    def __init__(self, config, keyboard, display_fbuf=None, display_py=None):
        """
        UI_Overlay aims to provide easy to use methods for displaying themed UI popups, and other Overlays.
        params:
            config:Config
                - A 'microhydra.Config' object.
                
            keyboard:KeyBoard
                - A 'KeyBoard' object from lib.keyboard
                
            display_fbuf:ST7789
            display_py:ST7789
                - An 'ST7789' object from lib.st7789fbuf or lib.st7789py
                - One of them must be supplied. 
        """
        self.config = config
        self.kb = keyboard
        
        # import our display to write to!
        self.compatibility_mode = False # working with st7789fbuf
        if display_fbuf:
            self.display = display_fbuf
        elif display_py:
            from font import vga1_8x16 as font
            self.display = display_py
            self.compatibility_mode = True # for working with st7789py
            self.font = font
        else:
            raise ValueError("UI_Overlay must be initialized with either 'display_fbuf' or 'display_py'.")
    
    def popup(self,text):
        """
        Display a popup message with given text.
        Blocks until any button is pressed.
        """
        # split text into lines
        lines = split_lines(text, max_length = 27)
        try:
            if self.compatibility_mode:
                # use the st7789py driver to display popup
                box_height = (len(lines) * 16) + 8
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.fill_rect(box_x, box_y, box_width, box_height, self.config.palette[0])
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.palette[2])
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[3])
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.palette[4])
                
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(self.font, line, centered_x, box_y + 4 + (idx*16), self.config.palette[-1], self.config.palette[0])
            else:
                #use the st7789fbuf driver to display popup
                box_height = (len(lines) * 10) + 8
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.rect(box_x, box_y, box_width, box_height, self.config.palette[0], fill=True)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.palette[2], fill=False)
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[3], fill=False)
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.palette[4], fill=False)
                
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(line, centered_x, box_y + 4 + (idx*10), self.config.palette[-1])
                self.display.show()
                
            time.sleep_ms(200)
            self.kb.get_new_keys() # run once to update keys
            while True:
                if self.kb.get_new_keys():
                    return
        except TypeError as e:
            raise TypeError(f"popup() failed. Double check that 'UI_Overlay' object was initialized with correct keywords: {e}")
        
    def error(self,text):
        """
        Display a popup error message with given text.
        Blocks until any button is pressed.
        """
        # split text into lines
        lines = split_lines(text, max_length = 27)
        try:
            if self.compatibility_mode:
                # use the st7789py driver to display popup
                box_height = (len(lines) * 16) + 24
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.fill_rect(box_x, box_y, box_width, box_height, 0)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.extended_colors[0])
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[0])
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.extended_colors[0])
                
                self.display.text(self.font, "ERROR", 100, box_y + 4, self.config.extended_colors[0])
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(self.font, line, centered_x, box_y + 20 + (idx*16), 65535, 0)
            else:
                #use the st7789fbuf driver to display popup
                box_height = (len(lines) * 10) + 20
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.rect(box_x, box_y, box_width, box_height, 0, fill=True)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.extended_colors[0], fill=False)
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[0], fill=False)
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.extended_colors[0], fill=False)
                
                self.display.text("ERROR", 100, box_y + 4, self.config.extended_colors[0])
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(line, centered_x, box_y + 16 + (idx*10), 65535)
                self.display.show()
                
            time.sleep_ms(200)
            self.kb.get_new_keys() # run once to update keys
            while True:
                if self.kb.get_new_keys():
                    return
                time.sleep_ms(1)
        except TypeError as e:
            raise TypeError(f"error() failed. Double check that 'UI_Overlay' object was initialized with correct keywords: {e}")
        
        
    
if __name__ == "__main__":
    # just for testing
    from lib import st7789fbuf, keyboard
    from machine import Pin, SPI
    from font import vga2_16x32 as font

    tft = st7789fbuf.ST7789(
        SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
        135,
        240,
        reset=Pin(33, Pin.OUT),
        cs=Pin(37, Pin.OUT),
        dc=Pin(34, Pin.OUT),
        backlight=Pin(38, Pin.OUT),
        rotation=1,
        color_order=st7789fbuf.BGR
        )
    
    kb = keyboard.KeyBoard()
    config = Config()
    overlay = UI_Overlay(config=config, keyboard=kb, display_fbuf=tft)

    # popup demo:
    tft.fill(0)
    tft.show()
    time.sleep(0.5)
    
    overlay.popup("Lorem ipsum is placeholder text commonly used in the graphic, print, and publishing industries for previewing layouts and visual mockups.")
    tft.fill(0)
    tft.show()
    time.sleep(0.5)
    
    overlay.error("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
    tft.fill(0)
    tft.show()
    
    # color palette
    bar_width = 240 // len(config.palette)
    for i in range(0,len(config.palette)):
        tft.rect(bar_width*i, 0, bar_width, 135, config.palette[i], fill=True)
        
    # extended colors
    bar_width = 240 // len(config.extended_colors)
    for i in range(0,len(config.extended_colors)):
        tft.rect(bar_width*i, 0, bar_width, 20, config.extended_colors[i], fill=True)
        
    config.save() # this should do nothing
    
    tft.show()
    time.sleep(2)
    tft.fill(0)
    tft.show()
    
    