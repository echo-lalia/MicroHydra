"""Read and return keyboard data for the M5Stack Cardputer ADV."""

from machine import Pin, I2C
from .tca8418 import TCA8418
import time

#lookup values for our keyboard
KC_SHIFT = const(7)
KC_FN = const(3)

KEYMAP = {
    1:'`',  5:'1',  11:'2',  15:'3', 21:'4', 25:'5', 31:'6', 35:'7', 41:'8', 45:'9', 51:'0', 55:'-',61:'=', 65:'BSPC',

    2:'TAB',6:'q',  12:'w',  16:'e', 22:'r', 26:'t', 32:'y', 36:'u', 42:'i', 46:'o', 52:'p', 56:'[', 62:']', 66:'\\',

    3:"FN",7:"SHIFT",13:'a', 17:'s', 23:'d', 27:'f', 33:'g', 37:'h', 43:'j', 47:'k', 53:'l', 57:';', 63:"'", 67:'ENT',

    4:'CTL',8:'OPT',14:'ALT',18:'z', 24:'x', 28:'c', 34:'v', 38:'b', 44:'n', 48:'m', 54:',', 58:'.', 64:'/', 68:'SPC',
    }

KEYMAP_SHIFT = {
    1:'~',  5:'!',  11:'@',  15:'#', 21:'$', 25:'%', 31:'^', 35:'&', 41:'*', 45:'(', 51:')', 55:'_', 61:'+', 65:'BSPC',

    2:'TAB',6:'Q',  12:'W',  16:'E', 22:'R', 26:'T', 32:'Y', 36:'U', 42:'I', 46:'O', 52:'P', 56:'{',62:'}',66:'|',

    3:"FN",7:"SHIFT",13:'A', 17:'S', 23:'D', 27:'F', 33:'G', 37:'H', 43:'J', 47:'K', 53:'L', 57:':', 63:'"', 67:'ENT',

    4:'CTL',8:'OPT',14:'ALT',18:'Z', 24:'X', 28:'C', 34:'V', 38:'B', 44:'N', 48:'M', 54:'<', 58:'>', 64:'?', 68:'SPC',
    }

KEYMAP_FN = {
    1:'ESC',5:'F1', 11:'F2', 15:'F3',21:'F4',25:'F5',31:'F6',35:'F7',41:'F8',45:'F9',51:'F10',55:'_',61:'=', 65:'DEL',

    2:'TAB',6:'q',  12:'w',  16:'e', 22:'r', 26:'t', 32:'y', 36:'u',42:'i', 46:'o', 52:'p', 56:'[', 62:']', 66:'\\',

    3:"FN",7:"SHIFT",13:'a', 17:'s', 23:'d', 27:'f', 33:'g', 37:'h', 43:'j', 47:'k', 53:'l', 57:'UP',63:"'", 67:'ENT',

    4:'CTL',8:'OPT',14:'ALT',18:'z', 24:'x', 28:'c', 34:'v', 38:'b', 44:'n',48:'m',54:'LEFT',58:'DOWN',64:'RIGHT',68:'SPC',  # noqa: E501
    }

MOD_KEYS = const(('ALT', 'CTL', 'FN', 'SHIFT', 'OPT'))
ALWAYS_NEW_KEYS = const(())

class Keys:
    """Keys class is responsible for reading and returning currently pressed keys.

    It is intented to be used by the Input module.
    """

    # optional values set preferred main/secondary action keys:
    main_action = "ENT"
    secondary_action = "SPC"
    aux_action = "G0"

    ext_dir_dict = {';':'UP', ',':'LEFT', '.':'DOWN', '/':'RIGHT', '`':'ESC'}

    def __init__(self, **kwargs):  # noqa: ARG002
        self._key_list_buffer = []

        # setup the "G0" button!
        self.G0 = Pin(0, Pin.IN, Pin.PULL_UP)
        
        # Initialize I2C bus
        i2c = I2C()
        
        try:
            self.keypad = TCA8418(i2c)

        except OSError as e:
            print(f"I2C communication error: {e}")

        self.key_state = []
        
    @micropython.viper
    def scan(self):  # noqa: ANN202
        """Scan through the matrix to see what keys are pressed."""
        key_code, is_press = self.keypad.read_key_event()
        if is_press:
            if key_code not in self._key_list_buffer:
                self._key_list_buffer.append(key_code)
        if not is_press:
            if key_code in self._key_list_buffer:
                self._key_list_buffer.remove(key_code)

        return self._key_list_buffer
    
    @staticmethod
    def ext_dir_keys(keylist) -> list:
        """Convert typical (aphanumeric) keys into extended movement-specific keys."""
        for idx, key in enumerate(keylist):
            if key in Keys.ext_dir_dict:
                keylist[idx] = Keys.ext_dir_dict[key]
        return keylist
    
    def get_pressed_keys(self, *, force_fn=False, force_shift=False) -> list:
        """Get a readable list of currently held keys.

        Also, populate self.key_state with current vals.

        Args:
        force_fn: (bool)
            If true, forces the use of 'FN' key layer
        force_shift: (bool)
            If True, forces the use of 'SHIFT' key layer
        """

        #update our scan results
        event_count = self.keypad.read_event_count()
        while event_count:
            self.scan()
            event_count = self.keypad.read_event_count()
        self.key_state = []

        if self.G0.value() == 0:
            self.key_state.append("G0")

        if not self._key_list_buffer and not self.key_state: # if nothing is pressed, we can return an empty list
            return self.key_state

        if KC_FN in self._key_list_buffer or force_fn:
            for keycode in self._key_list_buffer:
                self.key_state.append(KEYMAP_FN[keycode])

        elif KC_SHIFT in self._key_list_buffer or force_shift:
            for keycode in self._key_list_buffer:
                self.key_state.append(KEYMAP_SHIFT[keycode])

        else:
            for keycode in self._key_list_buffer:
                self.key_state.append(KEYMAP[keycode])

        return self.key_state