from machine import Pin
import time

"""
lib.smartkeyboard version: 1.1
    - improved formatting
    - added option to disable sys key commands
"""

#lookup values for our keyboard
kc_shift = const(61)
kc_fn = const(65)
kc_opt = const(60)

keymap = {
    67:'`',  63:'1',  57:'2',  53:'3', 47:'4', 43:'5', 37:'6', 33:'7', 27:'8', 23:'9', 17:'0', 13:'_', 7:'=', 3:'BSPC',

    66:'TAB',62:'q',  56:'w',  52:'e', 46:'r', 42:'t', 36:'y', 32:'u', 26:'i', 22:'o', 16:'p', 12:'[', 6:']', 2:'\\',

                      55:'a',  51:'s', 45:'d', 41:'f', 35:'g', 31:'h', 25:'j', 21:'k', 15:'l', 11:';', 5:"'", 1:'ENT',

    64:'CTL',60:'OPT',54:'ALT',50:'z', 44:'x', 40:'c', 34:'v', 30:'b', 24:'n', 20:'m', 14:',', 10:'.', 4:'/', 0:'SPC',
    }

keymap_shift = {
    67:'~',  63:'!',  57:'@',  53:'#', 47:'$', 43:'%', 37:'^', 33:'&', 27:'*', 23:'(', 17:')', 13:'-', 7:'+',

             62:'Q',  56:'W',  52:'E', 46:'R', 42:'T', 36:'Y', 32:'U', 26:'I', 22:'O', 16:'P', 12:'{', 6:'}', 2:'|',

                      55:'A',  51:'S', 45:'D', 41:'F', 35:'G', 31:'H', 25:'J', 21:'K', 15:'L', 11:':', 5:'"',

                               50:'Z', 44:'X', 40:'C', 34:'V', 30:'B', 24:'N', 20:'M', 14:'<', 10:'>', 4:'?',
    }

