"""Read and return keyboard data for the M5Stack Cardputer Advanced."""
from machine import Pin, I2C
import time

KC_SHIFT = const(61)
KC_FN = const(65)
KEYMAP = {
    0:'`',   4:'1',     8:'2',    12:'3', 16:'4', 20:'5', 24:'6', 28:'7', 32:'8', 36:'9', 40:'0', 44:'-', 48:'=', 52:'BSPC',
    1:'TAB', 5:'q',     9:'w',    13:'e', 17:'r', 21:'t', 25:'y', 29:'u', 33:'i', 37:'o', 41:'p', 45:'[', 49:']', 53:'\\',
    2:"FN",  6:"SHIFT", 10:'a',   14:'s', 18:'d', 22:'f', 26:'g', 30:'h', 34:'j', 38:'k', 42:'l', 46:';', 50:"'", 54:'ENT',
    3:'CTL', 7:'OPT',   11:'ALT', 15:'z', 19:'x', 23:'c', 27:'v', 31:'b', 35:'n', 39:'m', 43:',', 47:'.', 51:'/', 55:'SPC',
    }

KEYMAP_SHIFT = {
    0:'~',   4:'!',     8:'@',    12:'#', 16:'$', 20:'%', 24:'^', 28:'&', 32:'*', 36:'(', 40:')', 44:'_', 48:'+', 52:'BSPC',
    1:'TAB', 5:'Q',     9:'W',    13:'E', 17:'R', 21:'T', 25:'Y', 29:'U', 33:'I', 37:'O', 41:'P', 45:'{', 49:'}', 53:'|',
    2:"FN",  6:"SHIFT", 10:'A',   14:'S', 18:'D', 22:'F', 26:'G', 30:'H', 34:'J', 38:'K', 42:'L', 46:':', 50:'"', 54:'ENT',
    3:'CTL', 7:'OPT',   11:'ALT', 15:'Z', 19:'X', 23:'C', 27:'V', 31:'B', 35:'N', 39:'M', 43:'<', 47:'>', 51:'/', 55:'SPC',
    }

KEYMAP_FN = {
    0:'ESC', 4:'F1',    8:'F2',   12:'F3', 16:'F4', 20:'F5', 24:'F6', 28:'F7', 32:'F8', 36:'F9', 40:'F10',    44:'-',    48:'=', 52:'DEL',
    1:'TAB', 5:'q',     9:'w',    13:'e',  17:'r',  21:'t',  25:'y',  29:'u',  33:'i',  37:'o',  41:'p',      45:'[',    49:']', 53:'\\',
    2:"FN",  6:"SHIFT", 10:'a',   14:'s',  18:'d',  22:'f',  26:'g',  30:'h',  34:'j',  38:'k',  42:'l',      46:'UP',   50:"'", 54:'ENT',
    3:'CTL', 7:'OPT',   11:'ALT', 15:'z',  19:'x',  23:'c',  27:'v',  31:'b',  35:'n',  39:'m',  43:'LEFT',   47:'DOWN', 51:'RIGHT', 55:'SPC', # noqa: E501
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
        # Initialize I2C for TCA8418
        self.i2c = I2C(
            0,          # I2C bus ID
            scl=Pin(9),
            sda=Pin(8),
            freq=400000
        )

        # INT pin
        self.int_pin = Pin(11, Pin.IN)

        # TCA8418 I2C address (check your board, usually 0x34)
        self.addr = 0x34
        
        # setup the "G0" button!
        self.G0 = Pin(0, Pin.IN, Pin.PULL_UP)

        self.key_state = []

    def scan(self):
        """Scan the keypad using TCA8418 over I2C."""
        key_list_buffer = []
        self._key_list_buffer = key_list_buffer

        # TCA8418 registers (from datasheet)
        KEY_LSB_REG = 0x03  # First key pressed LSB
        KEY_MSB_REG = 0x04  # First key pressed MSB
        # Alternatively, you can read 2 bytes from KEY_LSB_REG to get all keys

        # Read 2 bytes of key data
        try:
            data = self.i2c.readfrom_mem(self.addr, KEY_LSB_REG, 2)
            key_lsb = data[0]
            key_msb = data[1]

            # Each bit represents a key in the matrix (0 = pressed)
            for row in range(8):
                for col in range(7):
                    key_idx = row * 7 + col
                    if key_idx < 8:
                        pressed = not (key_lsb & (1 << key_idx))
                    else:
                        pressed = not (key_msb & (1 << (key_idx - 8)))

                    if pressed:
                        key_address = (col * 10) + row  # keep old format
                        key_list_buffer.append(key_address)

        except Exception as e:
            print("I2C read failed:", e)

        return key_list_buffer



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
        self.scan()
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

