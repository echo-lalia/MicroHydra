"""Read and return keyboard data for the PicoCalc."""

from machine import Pin, I2C
import time


_REG_VER = const(0x01) # fw version
_REG_CFG = const(0x02) # config
_REG_INT = const(0x03) # interrupt status
_REG_KEY_STAT = const(0x04) # key status
_REG_DISP_BLIGHT = const(0x05) # backlight
_REG_DEB = const(0x06) # debounce cfg
_REG_FRQ = const(0x07) # poll freq cfg
_REG_RST = const(0x08) # reset
_REG_FIFO = const(0x09) # fifo
_REG_KB_BLIGHT = const(0x0A) # backlight 2
_REG_BAT = const(0x0B) # battery
_REG_DIR = const(0x0C) # gpio direction
_REG_PUE = const(0x0D) # gpio input pull enable
_REG_PUD = const(0x0E) # gpio input pull direction
_REG_GIO = const(0x0F) # gpio value
_REG_GIC = const(0x10) # gpio interrupt config
_REG_GIN = const(0x11) # gpio interrupt status

_KEY_COUNT_MASK = const(0x1F)
_WRITE_FLAG = const(1 << 7)

_STATE_PRESSED = const(1)
_STATE_HELD = const(2)
_STATE_RELEASED = const(3)


#lookup values for our keyboard
_KC_LEFT_SHIFT = const(162)
_KC_SHIFT = const(163)
_KC_G0 = const(145)
_KC_CAPS = const(193)

# milliseconds it takes for (potentially stuck) keycodes to be cleared when no key information is given.
_AUTO_CLEAR_TIME = const(400)


# map keycodes that refer to the same keys (convert 'smart' key codes back to hardware key presses)
HARDMAP = {
          214:181,            134:129,   135:130,   136:131,   137:132,   144:133,
                              208:177,   210:9,                213:212,
          215:182,            126:96,   63:47,  124:92,   95:45,  43:61, 123:91, 125:93,
    33:49,  64:50,  35:51,  36:52,  37:53,  94:54,  38:55,   42:56,  40:57,  41:48,
    81:133, 87:119, 69:101, 82:114, 84:116, 89:121, 85:117,  73:105, 79:111, 80:112,
                                                           # 209:105, <- this keycode is also sent by the enter button!
    65:97,  83:115, 68:100, 70:102, 71:103, 72:104, 74:106, 75:107, 76:108,  209:10,
    90:122, 88:120, 67:99,  86:118, 66:98,  78:110, 77:109, 60:44,  62:46,
                                                            58:59,  34:39,
    }

KEYMAP = {
          181:'UP',            129:'F1',      130:'F2',    131:'F3',       132:'F4',       133:'F5',
    180:'LEFT', 183:'RIGHT',   177:'ESC',     9:'TAB',                     212:'DEL',      8:'BSPC',
          182:'DOWN',             96:'`',   47:'/',   92:'\\',  45:'-',    61:'=',   91:'[',   93:']',
     49:'1',   50:'2',   51:'3',   52:'4',   53:'5',   54:'6',   55:'7',   56:'8',   57:'9',   48:'0',
    113:'q',  119:'w',  101:'e',  114:'r',  116:'t',  121:'y',  117:'u',  105:'i',  111:'o',  112:'p',
     97:'a',  115:'s',  100:'d',  102:'f',  103:'g',  104:'h',  106:'j',  107:'k',  108:'l',
    122:'z',  120:'x',   99:'c',  118:'v',   98:'b',  110:'n',  109:'m',   44:',',   46:'.',  10:'ENT',
      162:'SHIFT',     165:'CTL',    161:'ALT',    32:'SPC',    59:';',    39:"'",    163:'SHIFT',
}

KEYMAP_SHIFT = {
          181:'UP',            129:'F6',      130:'F7',    131:'F8',       132:'F9',       133:'F10',
    180:'LEFT', 183:'RIGHT',   177:'BREAK',     9:'HOME',                  212:'END',       8:'BSPC',
          182:'DOWN',              96:'~',   47:'?',   92:'|',   45:'_',   61:'+',   91:'{',   93:'}',
     49:'!',   50:'@',   51:'#',   52:'$',   53:'%',   54:'^',   55:'&',   56:'*',   57:'(',   48:')',
    113:'Q',  119:'W',  101:'E',  114:'R',  116:'T',  121:'Y',  117:'U',  105:'I',  111:'O',  112:'P',
     97:'A',  115:'S',  100:'D',  102:'F',  103:'G',  104:'H',  106:'J',  107:'K',  108:'L',
    122:'Z',  120:'X',   99:'C',  118:'V',   98:'B',  110:'N',  109:'M',   44:'<',   46:'>',  10:'ENT',
      162:'SHIFT',     165:'CTL',   161:'ALT',    32:'SPC',    59:':',     39:'"',     163:'SHIFT',
}



MOD_KEYS = const(('ALT', 'CTL', 'SHIFT', 'OPT'))
ALWAYS_NEW_KEYS = const(('G0',))