keymap_fn = {
    67:'ESC', 63:'F1', 57:'F2', 53:'F3',47:'F4',43:'F5',37:'F6',33:'F7',27:'F8',23:'F9',17:'F10',13:'_',7:'=', 3:'DEL',

                                                                                                 11:'UP',
                                                                                       14:'LEFT',10:'DOWN',4:'RIGHT'
    }

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ KeyBoard: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class KeyBoard():
    """
    Smart Keyboard Class
    
    
    Args:
    =====
    
    hold_ms : int = 600
        how long a key must be held before repeating
    
    repeat_ms : int = 80
        how long between key repetitions
    
    config : Config|None = None
        your MH config instance. If not provided, it is created automatically.
        
    use_sys_commands : bool = True
        whether or not to enable 'global' system commands.
        If enabled, removes 'opt' key presses and changes config using keyboard shortcuts.
    
    """
    def __init__(self, hold_ms=600, repeat_ms=80, config=None, use_sys_commands=True):
        self._key_list_buffer = []

        if config:
            self.config = config
        elif use_sys_commands:
            from lib import mhconfig
            self.config = mhconfig.Config()

        self.tracker = {}
        self.hold_ms=600
        self.repeat_delta = hold_ms - repeat_ms

        #setup the "Go" button!
        self.go = Pin(0, Pin.IN, Pin.PULL_UP)

        #setup column pins. These are read as inputs.
        self.c0 = Pin(13, Pin.IN, Pin.PULL_UP)
        self.c1 = Pin(15, Pin.IN, Pin.PULL_UP)
        self.c2 = Pin(3, Pin.IN, Pin.PULL_UP)
        self.c3 = Pin(4, Pin.IN, Pin.PULL_UP)
        self.c4 = Pin(5, Pin.IN, Pin.PULL_UP)
        self.c5 = Pin(6, Pin.IN, Pin.PULL_UP)
        self.c6 = Pin(7, Pin.IN, Pin.PULL_UP)

        # setup row pins. These are given to a 74hc138 "demultiplexer",
        # which lets us turn 3 output pins into 8 outputs (8 rows)
        self.a0 = Pin(8, Pin.OUT)
        self.a1 = Pin(9, Pin.OUT)
        self.a2 = Pin(11, Pin.OUT)

        self.key_state = []

        self.sys_commands = use_sys_commands


    def scan(self):
        """scan through the matrix to see what keys are pressed."""

        self._key_list_buffer = []

        #this for loop iterates through the 8 rows of our matrix
        for row in range(0,8):
            self.a0.value(row & 0b001)
            self.a1.value( ( row & 0b010 ) >> 1)
            self.a2.value( ( row & 0b100 ) >> 2)

            if not self.c6.value():
                self._key_list_buffer.append(row)
            if not self.c5.value():
                self._key_list_buffer.append(10 + row)
            if not self.c4.value():
                self._key_list_buffer.append(20 + row)
            if not self.c3.value():
                self._key_list_buffer.append(30 + row)
            if not self.c2.value():
                self._key_list_buffer.append(40 + row)
            if not self.c1.value():
                self._key_list_buffer.append(50 + row)
            if not self.c0.value():
                self._key_list_buffer.append(60 + row)

        return self._key_list_buffer


    def get_pressed_keys(self):
        """Get a readable list of currently held keys."""

        #update our scan results
        self.scan()
        self.key_state = []

        if self.go.value() == 0:
            self.key_state.append("GO")

        if not self._key_list_buffer and not self.key_state: # if nothing is pressed, we can return an empty list
            return self.key_state

        if kc_fn in self._key_list_buffer:
            #remove modifier keys which are already accounted for
            self._key_list_buffer.remove(kc_fn)
            if kc_shift in self._key_list_buffer:
                self._key_list_buffer.remove(kc_shift)

            for keycode in self._key_list_buffer:
                # get fn keymap, or default to normal keymap
                self.key_state.append(
                    keymap_fn.get(keycode, keymap[keycode])
                    )

        elif kc_shift in self._key_list_buffer:
            #remove modifier keys which are already accounted for
            self._key_list_buffer.remove(kc_shift)

            for keycode in self._key_list_buffer:
                # get fn keymap, or default to normal keymap
                self.key_state.append(
                    keymap_shift.get(keycode, keymap[keycode])
                    )

        else:
            for keycode in self._key_list_buffer:
                self.key_state.append(keymap[keycode])

        return self.key_state


    def get_new_keys(self):
        """
        Return a list of keys which are newly pressed.
        """
        self.populate_tracker()
        self.get_pressed_keys()

        keylist = [key for key in self.key_state if key not in self.tracker]

        for key, key_time in self.tracker.items():
            # test if keys have been held long enough to repeat
            if time.ticks_diff(time.ticks_ms(), key_time) >= self.hold_ms:
                keylist.append(key)
                self.tracker[key] = time.ticks_ms() - self.repeat_delta

        if self.sys_commands:
            self.system_commands(keylist)

        return keylist


    def populate_tracker(self):
        """Move currently pressed keys to tracker"""
        # add new keys
        for key in self.key_state:
            if key not in self.tracker.keys():
                self.tracker[key] = time.ticks_ms()

        # remove keys that arent being pressed from tracker
        for key in self.tracker.keys():
            if key not in self.key_state:
                self.tracker.pop(key)


    def system_commands(self, keylist):
        """Check for system commands in the keylist and apply to config"""
        if 'OPT' in self.key_state:
            # system commands are bound to 'OPT': remove OPT and apply commands
            if 'OPT' in keylist:
                keylist.remove('OPT')

            # mute/unmute
            if 'm' in keylist:
                self.config['ui_sound'] = not self.config['ui_sound']
                keylist.remove('m')

            # vol up
            if ';' in keylist:
                self.config['volume'] = (self.config['volume'] + 1) % 11
                keylist.remove(';')

            # vol down
            elif '.' in keylist:
                self.config['volume'] = (self.config['volume'] - 1) % 11
                keylist.remove('.')


if __name__ == "__main__":
    kb = KeyBoard()
    for _ in range(0,4000):
        print('')
        print(kb.get_new_keys())
        print(kb.config.config)
        print('')
        time.sleep_ms(50)
                
        
