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

# TCA8418 Hardware Configuration

KB_I2C_ADDR = 0x34
REG_CFG = 0x01
REG_INT_STAT = 0x02
REG_KEY_LCK_EC = 0x03
REG_KEY_EVENT_A = 0x04
REG_KP_GPIO1 = 0x1D
REG_KP_GPIO2 = 0x1E
REG_KP_GPIO3 = 0x1F

class Keys:
    """Keys class for Cardputer ADV (TCA8418 I2C)."""

    main_action = "ENT"
    secondary_action = "SPC"
    aux_action = "G0"
    ext_dir_dict = {';':'UP', ',':'LEFT', '.':'DOWN', '/':'RIGHT', '`':'ESC'}

    def __init__(self, **kwargs):
        self._key_list_buffer = []  
        self._pressed_keys_set = set() 
        
        # Setup G0 button
        self.G0 = Pin(0, Pin.IN, Pin.PULL_UP)

        # Initialize I2C (SDA=G8, SCL=G9 for StampS3). Uses the second controller (1) instead of (0) which seemed to help with stability
        self.i2c = I2C(1, scl=Pin(9), sda=Pin(8), freq=400000)
        self.kb_present = False

        try:
            self.i2c.writeto(KB_I2C_ADDR, b'')
            

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO1, b'\x7F')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO2, b'\xFF')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO3, b'\x00')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_CFG, b'\x01')
            
            # clear any stuck interrupts
            self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x03')
            
            self.kb_present = True
        except Exception as e:
            print(f"Keyboard Init Error: {e}")

        self.key_state = []

    def _tca_to_address(self, tca_val):
        """
        Converts a TCA8418 raw key code into the Python 'key_address'.
        Logic from the C++ 'remap' and 'IOMatrix' logic from the M5Stack Cardputer library for Arduino IDE.
        """
        key_id = (tca_val & 0x7F) - 1
        tca_row = key_id // 10
        tca_col = key_id % 10

        # logical_x Cardputer columns (0..13)
        # logical_y:  Cardputer rows (0..3)
        lx = (tca_row * 2) + (1 if tca_col > 3 else 0)
        ly = tca_col % 4
        
        col_idx = lx // 2
        
        # If lx is even, Upper IO MUX (rows 4-7)
        # If lx is odd, Lower IO MUX (rows 0-3)
        is_upper = (lx % 2 == 0)
        i_base = 4 if is_upper else 0
        
        #The Arduino IDE library uses uses y = 3 - (i % 4)

        row_idx = i_base + (3 - ly)
        
        # Final Python Address: (Column * 10) + Row
        address = (col_idx * 10) + row_idx
        return address

    def scan(self):
        """Reads I2C events and updates the list of held keys."""
        if not self.kb_present:
            return []
            
        try:
            # Loop max 15 times, then give up if those fail.
            for _ in range(15):
                # Check INT_STAT 
                int_stat_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_INT_STAT, 1)
                int_stat = int_stat_buf[0]
                
                if not (int_stat & 0x01):
                    break 
                
                # Check how many events
                count_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_KEY_LCK_EC, 1)
                count = count_buf[0] & 0x0F
                
                if count == 0:
                    # Clear INT manually if count = 0
                    self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x01')
                    break
                
                # Read event from i2c
                evt_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_KEY_EVENT_A, 1)
                val = evt_buf[0]
                
                # Process the event
                is_press = (val & 0x80) > 0
                address = self._tca_to_address(val)
                
                if is_press:
                    self._pressed_keys_set.add(address)
                else:
                    if address in self._pressed_keys_set:
                        self._pressed_keys_set.remove(address)
            
                # Clear INT  flagg
                self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x01')

        except Exception:
            pass

        # Convert set to list
        self._key_list_buffer = list(self._pressed_keys_set)
        return self._key_list_buffer

    @staticmethod
    def ext_dir_keys(keylist) -> list:
        for idx, key in enumerate(keylist):
            if key in Keys.ext_dir_dict:
                keylist[idx] = Keys.ext_dir_dict[key]
        return keylist

    def get_pressed_keys(self, *, force_fn=False, force_shift=False) -> list:
        """
        Get a readable list of currently held keys.
        """
        self.scan()
        self.key_state = []

        if self.G0.value() == 0:
            self.key_state.append("G0")

        if not self._key_list_buffer and not self.key_state:
            return self.key_state

        #FN / Shift logic
        fn_active = force_fn
        shift_active = force_shift

        for code in self._key_list_buffer:
            base_char = KEYMAP.get(code)
            if base_char == 'SHIFT':
                shift_active = True
            elif base_char == 'FN':
                fn_active = True

        if fn_active:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP_FN:
                    self.key_state.append(KEYMAP_FN[keycode])
        elif shift_active:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP_SHIFT:
                    self.key_state.append(KEYMAP_SHIFT[keycode])
        else:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP:
                    self.key_state.append(KEYMAP[keycode])

        return self.key_state
