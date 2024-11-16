"""Read and return Keyboard / Trackball data for the Lilygo T-Deck.

!Important note!:
    The T-Deck has a separate ESP32C3 in its keyboard that communicates
    with the main controller.
    The firmware that comes with that ESP32C3 is not very useful.
    It leaves several keys completely unused, and provides no way to
    read the keys being pressed.

    For this reason, MicroHydra has a custom firmware for the keyboard
    that much be flashed for full functionality.
    The custom firmware is backwards compatible with the og firmware,
    and it allows the main controller to enable a raw output mode.

    This module includes a simple method of 'detecting' when the old
    firmware is used, and enables a backwards-compatibility mode.
    However, the results will be lower quality compared to the custom firmware.
"""
from machine import I2C, Pin
import time


KBD_PWR = Pin(10, Pin.OUT)
KBD_INT = Pin(46, Pin.IN)


# keycodes mapped to matrix keys.
KEYMAP = {
    1:'q',   2:'w', 17:'e',  33:'r', 35:'t', 51:'y', 49:'u', 67:'i', 65:'o', 20:'p',
    4:'a',  18:'s', 19:'d',  39:'f', 34:'g', 50:'h', 55:'j', 71:'k', 66:'l', 68:'BSPC',
    5:'ALT',22:'z', 21:'x',  38:'c', 37:'v', 53:'b', 54:'n', 70:'m', 69:'$', 52:'ENT',
          23:'SHIFT',  7:'CTL',       6:'SPC',     3:'FN',  36:'SHIFT',
    }
KEYMAP_SHIFT = {
    1:'Q',   2:'W',  17:'E',  33:'R', 35:'T', 51:'Y', 49:'U', 67:'I', 65:'O', 20:'P',
    4:'A',  18:'S',  19:'D',  39:'F', 34:'G', 50:'H', 55:'J', 71:'K', 66:'L', 68:'BSPC',
    5:'ALT',22:'Z',  21:'X',  38:'C', 37:'V', 53:'B', 54:'N', 70:'M', 69:'$', 52:'ENT',
          23:'SHIFT',  7:'CTL',       6:'SPC',     3:'FN',  36:'SHIFT',
    }
KEYMAP_FN = {
    1:'#',   2:'1',  17:'2',  33:'3', 35:'(', 51:')', 49:'_', 67:'-', 65:'+', 20:'@',
    4:'*',  18:'4',  19:'5',  39:'6', 34:'/', 50:':', 55:';', 71:"'", 66:'"', 68:'DEL',
    5:'ALT',22:'7',  21:'8',  38:'9', 37:'?', 53:'!', 54:',', 70:'.', 69:'SPEAK',
          23:'SHIFT',  7:'0',          6:'TAB',     3:'FN',  36:'SHIFT',
    }


_KC_LEFT_SHIFT = const(23)
_KC_SHIFT = const(36)
_KC_FN = const(3)

_I2C_ADDR = const(0x55)

_BACKLIGHT_OFF = const(0x00)
_BACKLIGHT_ON  = const(0x01)
_DISABLE_RAW_MODE = const(0x02)
_ENABLE_RAW_MODE  = const(0x03)

# the number of keys sent in raw mode
_NUM_READ_KEYS = const(4)
_EMPTY_BYTES = b'\x00' * _NUM_READ_KEYS


# warning to print when wrong firmware is detected.
_KB_FIRMWARE_WARNING = const("""\
WARNING:
The T-Deck keyboard sent an invalid code to the _keys module.
This is probably because the wrong firmware is installed on the keyboard. \
It is reccomended that you flash the Hydra KB firmware to the keyboard to get full functionality.

Compatibility mode will now be enabled...""")


MOD_KEYS = const(("FN", "SHIFT", "CTL", "ALT", "OPT"))
ALWAYS_NEW_KEYS = const(('UP', 'RIGHT', 'LEFT', 'DOWN'))



