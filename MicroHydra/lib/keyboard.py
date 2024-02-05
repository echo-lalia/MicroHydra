from machine import Pin
import time


#lookup values for our keyboard
kc_shift = const(61)
kc_fn = const(65)

keymap = {
    67:'`',  63:'1',  57:'2',  53:'3', 47:'4', 43:'5', 37:'6', 33:'7', 27:'8', 23:'9', 17:'0', 13:'_', 7:'=', 3:'BSPC',
    
    66:'TAB',62:'q',  56:'w',  52:'e', 46:'r', 42:'t', 36:'y', 32:'u', 26:'i', 22:'o', 16:'p', 12:'[', 6:']', 2:'\\',
    
                      55:'a',  51:'s', 45:'d', 41:'f', 35:'g', 31:'h', 25:'j', 21:'k', 15:'l', 11:';', 5:"'", 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'z', 44:'x', 40:'c', 34:'v', 30:'b', 24:'n', 20:'m', 14:',', 10:'.', 4:'/', 0:'SPC',
    }

keymap_shift = {
    67:'~',  63:'!',  57:'@',  53:'#', 47:'$', 43:'%', 37:'^', 33:'&', 27:'*', 23:'(', 17:')', 13:'-', 7:'+', 3:'BSPC',
    
    66:'TAB',62:'Q',  56:'W',  52:'E', 46:'R', 42:'T', 36:'Y', 32:'U', 26:'I', 22:'O', 16:'P', 12:'{', 6:'}', 2:'|',
    
                      55:'A',  51:'S', 45:'D', 41:'F', 35:'G', 31:'H', 25:'J', 21:'K', 15:'L', 11:':', 5:'"', 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'Z', 44:'X', 40:'C', 34:'V', 30:'B', 24:'N', 20:'M', 14:'<', 10:'>', 4:'?', 0:'SPC',
    }

keymap_fn = {
    67:'ESC',63:'F1', 57:'F2', 53:'F3',47:'F4',43:'F5',37:'F6',33:'F7',27:'F8',23:'F9',17:'F10',13:'_',7:'=', 3:'DEL',
    
    66:'TAB',62:'q',  56:'w',  52:'e', 46:'r', 42:'t', 36:'y', 32:'u', 26:'i', 22:'o', 16:'p', 12:'[', 6:']', 2:'\\',
    
                      55:'a',  51:'s', 45:'d', 41:'f', 35:'g', 31:'h', 25:'j', 21:'k', 15:'l', 11:'UP',5:"'", 1:'ENT',
    
    64:'CTL',60:'OPT',54:'ALT',50:'z', 44:'x', 40:'c', 34:'v', 30:'b', 24:'n',20:'m',14:'LEFT',10:'DOWN',4:'RIGHT',0:'SPC',
    }


class KeyBoard():
    def __init__(self):
        self._key_list_buffer = []
        
        #setup the "Go" button!
        self.go = Pin(0, Pin.IN, Pin.PULL_UP)
        
#         #setup column pins. These are read as inputs.
#         c0 = Pin(13, Pin.IN, Pin.PULL_UP)
#         c1 = Pin(15, Pin.IN, Pin.PULL_UP)
#         c2 = Pin(3, Pin.IN, Pin.PULL_UP)
#         c3 = Pin(4, Pin.IN, Pin.PULL_UP)
#         c4 = Pin(5, Pin.IN, Pin.PULL_UP)
#         c5 = Pin(6, Pin.IN, Pin.PULL_UP)
#         c6 = Pin(7, Pin.IN, Pin.PULL_UP)
#         
#         #setup row pins. These are given to a 74hc138 "demultiplexer", which lets us turn 3 output pins into 8 outputs (8 rows) 
#         a0 = Pin(8, Pin.OUT)
#         a1 = Pin(9, Pin.OUT)
#         a2 = Pin(11, Pin.OUT)
#         
#         self.pinMap = {
#             'C0': c0,
#             'C1': c1,
#             'C2': c2,
#             'C3': c3,
#             'C4': c4,
#             'C5': c5,
#             'C6': c6,
#             'A0': a0,
#             'A1': a1,
#             'A2': a2,
#         }
#         
#         self.key_state = []
        #setup column pins. These are read as inputs.

        self.c0 = Pin(13, Pin.IN, Pin.PULL_UP)
        self.c1 = Pin(15, Pin.IN, Pin.PULL_UP)
        self.c2 = Pin(3, Pin.IN, Pin.PULL_UP)
        self.c3 = Pin(4, Pin.IN, Pin.PULL_UP)
        self.c4 = Pin(5, Pin.IN, Pin.PULL_UP)
        self.c5 = Pin(6, Pin.IN, Pin.PULL_UP)
        self.c6 = Pin(7, Pin.IN, Pin.PULL_UP)
        
        #setup row pins. These are given to a 74hc138 "demultiplexer", which lets us turn 3 output pins into 8 outputs (8 rows) 
        self.a0 = Pin(8, Pin.OUT)
        self.a1 = Pin(9, Pin.OUT)
        self.a2 = Pin(11, Pin.OUT)
        
        self.key_state = []
        
        
    def scan(self):
        """scan through the matrix to see what keys are pressed."""
        
        self._key_list_buffer = []
        
        #this for loop iterates through the 8 rows of our matrix
        for row in range(0,8):
            self.a0.value(row & 0b001)
            self.a1.value( ( row & 0b010 ) >> 1)
            self.a2.value( ( row & 0b100 ) >> 2)
        
        

            #for i, col in enumerate(self.columns):
            #for i in range(0,7):
            #    if not self.columns[i].value(): # button pressed
            #        key_address = (i * 10) + row
            #        self._key_list_buffer.append(key_address)
                    
            # I know this is ugly, it should be a loop.
            # but this scan can be slow, and doing  this instead of a loop runs much faster:
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
                self.key_state.append(keymap_fn[keycode])
                
        elif kc_shift in self._key_list_buffer:
            
            #remove modifier keys which are already accounted for
            self._key_list_buffer.remove(kc_shift)
            
            for keycode in self._key_list_buffer:
                self.key_state.append(keymap_shift[keycode])
        
        else:
            for keycode in self._key_list_buffer:
                self.key_state.append(keymap[keycode])
        
        return self.key_state
            
        
        


if __name__ == "__main__":
    kb = KeyBoard()
    print(kb.get_pressed_keys())
                
        