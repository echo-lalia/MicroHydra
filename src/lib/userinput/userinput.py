"""
This module is responsible for combining device-specific
user input modules into a single, unified API.

This module also adds some fancy extra features to that input,
such as key repetition, and global keyboard shortcuts.

!IMPORTANT NOTE!
    The API connecting _keys and userinput is almost certainly going to change!
    Do not use the _keys module directly!
"""
import time
from lib.hydra.config import Config

try:
    from . import _keys
except:
    from lib.userinput import _keys

# mh_if touchscreen:
try:
    from . import _touch
except:
    from lib.userinput import _touch
# mh_end_if



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UserInput: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UserInput(_keys.Keys):
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
    
    **kwargs :
        Passes other (device-specific) keywords to _keys.Keys
    """
    def __init__(
        self,
        hold_ms=600,
        repeat_ms=80,
        use_sys_commands=True,
        **kwargs):

        self._key_list_buffer = []
        
        self.config = Config()
        
        # key repetition
        self.tracker = {}
        self.hold_ms = hold_ms
        self.repeat_delta = hold_ms - repeat_ms

        # enable system commands
        self.use_sys_commands = use_sys_commands
        
        # init _keys.Keys
        super().__init__(**kwargs)
        
        # mh_if kb_light:
        # keyboard backlight control!
        self.set_backlight(self.config["kb_light"])
        # mh_end_if
        
        # mh_if touchscreen:
        # setup touch control!
        self.touch = _touch.Touch(i2c=self.i2c)
        self.get_touch_events = self.touch.get_touch_events
        self.get_current_points = self.touch.get_current_points
        # mh_end_if


    @micropython.viper
    def _get_new_keys(self):
        """Viper component of get_new_keys"""
        # using viper for this part is probably not critical for speed.
        # but in my experience viper tends to be much faster any time
        # iteration is involved (also seems to use less ram).
        # and so when something like this can easily be viper-ized,
        # I tend to just do it.

        tracker = self.tracker
        time_now = int(time.ticks_ms())
        hold_ms = int(self.hold_ms)
        repeat_delta = int(self.repeat_delta)
        
        # Iterate over pressed keys, keeping keys not in the tracker.
        # And, check for device-specific keys that should always be "new".
        keylist = []
        for key in self.key_state:
            if key not in tracker \
            or key in _keys.ALWAYS_NEW_KEYS:
                keylist.append(key)

        # Test if tracked keys have been held enough to repeat.
        # If they have, we can repeat them and reset the repeat time.
        # Also, don't repeat excluded keys.
        for key, key_time in tracker.items():
            if int(time.ticks_diff(time_now, key_time)) >= hold_ms \
            and key not in _keys.DONT_REPEAT_KEYS:
                keylist.append(key)
                tracker[key] = time_now - repeat_delta

        return keylist


    def get_new_keys(self):
        """
        Return a list of keys which are newly pressed.
        """
        self.populate_tracker()
        self.get_pressed_keys()
        keylist = self._get_new_keys()

        if self.use_sys_commands:
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
            
            # mh_if kb_light:
            if "b" in keylist:
                self.config["kb_light"] = not self.config["kb_light"]
                self.set_backlight(self.config["kb_light"])
                keylist.remove('b')
            # mh_end_if



if __name__ == "__main__":
    user_input = UserInput()
    while True:
        print(user_input.get_new_keys() + user_input.get_touch_events())
        time.sleep_ms(30)