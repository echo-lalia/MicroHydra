"""This module is responsible for combining device-specific input modules into a single, unified API.

This module also adds some fancy extra features to that input,
such as key repetition, and global keyboard shortcuts.

!IMPORTANT NOTE!
    The API connecting _keys and userinput is almost certainly going to change!
    Do not use the _keys module directly!
"""
import time
from lib.hydra.config import Config
from lib.display import Display
import machine
from . import _keys

# mh_if touchscreen:
from . import _touch
# mh_end_if



# Used for drawing locked keys to display:
_PADDING = const(3)
_FONT_WIDTH = const(8)
_FONT_HEIGHT = const(8)
_BOX_HEIGHT = const(_FONT_HEIGHT + (_PADDING * 2) + 1)
_RADIUS = const((_BOX_HEIGHT - 1) // 2)



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UserInput: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UserInput(_keys.Keys):
    """Smart Keyboard Class.

    Args:
    =====

    hold_ms : int = 600
        how long a key must be held before repeating

    repeat_ms : int = 80
        how long between key repetitions

    use_sys_commands : bool = True
        whether or not to enable 'global' system commands.
        If enabled, removes 'opt' key presses and changes config using keyboard shortcuts.

    allow_locking_keys : bool = True
        Set to False to disable locking modifier keys (True uses the value in config.json).

    **kwargs :
        Passes other (device-specific) keywords to _keys.Keys
    """

    def __init__(
        self,
        *,
        hold_ms=600,
        repeat_ms=80,
        use_sys_commands=True,
        allow_locking_keys=False,
        **kwargs):
        """Initialize the input drivers with the given settings."""
        self.config = Config()

        # key repetition / locking keys
        self.tracker = {}
        self.hold_ms = hold_ms
        self.repeat_delta = hold_ms - repeat_ms

        self.locking_keys = allow_locking_keys
        self.locked_keys = []

        # enable system commands
        self.use_sys_commands = use_sys_commands

        # setup locked key overlay:
        Display.overlay_callbacks.append(self._locked_keys_overlay)

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



    def __new__(cls, **kwargs):  # noqa: ARG003, D102
        if not hasattr(cls, 'instance'):
          cls.instance = super().__new__(cls)
        return cls.instance



    @micropython.viper
    def _get_new_keys(self) -> list[str]:
        """Viper component of get_new_keys."""
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
                keylist.append(key)  # noqa: PERF401

        # Test if tracked keys have been held enough to repeat.
        # If they have, we can repeat them and reset the repeat time.
        # Also, don't repeat modifier` keys.
        for key, key_time in tracker.items():
            if key not in _keys.MOD_KEYS \
            and int(time.ticks_diff(time_now, key_time)) >= hold_ms:
                keylist.append(key)
                tracker[key] = time_now - repeat_delta

        return keylist


    def get_new_keys(self) -> list[str]:
        """Return a list of keys which are newly pressed."""
        self.populate_tracker()

        if self.locking_keys:
            self.handle_locking_keys()

        self.get_pressed_keys()
        keylist = self._get_new_keys()

        if self.use_sys_commands:
            self.system_commands(keylist)

        return keylist


    def get_pressed_keys(self) -> list[str]:
        """Get list of currently pressed keys."""
        return super().get_pressed_keys(
            force_fn=('FN' in self.locked_keys),
            force_shift=('SHIFT' in self.locked_keys),
            )


    def get_mod_keys(self) -> list[str]:
        """Return modifier keys that are being held, or that are currently locked."""
        return [key for key in self.key_state + self.locked_keys if key in _keys.MOD_KEYS]


    def populate_tracker(self):
        """Move currently pressed keys to tracker."""
        # add new keys
        for key in self.key_state:
            if key not in self.tracker:

                # mod keys lock rather than repeat
                if self.locking_keys \
                and key in _keys.MOD_KEYS:
                    # True means key can be locked
                    self.tracker[key] = True
                else:
                    # Remember when key was pressed for key-repeat behavior
                    self.tracker[key] = time.ticks_ms()

        # remove keys that aren't being pressed from tracker
        # (mod keys are removed in handle_locking_keys)
        for key in self.tracker:
            if key not in self.key_state \
            and (self.locking_keys is False
            or key not in _keys.MOD_KEYS):
                self.tracker.pop(key)


    def handle_locking_keys(self):
        """Handle 'locking' behaviour of modifier keys."""
        tracker = self.tracker
        locked_keys = self.locked_keys

        # iterate over mod keys in tracker:
        for key in tracker:
            if key in _keys.MOD_KEYS:

                # pre-fetch for easier readability:
                tracker_val = tracker[key]
                in_locked_keys = key in locked_keys
                is_being_pressed = key in self.key_state

                # when mod key is pressed, val is True
                # becomes False when any other key is pressed at the same time
                # if not pressed and still True, then lock the mod key
                # remove locked mod key when pressed again.

                if tracker_val: # is True
                    if is_being_pressed:
                        # key is being pressed and val is True
                        if in_locked_keys:
                            # key already in locked keys, must have been pressed twice.
                            locked_keys.remove(key)
                            tracker[key] = False

                        elif len(self.key_state) > 1:
                            # multiple keys are being pressed together, dont lock this key
                            tracker[key] = False
                    else:
                        # key has just been released and should be locked
                        locked_keys.append(key)
                        tracker.pop(key)

                # tracker val is False
                elif not is_being_pressed:
                    # if not being pressed and not locking, then just remove it
                    tracker.pop(key)


    def system_commands(self, keylist):
        """Check for system commands in the keylist and apply to config."""
        if 'OPT' in self.key_state:
            # system commands are bound to 'OPT': remove OPT and apply commands
            if 'OPT' in keylist:
                keylist.remove('OPT')

            # mute/unmute
            if 'm' in keylist:
                self.config['ui_sound'] = not self.config['ui_sound']
                keylist.remove('m')

            # vol up
            if 'UP' in keylist:
                self.config['volume'] = (self.config['volume'] + 1) % 11
                keylist.remove('UP')

            # vol down
            elif 'DOWN' in keylist:
                self.config['volume'] = (self.config['volume'] - 1) % 11
                keylist.remove('DOWN')

            if "q" in keylist:
                machine.RTC().memory("")
                machine.reset()

            # mh_if kb_light:
            if "b" in keylist:
                self.config["kb_light"] = not self.config["kb_light"]
                self.set_backlight(self.config["kb_light"])
                keylist.remove('b')
            # mh_end_if


    def _locked_keys_overlay(self, display):
        """Draw currently locked keys to the display."""
        width = display.width

        for key_txt in self.locked_keys:
            box_width = (len(key_txt) * _FONT_WIDTH)
            x = width - box_width - _PADDING - _RADIUS
            key_idx = _keys.MOD_KEYS.index(key_txt)
            txt_clr = key_idx % 3
            bg_clr = (key_idx % 3) + 6
            ex_clr = 11 + key_idx

            # bg
            display.rect(x, 1, box_width, _BOX_HEIGHT, display.palette[bg_clr], fill=True)
            display.ellipse(x, _RADIUS + 1, _RADIUS, _RADIUS, display.palette[bg_clr], fill=True, m=6)
            display.ellipse(x + box_width, _RADIUS + 1, _RADIUS, _RADIUS, display.palette[bg_clr], fill=True, m=9)

            # outline
            display.hline(x, 1, box_width, display.palette[ex_clr])
            display.hline(x, _BOX_HEIGHT, box_width, display.palette[ex_clr])
            display.ellipse(x, _RADIUS + 1, _RADIUS, _RADIUS, display.palette[ex_clr], fill=False, m=6)
            display.ellipse(x + box_width, _RADIUS + 1, _RADIUS, _RADIUS, display.palette[ex_clr], fill=False, m=9)

            display.text(key_txt, x, _PADDING + 2, display.palette[txt_clr])
            width = x - _RADIUS - _PADDING