_I2C_ADDR = const(0x1f)


class Keys:
    """Keys class is responsible for reading and returning currently pressed keys.

    It is intented to be used by the Input module.
    """

    # optional values set preferred main/secondary action keys:
    main_action = "ENT"
    secondary_action = "SPC"
    aux_action = "G0"

    ext_dir_dict = {}

    def __init__(self, **kwargs):  # noqa: ARG002
        self._key_list_buffer = []

        self.i2c = I2C(
            1,
            scl=Pin(7),
            sda=Pin(6),
            freq=20_000,
        )

        self.key_state = []
        
        # Track the amount of time that the keyboard has reported no new key information. (used for automatically fixing stuck keys)
        self.empty_read_start = 0
        
        self.caps = False


    @staticmethod
    def ext_dir_keys(keylist) -> list:
        """Convert typical (aphanumeric) keys into extended movement-specific keys."""
        for idx, key in enumerate(keylist):
            if key in Keys.ext_dir_dict:
                keylist[idx] = Keys.ext_dir_dict[key]
        return keylist


    def set_backlight(self, val: int):
        """Set the keyboard backlight to val (int from 0 to 255)."""
        self.i2c.writeto_mem(_I2C_ADDR, _REG_KB_BLIGHT | _WRITE_FLAG, bytearray([val]))


    def set_display_light(self, val: int):
        """Set the display backlight to val (int from 0 to 255)."""
        self.i2c.writeto_mem(_I2C_ADDR, _REG_DISP_BLIGHT | _WRITE_FLAG, bytearray([val]))


    @micropython.viper
    def get_batt_pct(self) -> int:
        """Get the battery level as a percentage."""
        # I have no idea why we need to take the right bits only;
        # I'm just copying the test_battery function from the official helloworld firmware.
        return (ptr8(self.i2c.readfrom_mem(_I2C_ADDR, _REG_BAT, 2))[1] & 0b0111_1111) 


    def capitalize(self):
        """Capitalize the pressed keys (if caps lock is on)."""
        for i in range(len(self.key_state)):
            self.key_state[i] = self.key_state[i].upper()


    def _get_num_keycodes(self) -> int:
        return self.i2c.readfrom_mem(_I2C_ADDR, _REG_KEY_STAT, 1)[0] & _KEY_COUNT_MASK


    def get_pressed_keys(self, *, force_fn=False, force_shift=False) -> list:
        """Get a readable list of currently held keys.

        Also, populate self.key_state with current vals.

        Args:
        force_fn: (bool)
            Provided only for compatibility.
        force_shift: (bool)
            If True, forces the use of 'SHIFT' key layer
        """
        num_codes = self._get_num_keycodes()
        
        # Track time since empty key reads started so we can fix stuck keys
        # When a key is first pressed, it will be absent from a little bit before _STATE_PRESSED codes start
        if num_codes == 0:
            if self._key_list_buffer:
                if self.empty_read_start == -1:
                    self.empty_read_start = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(), self.empty_read_start) > _AUTO_CLEAR_TIME:
                    self.empty_read_start = -1
                    self._key_list_buffer.clear()
        else:
            self.empty_read_start = -1
            # Read key press/release events from keyboard,
            # and flatten them so that each button is represented by one code (as much as possible).
            for _ in range(num_codes):
                state, code = self.i2c.readfrom_mem(_I2C_ADDR, _REG_FIFO, 2)
                code = HARDMAP.get(code, code)
                if state == _STATE_PRESSED and code not in self._key_list_buffer:
                    self._key_list_buffer.append(code)
                elif state == _STATE_RELEASED and code in self._key_list_buffer:
                    self._key_list_buffer.remove(code)

        # Early return for no keys
        if not self._key_list_buffer and not self.key_state:
            return self.key_state

        self.key_state.clear()
        
        if _KC_CAPS in self._key_list_buffer:
            self.caps = not self.caps
            self._key_list_buffer.remove(_KC_CAPS)

        # G0 key doesn't send `_STATE_RELEASED`, so it needs to be manually handled.
        if _KC_G0 in self._key_list_buffer:
            self.key_state.append('G0')
            self._key_list_buffer.remove(_KC_G0)

        # Interpret using SHIFT keymap
        if _KC_SHIFT in self._key_list_buffer or _KC_LEFT_SHIFT in self._key_list_buffer or force_shift:
            for code in self._key_list_buffer:
                self.key_state.append(KEYMAP_SHIFT[code])
        # Standard keymap.
        else:
            for code in self._key_list_buffer:
                self.key_state.append(KEYMAP[code])
        
        # Shortcut for 'OPT' key
        if _KC_SHIFT in self._key_list_buffer and _KC_LEFT_SHIFT in self._key_list_buffer:
            self.key_state.append('OPT')
            while "SHIFT" in self.key_state:
                self.key_state.remove("SHIFT")
        
        if self.caps:
            self.capitalize()

        return self.key_state
