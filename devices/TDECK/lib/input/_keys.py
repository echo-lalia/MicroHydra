"""
Read and return Keyboard / Trackball data
for the Lilygo T-Deck
"""
from machine import SoftI2C, Pin
import time

KBD_PWR = Pin(10, Pin.OUT)
KBD_INT = Pin(46, Pin.IN)

# keycodes mapped to matrix keys.
KEYMAP = {
    1:'q',   2:'w',  17:'e',  33:'r', 35:'t', 51:'y', 49:'u', 67:'i', 65:'o', 20:'p',
    4:'a',   18:'s', 19:'d',  39:'f', 34:'g', 50:'h', 55:'j', 71:'k', 66:'l', 68:'BSPC',
    5:'ALT',22:'z', 21:'x',  38:'c', 37:'v', 53:'b', 54:'n', 70:'m', 69:'$', 52:'ENT',
            23:'LSHFT', 7:'CTRL',     6:'SPC',     3:'SYM', 36:'SHFT',
    }

_I2C_ADDR = const(0x55)

_BACKLIGHT_OFF = const(0x00)
_BACKLIGHT_ON  = const(0x01)
_DISABLE_RAW_MODE = const(0x02)
_ENABLE_RAW_MODE  = const(0x03)

# the number of keys sent in raw mode
_NUM_READ_KEYS = const(4)


class Keys:
    """
    Keys class is responsible for reading and returning currently pressed keys.
    It is intented to be used by the Input module.
    """
    def __init__(self, tb_move_thresh = 2, **kwargs):
        # turn on keyboard
        KBD_PWR.value(1)

        # I2C for communicating with ESP32C3
        self.i2c = SoftI2C(scl=Pin(8), sda=Pin(18), freq=400000, timeout=50000)

        # Stores a single int for writing to display
        # (because I2C requires it be a buffer)
        self.code_buf = bytearray(1)
        
        # enable raw mode (REQUIRES HYDRA KB FIRMWARE)
        self._send_code(_ENABLE_RAW_MODE)
        
        # trackball read pins
        self.tb_up = Pin(3, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_down = Pin(15, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_left = Pin(1, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_right = Pin(2, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_click = Pin(0, mode=Pin.IN, pull=Pin.PULL_UP)
        # irq responds to TB inputs
        self.tb_up.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_down.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_left.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_right.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_click.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        
        # trackball motion
        self.tb_x = 0
        self.tb_y = 0
        self.tb_clicks = 0
        
        # set configuration
        self.tb_move_thresh = tb_move_thresh
        
        
    def _handle_irq(self, tb_pin):
        """Respond to trackball movements"""
        if tb_pin == self.tb_left:
            self.tb_x -= 1
        elif tb_pin == self.tb_right:
            self.tb_x += 1

        elif tb_pin == self.tb_up:
            self.tb_y -= 1
        elif tb_pin == self.tb_down:
            self.tb_y += 1
        
        elif tb_pin == self.tb_click:
            self.tb_clicks += 1


    def _send_code(self, code):
        """Send a single code to the keyboard"""
        self.code_buf[0] = code
        self.i2c.writeto(_I2C_ADDR, self.code_buf)


    def _add_tb_keys(self, keylist):
        """Add trackball keys to list"""
        tb_x = self.tb_x
        tb_y = self.tb_y
        move_thresh = self.tb_move_thresh
        
        tb_x //= move_thresh
        tb_y //= move_thresh
        
        if tb_x:
            if tb_x > 0:
                keylist.append("RIGHT")
            else:
                keylist.append("LEFT")
        if tb_y:
            if tb_y > 0:
                keylist.append("DOWN")
            else:
                keylist.append("UP")
        
        if self.tb_clicks:
            keylist.append("G0")
        
        self.tb_clicks = 0
        self.tb_x = 0
        self.tb_y = 0
        
        
    def _special_mod_keys(self, keylist):
        """Convert device-specific key combos into general keys."""
        # shortcut for "OPT" key
        if "LSHFT" in keylist:
            keylist.remove("LSHFT")
            if "CTRL" in keylist:
                keylist.remove("CTRL")
                keylist.append("OPT")
            else:
                keylist.append("SHFT")
        

    def get_pressed_keys(self):
        """Return currently pressed keys."""
        codes = self.i2c.readfrom(_I2C_ADDR, _NUM_READ_KEYS)
        keys = []
        for code in codes:
            if code != 0:
                # avoid rare duplicate keys
                key = KEYMAP[code]
                if key not in keys:
                    keys.append(key)
        
        self._special_mod_keys(keys)
        self._add_tb_keys(keys)
        return keys
        

if __name__ == "__main__":
    keys = Keys()
    while True:
        print(keys.get_pressed_keys())

        time.sleep_ms(50)