class Keys:
    """Keys class is responsible for reading and returning currently pressed keys.

    Keys is intented to be used by the Input module.

    Args:
        tb_repeat_ms: (int)
            Minimum time between inputs .
    """

    # optional values set preferred main/secondary action keys:
    main_action = "G0"
    secondary_action = "ENT"
    aux_action = "SPC"

    ext_dir_dict = {'i':'UP', 'j':'LEFT', 'k':'DOWN', 'l':'RIGHT'}

    def __init__(self, tb_repeat_ms=60, **kwargs):  # noqa: ARG002
        # turn on keyboard
        KBD_PWR.value(1)

        # I2C for communicating with ESP32C3
        self.i2c = I2C(0, scl=Pin(8), sda=Pin(18), freq=400000, timeout=500000)

        # Stores a single int for writing to display
        # (because I2C requires it be a buffer)
        self.code_buf = bytearray(1)

        # enable raw mode (REQUIRES HYDRA KB FIRMWARE)
        self._send_code(_ENABLE_RAW_MODE)
        self.firmware_compat_mode = False

        # trackball read pins
        self.tb_up = Pin(3, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_down = Pin(15, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_left = Pin(1, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_right = Pin(2, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_click = Pin(0, mode=Pin.IN, pull=Pin.PULL_UP)

        # irq used to count directional input
        self.tb_up.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_down.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_left.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)
        self.tb_right.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_irq)

        # trackball motion
        self.tb_repeat_ms = tb_repeat_ms
        self.tb_timer = {
            self.tb_up: None,
            self.tb_down: None,
            self.tb_left: None,
            self.tb_right: None,
            }
        self.tb_x = 0
        self.tb_y = 0

        self.key_state = []


    @staticmethod
    def ext_dir_keys(keylist: list) -> list:
        """Convert typical (aphanumeric) keys into extended movement-specific keys."""
        for idx, key in enumerate(keylist):
            if key in Keys.ext_dir_dict:
                keylist[idx] = Keys.ext_dir_dict[key]
        return keylist


    def _handle_irq(self, tb_pin: Pin):
        """Respond to trackball movements."""
        if self.tb_timer[tb_pin] is not None \
        and time.ticks_diff(time.ticks_ms(), self.tb_timer[tb_pin]) < self.tb_repeat_ms:
            return

        self.tb_timer[tb_pin] = time.ticks_ms()

        if tb_pin == self.tb_left:
            self.tb_x -= 1
        elif tb_pin == self.tb_right:
            self.tb_x += 1

        elif tb_pin == self.tb_up:
            self.tb_y -= 1
        elif tb_pin == self.tb_down:
            self.tb_y += 1


    def _send_code(self, code: int):
        """Send a single code to the keyboard."""
        self.code_buf[0] = code
        self.i2c.writeto(_I2C_ADDR, self.code_buf)


    def _add_tb_keys(self, keylist: list):
        """Add trackball directions to keylist."""
        tb_x = self.tb_x
        tb_y = self.tb_y

        if not (tb_x or tb_y):
            if any(self.tb_timer.values()):
                for key in self.tb_timer:
                    self.tb_timer[key] = None
            return

        if tb_x:
            if tb_x > 0:
                keylist.append("RIGHT")
            else:
                keylist.append("LEFT")
            self.tb_x = 0
        if tb_y:
            if tb_y > 0:
                keylist.append("DOWN")
            else:
                keylist.append("UP")
            self.tb_y = 0


    def _special_mod_keys(self, keylist: list):
        """Convert device-specific key combos into general keys."""
        # shortcut for "OPT" key
        if "FN" in keylist \
        and "SHIFT" in keylist:
            keylist.remove("SHIFT")
            keylist.remove("FN")
        # shortcut for "ESC"
        if "ALT" in keylist \
        and "e" in keylist:
            keylist.remove("ALT")
            keylist.remove("q")
            keylist.append("ESC")


    def _alt_get_pressed_keys(self, **kwargs) -> list:  # noqa: ARG002
        """Alternate version of get_pressed_keys (for compatibility)."""
        try:
            read_key = self.i2c.readfrom(_I2C_ADDR, 1).decode()
        except UnicodeError:
            read_key = ""

        tb_val = self.tb_click.value()
        keys = []

        if read_key == "\x00" \
        and not self.tb_x \
        and not self.tb_y \
        and tb_val:
            self.key_state = keys
            return keys

        # tb button
        if tb_val == 0:
            keys.append("G0")

        if read_key != "\x00":
            if read_key == "\x08":
                keys.append("BSPC")
            elif read_key == '\r':
                keys.append("ENT")
            elif read_key == ' ':
                keys.append("SPC")
            else:
                keys.append(read_key)

        self._add_tb_keys(keys)
        self.key_state = keys
        return keys


    def set_backlight(self, value:bool):
        """Turn keyboard backlight on or off."""
        if value:
            self._send_code(_BACKLIGHT_ON)
        else:
            self._send_code(_BACKLIGHT_OFF)


    def get_pressed_keys(self, *, force_fn=False, force_shift=False) -> list:
        """Return currently pressed keys.

        Also, populate self.key_state with current vals.


        Args:
        force_fn: (bool)
            If true, forces the use of 'FN' key layer

        force_shift: (bool)
            If True, forces the use of 'SHIFT' key layer
        """
        codes = self.i2c.readfrom(_I2C_ADDR, _NUM_READ_KEYS)
        tb_val = self.tb_click.value()
        keys = []

        # early return on no input
        if codes == _EMPTY_BYTES \
        and not self.tb_x \
        and not self.tb_y \
        and tb_val:
            self.key_state = keys
            return keys


        # process special keys before converting to readable format
        if _KC_FN in codes and _KC_SHIFT in codes:
            keymap = KEYMAP
            keys.append('OPT')
        elif (_KC_FN in codes) \
        or force_fn:
            keymap = KEYMAP_FN
        elif (_KC_SHIFT in codes or _KC_LEFT_SHIFT in codes) \
        or force_shift:
            keymap = KEYMAP_SHIFT
        else:
            keymap = KEYMAP

        # tb button
        if tb_val == 0:
            keys.append("G0")

        for code in codes:
            if code != 0:
                if code in keymap:
                    key = keymap[code]
                    if key not in keys:
                        keys.append(key)

                elif code > 100 or code in {13, 32}:
                    # firmware should not be sending values like this
                    # enable compatibility mode for wrong kb firmware
                    print(_KB_FIRMWARE_WARNING)
                    self.firmware_compat_mode = True
                    self.get_pressed_keys = self._alt_get_pressed_keys
                    return [chr(code)]

        self._special_mod_keys(keys)
        self._add_tb_keys(keys)
        self.key_state = keys
        return keys
