"""
Read and return keyboard data for the M5Stack Cardputer
"""
from machine import Pin


#lookup values for our keyboard
KC_SHIFT = const(61)
KC_FN = const(65)

KEYMAP = {
    67:'`',  63:'1',  57:'2',  53:'3', 47:'4', 43:'5', 37:'6', 33:'7', 27:'8', 23:'9', 17:'0', 13:'_', 7:'=', 3:'BSPC',
    
    66:'TAB',62:'q',  56:'w',  52:'e', 46:'r', 42:'t', 36:'y', 32:'u', 26:'i', 22:'o', 16:'p', 12:'[', 6:']', 2:'\\',
    
    65:"FN",61:"SHIFT",55:'a', 51:'s', 45:'d', 41:'f', 35:'g', 31:'h', 25:'j', 21:'k', 15:'l', 11:';', 5:"'", 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'z', 44:'x', 40:'c', 34:'v', 30:'b', 24:'n', 20:'m', 14:',', 10:'.', 4:'/', 0:'SPC',
    }

KEYMAP_SHIFT = {
    67:'~',  63:'!',  57:'@',  53:'#', 47:'$', 43:'%', 37:'^', 33:'&', 27:'*', 23:'(', 17:')', 13:'-', 7:'+', 3:'BSPC',
    
    66:'TAB',62:'Q',  56:'W',  52:'E', 46:'R', 42:'T', 36:'Y', 32:'U', 26:'I', 22:'O', 16:'P', 12:'{', 6:'}', 2:'|',
    
    65:"FN",61:"SHIFT",55:'A', 51:'S', 45:'D', 41:'F', 35:'G', 31:'H', 25:'J', 21:'K', 15:'L', 11:':', 5:'"', 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'Z', 44:'X', 40:'C', 34:'V', 30:'B', 24:'N', 20:'M', 14:'<', 10:'>', 4:'?', 0:'SPC',
    }

KEYMAP_FN = {
    67:'ESC',63:'F1', 57:'F2', 53:'F3',47:'F4',43:'F5',37:'F6',33:'F7',27:'F8',23:'F9',17:'F10',13:'_',7:'=', 3:'DEL',
    
    66:'TAB',62:'q',  56:'w',  52:'e', 46:'r', 42:'t', 36:'y', 32:'u', 26:'i', 22:'o', 16:'p', 12:'[', 6:']', 2:'\\',
    
    65:"FN",61:"SHIFT",55:'a', 51:'s', 45:'d', 41:'f', 35:'g', 31:'h', 25:'j', 21:'k', 15:'l', 11:'UP',5:"'", 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'z', 44:'x', 40:'c', 34:'v', 30:'b', 24:'n',20:'m',14:'LEFT',10:'DOWN',4:'RIGHT',0:'SPC',
    }


MOD_KEYS = const(('ALT', 'CTRL', 'FN', 'SHIFT', 'OPT'))
ALWAYS_NEW_KEYS = const(())


class Keys():
    """
    Keys class is responsible for reading and returning currently pressed keys.
    It is intented to be used by the Input module.
    """
    def __init__(self, **kwargs):
        self._key_list_buffer = []
        
        #setup the "Go" button!
        self.go = Pin(0, Pin.IN, Pin.PULL_UP)

        #setup column pins. These are read as inputs.
        c0 = Pin(13, Pin.IN, Pin.PULL_UP)
        c1 = Pin(15, Pin.IN, Pin.PULL_UP)
        c2 = Pin(3, Pin.IN, Pin.PULL_UP)
        c3 = Pin(4, Pin.IN, Pin.PULL_UP)
        c4 = Pin(5, Pin.IN, Pin.PULL_UP)
        c5 = Pin(6, Pin.IN, Pin.PULL_UP)
        c6 = Pin(7, Pin.IN, Pin.PULL_UP)
        self.columns = (c6, c5, c4, c3, c2, c1, c0)
        
        #setup row pins. These are given to a 74hc138 "demultiplexer", which lets us turn 3 output pins into 8 outputs (8 rows) 
        self.a0 = Pin(8, Pin.OUT)
        self.a1 = Pin(9, Pin.OUT)
        self.a2 = Pin(11, Pin.OUT)
        
        self.key_state = []

    @micropython.viper
    def scan(self):
        """scan through the matrix to see what keys are pressed."""
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


    def get_pressed_keys(self, force_fn=False, force_shift=False):
        """
        Get a readable list of currently held keys.
        Also, populate self.key_state with current vals.
        
        Args:
        =====

        force_fn : bool = False
            If true, forces the use of 'FN' key layer

        force_shift : bool - False
            If True, forces the use of 'SHIFT' key layer
        
        """
        
        #update our scan results
        self.scan()
        self.key_state = []
        
        if self.go.value() == 0:
            self.key_state.append("GO")
        
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