import time
from . import _keys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ KeyBoard: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UserInput():
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
    def __init__(self, hold_ms=600, repeat_ms=80, config=None, use_sys_commands=True, **kwargs):
        self._key_list_buffer = []
        
        # TODO: make config a singleton and simplify this
        if config:
            self.config = config
        elif use_sys_commands:
            from lib import mhconfig
            self.config = mhconfig.Config()
        
        self.keys = _keys.Keys(**kwargs)
        
        self.tracker = {}
        self.hold_ms = 600
        self.repeat_delta = hold_ms - repeat_ms

        self.key_state = []

        self.sys_commands = use_sys_commands


    def get_pressed_keys(self):
        """Get a readable list of currently held keys."""
        self.key_state = self.keys.get_pressed_keys()

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
