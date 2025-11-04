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

        # setup the "G0" button!
        self.G0 = Pin(0, Pin.IN, Pin.PULL_UP)

        # setup column pins. These are read as inputs.
        c0 = Pin(13, Pin.IN, Pin.PULL_UP)
        c1 = Pin(15, Pin.IN, Pin.PULL_UP)
        c2 = Pin(3, Pin.IN, Pin.PULL_UP)
        c3 = Pin(4, Pin.IN, Pin.PULL_UP)
        c4 = Pin(5, Pin.IN, Pin.PULL_UP)
        c5 = Pin(6, Pin.IN, Pin.PULL_UP)
        c6 = Pin(7, Pin.IN, Pin.PULL_UP)
        self.columns = (c6, c5, c4, c3, c2, c1, c0)

        # setup row pins.
        # These are given to a 74hc138 "demultiplexer", which lets us turn 3 output pins into 8 outputs (8 rows)
        self.a0 = Pin(8, Pin.OUT)
        self.a1 = Pin(9, Pin.OUT)
        self.a2 = Pin(11, Pin.OUT)

        self.key_state = []

    @micropython.viper
    def scan(self):  # noqa: ANN202
        """Scan through the matrix to see what keys are pressed."""
        key_list_buffer = []
        self._key_list_buffer = key_list_buffer

        columns = self.columns

        a0 = self.a0
        a1 = self.a1
        a2 = self.a2

        #this for loop iterates through the 8 rows of our matrix
        row_idx = 0
        while row_idx < 8:
            a0.value(row_idx & 0b001)
            a1.value(( row_idx & 0b010 ) >> 1)
            a2.value(( row_idx & 0b100 ) >> 2)

            # iterate through each column
            col_idx = 0
            while col_idx < 7:
                if not columns[col_idx].value(): # button pressed
                    # pack column/row into one integer
                    key_address = (col_idx * 10) + row_idx
                    key_list_buffer.append(key_address)

                col_idx += 1

            row_idx += 1

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

