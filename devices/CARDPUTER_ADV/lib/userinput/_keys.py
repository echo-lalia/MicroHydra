"""Read and return keyboard data for the M5Stack Cardputer Advanced"""

from machine import Pin, I2C
import time

# Lookup constants for modifier keys
KC_SHIFT = const(61)
KC_FN = const(65)

# Regular keymap
KEYMAP = {
    1:'SPC', 2:'`', 3:'1', 4:'2', 5:'3', 6:'4', 7:'5', 8:'6',
    11:'7', 12:'8', 13:'9', 14:'0', 15:'-', 16:'=', 17:'BSPC',
    21:'TAB', 22:'q', 23:'w', 24:'e', 25:'r', 26:'t', 27:'y', 28:'u',
    31:'i', 32:'o', 33:'p', 34:'[', 35:'{', 36:']', 37:'\\',
    41:'FN', 42:'SHIFT', 43:'a', 44:'s', 45:'d', 46:'f', 47:'g', 48:'h',
    51:'j', 52:'k', 53:'l', 54:';', 55:':', 56:"'", 57:'ENT',
    61:'CTL', 62:'OPT', 63:'ALT', 64:'z', 65:'x', 66:'c', 67:'v', 68:'b',
    71:'n', 72:'m', 73:',', 74:'.', 75:'/', 76:'UP', 77:'LEFT', 78:'DOWN', 79:'RIGHT'
}

# Shifted keymap
KEYMAP_SHIFT = {
    1:'SPC', 2:'~', 3:'!', 4:'@', 5:'#', 6:'$', 7:'%', 8:'^',
    11:'&', 12:'*', 13:'(', 14:')', 15:'_', 16:'+', 17:'BSPC',
    21:'TAB', 22:'Q', 23:'W', 24:'E', 25:'R', 26:'T', 27:'Y', 28:'U',
    31:'I', 32:'O', 33:'P', 34:'{', 35:'}', 36:'|', 37:'\\',
    41:'FN', 42:'SHIFT', 43:'A', 44:'S', 45:'D', 46:'F', 47:'G', 48:'H',
    51:'J', 52:'K', 53:'L', 54:':', 55:'"', 56:"'", 57:'ENT',
    61:'CTL', 62:'OPT', 63:'ALT', 64:'Z', 65:'X', 66:'C', 67:'V', 68:'B',
    71:'N', 72:'M', 73:'<', 74:'>', 75:'?', 76:'UP', 77:'LEFT', 78:'DOWN', 79:'RIGHT'
}

# FN keymap (special functions, arrows, F1–F10, etc.)
KEYMAP_FN = {
    1:'SPC', 2:'ESC', 3:'F1', 4:'F2', 5:'F3', 6:'F4', 7:'F5', 8:'F6',
    11:'F7', 12:'F8', 13:'F9', 14:'F10', 15:'_', 16:'=', 17:'DEL',
    21:'TAB', 22:'q', 23:'w', 24:'e', 25:'r', 26:'t', 27:'y', 28:'u',
    31:'i', 32:'o', 33:'p', 34:'[', 35:']', 36:'\\', 37:'\\',
    41:'FN', 42:'SHIFT', 43:'a', 44:'s', 45:'d', 46:'f', 47:'g', 48:'h',
    51:'j', 52:'k', 53:'l', 54:'UP', 55:"'", 56:"'", 57:'ENT',
    61:'CTL', 62:'OPT', 63:'ALT', 64:'z', 65:'x', 66:'c', 67:'v', 68:'b',
    71:'n', 72:'m', 73:'LEFT', 74:'RIGHT', 75:'DOWN', 76:'UP', 77:'LEFT', 78:'DOWN', 79:'RIGHT'
}

MOD_KEYS = const(('ALT', 'CTL', 'FN', 'SHIFT', 'OPT'))
ALWAYS_NEW_KEYS = const(())

TCA8418_ADDR = 0x34

class Keys:
    """I2C-based keyboard reader for M5Stack Cardputer."""

    main_action = "ENT"
    secondary_action = "SPC"
    aux_action = "G0"

    def __init__(self, i2c_bus=1, scl_pin=9, sda_pin=8, int_pin=11):
        self.i2c = I2C(i2c_bus, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.int_pin = Pin(int_pin, Pin.IN, Pin.PULL_UP)
        self._key_state = []

    def scan(self):
        """Read all available key events from TCA8418."""
        key_list_buffer = []
        while not self.int_pin.value():  # While INT pin is low
            try:
                data = self.i2c.readfrom_mem(TCA8418_ADDR, 0x04, 1)[0]  # KEY_EVENT_A
                key_num = data & 0x7F
                key_pressed = bool(data & 0x80)
                if key_pressed:
                    key_list_buffer.append(key_num)
            except OSError:
                break  # No data
        self._key_state = key_list_buffer
        return key_list_buffer

    def get_pressed_keys(self, *, force_fn=False, force_shift=False):
        """Return human-readable key names."""
        self.scan()
        if not self._key_state:
            return []

        # Determine which mapping to use
        if KC_FN in self._key_state or force_fn:
            mapper = KEYMAP_FN
        elif KC_SHIFT in self._key_state or force_shift:
            mapper = KEYMAP_SHIFT
        else:
            mapper = KEYMAP

        return [mapper.get(k, str(k)) for k in self._key_state]
