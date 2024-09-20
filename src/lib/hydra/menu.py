"""This module provides an API for creating menus.

lib/Settings.py uses this module heavily.
"""

import array
import math
import time

from font import vga2_16x32 as font
from lib.display import Display
from lib.userinput import UserInput

from . import beeper, color
from .config import Config
from .utils import get_instance


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_WIDTH = const(240)
_MH_DISPLAY_HEIGHT = const(135)

_DISPLAY_WIDTH_CENTER = const(_MH_DISPLAY_WIDTH//2)
_DISPLAY_CENTER_LEFT = const(_DISPLAY_WIDTH_CENTER//2)
_DISPLAY_CENTER_RIGHT = const(_DISPLAY_WIDTH_CENTER+_DISPLAY_CENTER_LEFT)

# scrollbar
_SCROLLBAR_WIDTH = const(2)
_SCROLLBAR_X = const(_MH_DISPLAY_WIDTH-_SCROLLBAR_WIDTH)
_SCROLLBAR_BUFFER_WIDTH = const(4)
_SCROLLBAR_BUFFER_X = const(_SCROLLBAR_X-_SCROLLBAR_BUFFER_WIDTH)

_FONT_HEIGHT = const(32) # big font height
_FONT_WIDTH = const(16) # big font width
_FONT_HEIGHT_HALF = const(_FONT_HEIGHT//2)
_FONT_WIDTH_HALF = const(_FONT_WIDTH//2)

_SMALL_FONT_HEIGHT = const(8) # small font height
_SMALL_FONT_HEIGHT_HALF = const(_SMALL_FONT_HEIGHT//2)
_SMALL_FONT_WIDTH = const(8) # small font width
_SMALL_FONT_WIDTH_HALF = const(_SMALL_FONT_WIDTH//2)


_PER_PAGE = const(_MH_DISPLAY_HEIGHT//_FONT_HEIGHT)
_Y_PADDING = const( (_MH_DISPLAY_HEIGHT - (_PER_PAGE * _FONT_HEIGHT)) // 2)

_SCROLL_MS = const(200)

# for touch:
_CONFIRM_MIN_X = const(_MH_DISPLAY_WIDTH // 4)
_CONFIRM_MAX_X = const(_MH_DISPLAY_WIDTH - _CONFIRM_MIN_X)
_CONFIRM_MIN_Y = const(_MH_DISPLAY_HEIGHT // 4)
_CONFIRM_MAX_Y = const(_MH_DISPLAY_HEIGHT - _CONFIRM_MIN_Y)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# global config will provide default stylings
DISPLAY = None
CONFIG = None
BEEP = None


# ----------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MENU ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----------------------------------------------------------------------------------------------------
class Menu:
    """Create menus for MicroHydra."""

    def __init__(
            self,
            per_page:int = _PER_PAGE,
            y_padding:int = _Y_PADDING,
            esc_callback:callable|None=None,
            i18n=None):
        """Initialize the Menu.

        args:
        - per_page (int): menu items per page
        - y_padding (int): y padding on first menu item
        - esc_callback (callable|None): callback for handling escape from menu screen
        - i18n (I18n|None): I18n object for translating menu items
        """

        # init globals
        global CONFIG, DISPLAY, BEEP  # noqa: PLW0603

        CONFIG = get_instance(Config)
        BEEP = get_instance(beeper.Beeper)
        DISPLAY = get_instance(Display, allow_init=False)


        self.items = []
        self.cursor_index = 0

        self.prev_screen_index = 0
        self.setting_screen_index = 0

        self.scroll_start_ms = time.ticks_ms()

        self.per_page = per_page
        self.y_padding = y_padding

        self.in_submenu = False
        self.running = False

        self.esc_callback = esc_callback

        self.i18n = i18n


    def append(self, item):
        """Add a new item to the menu."""
        self.items.append(item)


    def _get_animated_y(self) -> int:
        distance = (self.setting_screen_index - self.prev_screen_index) * font.HEIGHT
        fac = time.ticks_diff(time.ticks_ms(), self.scroll_start_ms) / _SCROLL_MS
        if fac >= 1:
            return 0
        fac = ease_out(fac)
        return int((1-fac)*distance)


    def draw(self) -> bool|None:
        """Draw the Menu.

        Returns:
        - None if in submenu,
        - True if being animated,
        - False if animation complete.
        """
        if self.in_submenu:
            return None

        if self.cursor_index >= self.setting_screen_index + self.per_page:
            self.prev_screen_index = self.setting_screen_index
            self.setting_screen_index += self.cursor_index - (self.setting_screen_index + (self.per_page - 1))
            self.scroll_start_ms = time.ticks_ms()

        elif self.cursor_index < self.setting_screen_index:
            self.prev_screen_index = self.setting_screen_index
            self.setting_screen_index -= self.setting_screen_index - self.cursor_index
            self.scroll_start_ms = time.ticks_ms()

        DISPLAY.fill(CONFIG.palette[2])

        anim_y = self._get_animated_y()

        if anim_y == 0:
            visible_range = range(self.setting_screen_index, self.setting_screen_index + self.per_page)
        else:
            visible_range = range(self.setting_screen_index-1, self.setting_screen_index + self.per_page+1)

        for i in visible_range:
            y = self.y_padding + anim_y + (i - self.setting_screen_index) * _FONT_HEIGHT
            if i <= len(self.items) - 1:
                self.items[i].selected = i == self.cursor_index
                self.items[i].y_pos = y
                self.items[i].draw()

        self.update_scroll_bar()

        # return true/false based on if animation is finished
        return anim_y != 0


    def update_scroll_bar(self):
        """Draw the scroll bar."""
        max_screen_index = len(self.items) - self.per_page

        if max_screen_index <= 0:
            return

        scrollbar_height = _MH_DISPLAY_HEIGHT // max_screen_index
        scrollbar_position = math.floor(
            (_MH_DISPLAY_HEIGHT - scrollbar_height) * (self.setting_screen_index / max_screen_index)
        )

        DISPLAY.rect(_SCROLLBAR_BUFFER_X, 0, _SCROLLBAR_BUFFER_WIDTH, _MH_DISPLAY_HEIGHT, CONFIG.palette[2], fill=True)
        DISPLAY.rect(_SCROLLBAR_X, 0, _SCROLLBAR_WIDTH, _MH_DISPLAY_HEIGHT, CONFIG.palette[1], fill=True)
        DISPLAY.rect(_SCROLLBAR_X, scrollbar_position, _SCROLLBAR_WIDTH, scrollbar_height, CONFIG.palette[4], fill=True)


    def handle_input(self, key) -> bool|None:
        """Take the input key and react accordingly."""
        if self.in_submenu:
            return self.items[self.cursor_index].handle_input(key)

        # this applies extra device-specific navigation keys
        key = UserInput.ext_dir_dict.get(key, key)

        if key == 'UP':
            self.cursor_index = (self.cursor_index - 1) % len(self.items)
            BEEP.play(("G3","B3"), time_ms=30)
            return True

        if key == 'DOWN':
            self.cursor_index = (self.cursor_index + 1) % len(self.items)
            BEEP.play(("B3","D3"), time_ms=30)
            return True

        if key in ('G0', 'ENT'):
            BEEP.play(("G3","B3","D3"), time_ms=30)
            return (self.items[self.cursor_index].handle_input("G0"))

        if key == "ESC":
            # pass control back when menu is backed out of.
            if self.esc_callback:
                BEEP.play((("C3","E3","D3"),"D4","C4"), time_ms=100)
                self.esc_callback(self)
            self.running = False
            return True
        return False


    # mh_if touchscreen:
    # @staticmethod
    # def _process_touch(keys, kb):
    #     """Convert swipes and taps to arrows and enters"""
    #     events = kb.get_touch_events()
    #     for event in events:
    #         if hasattr(event, 'direction'):
    #             # is a swipe
    #             keys.append(event.direction)

    #         elif _CONFIRM_MIN_X < event.x < _CONFIRM_MAX_X \
    #         and _CONFIRM_MIN_Y < event.y < _CONFIRM_MAX_Y:
    #             keys.append("ENT")
    # mh_end_if


    def exit(self):
        """Stop the main loop."""
        self.running = False


    def main(self):
        """Show the menu."""
        kb = UserInput.instance if hasattr(UserInput, 'instance') else UserInput()
        updating_display = True
        self.running = True
        while self.running:
            keys = kb.get_new_keys()

            # mh_if touchscreen:
            # self._process_touch(keys, kb)
            # mh_end_if

            for key in keys:
                self.handle_input(key)

            if keys:
                updating_display = True

            if updating_display:
                updating_display = self.draw()
                DISPLAY.show()

            if not keys and not updating_display:
                time.sleep_ms(1)




# -----------------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Menu Items: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# -----------------------------------------------------------------------------------------------------------

class MenuItem:
    """Parent class for HydraMenu Menu Items."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value,
        *,
        callback:callable|None=None,
        instant_callback:callable|None=None,
        **kwargs):  # noqa: ARG002
        """Initialize the MenuItem.

        Args:
        - menu (Menu):
            Parent Menu of the menu item.
        - text (str):
            Display text of the menu item.
        - value :
            the value that the menu item controls.
        - callback (callable):
            callback to call when menu item is updated. (optional)
        - instant_callback (callable):
            callback for any time menu item is changed,
            even before changes are confirmed. (optional)

        Additional kwargs:
        - min_int (int):
            for IntItems, the minimum allowed value.
        - max_int (int):
            for IntItems, the maximum allowed value.
        - hide (bool):
            for WriteItems, whether or not to hide entered text.
        """

        self.menu = menu
        self.text = text
        self.value = value
        self.callback = callback
        self.instant_callback = instant_callback
        self.selected = False
        self.i18n = menu.i18n


    def __repr__(self):
        return repr(self.value)


    def draw(self):
        """Draw this item."""
        draw_right_text(repr(self), self.y_pos, selected=self.selected)
        text = self.text if self.i18n is None else self.i18n[self.text]
        draw_left_text(text, self.y_pos, self.selected)
        DISPLAY.hline(0, self.y_pos, _MH_DISPLAY_WIDTH, CONFIG.palette[3])
        DISPLAY.hline(0, self.y_pos+_FONT_HEIGHT-1, _MH_DISPLAY_WIDTH, CONFIG.palette[1])


    def handle_input(self, key):  # noqa: ARG002
        """React accordingly to given key."""
        return

    def trans_popupwin(self) -> 'PopUpWin':
        """Translate window title for menu items."""
        return PopUpWin(self.text if self.i18n is None else self.i18n[self.text])

    def _callback(self, callback):
        """Call given callback (if it exists)."""
        if callback:
            callback(self, self.value)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Bool Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class BoolItem(MenuItem):
    """Item for creating boolean options."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:bool,  # noqa: FBT001
        *,
        callback:callable|None=None,
        **kwargs):  # noqa: ARG002
        """Initialize the bool item."""
        super().__init__(menu=menu, text=text, value=value, callback=callback)


    def handle_input(self, key) -> bool:  # noqa: ARG002
        """Toggle value."""
        self.value = not self.value

        self._callback(self.callback)

        return True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Do Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DOITEM_LEFT_SELECTOR_X = const(1)
_DOITEM_RIGHT_SELECTOR_X = const(_MH_DISPLAY_WIDTH - 17 - _DOITEM_LEFT_SELECTOR_X)

class DoItem(MenuItem):
    """Item for creating 'action' buttons."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:None=None,  # noqa: ARG002
        *,
        callback:callable|None=None,
        **kwargs):  # noqa: ARG002
        """Initialize the DoItem."""

        super().__init__(menu=menu, text=text, value=None, callback=callback)


    def draw(self):
        """Draw this item."""
        text = self.text if self.i18n is None else self.i18n[self.text]

        if self.selected:
            # Draw "< >" around (or behind) text
            DISPLAY.text("<", _DOITEM_LEFT_SELECTOR_X, self.y_pos, CONFIG.palette[5], font=font)
            DISPLAY.text(">", _DOITEM_RIGHT_SELECTOR_X, self.y_pos, CONFIG.palette[5], font=font)

            draw_centered_text(text, _DISPLAY_WIDTH_CENTER, self.y_pos, CONFIG.palette[9], font=font)
        else:
            draw_centered_text(text, _DISPLAY_WIDTH_CENTER, self.y_pos, CONFIG.palette[6], font=font)
        DISPLAY.hline(0, self.y_pos, _MH_DISPLAY_WIDTH, CONFIG.palette[2])
        DISPLAY.hline(0, self.y_pos+_FONT_HEIGHT-1, _MH_DISPLAY_WIDTH, CONFIG.palette[1])


    def handle_input(self, key):  # noqa: ARG002
        """Call stored action."""
        BEEP.play(("C3","E3","G3",("E3","G3","C3")), time_ms=30)
        if self.callback:
            self.callback(self)



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ RGB Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_SELECTION_ARROW_Y = const(_MH_DISPLAY_HEIGHT * 70 // 100)
_RGB_HINT_Y = const(_MH_DISPLAY_HEIGHT * 40 // 100)
_RGB_INPUT_Y = const(_RGB_HINT_Y + _SMALL_FONT_HEIGHT)

class RGBItem(MenuItem):
    """Item for creating RGB565 options."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        *,
        callback:callable|None=None,
        instant_callback:callable|None=None,
        **kwargs):  # noqa: ARG002
        """Initialize the RGB Item."""
        super().__init__(
            menu=menu,
            text=text,
            value=list(color.separate_color565(value)),
            callback=callback,
            instant_callback=instant_callback,
        )
        self.in_item = False
        self.cursor_index = 0
        self.init_value = list(color.separate_color565(value))


    def __repr__(self):
        return f"{self.value[0]},{self.value[1]},{self.value[2]}"

    def _callback(self, callback):
        if callback:
            callback(self, color.combine_color565(self.value[0],self.value[1],self.value[2]))

    def handle_input(self, key) -> bool|None:
        """Take given input key and respond accordingly."""
        _MAX_RANGE = const((32, 64, 32))
        input_accepted = False

        key = UserInput.ext_dir_dict.get(key, key)

        if not self.in_item:
            # remember original value
            self.init_value = self.value.copy()

        self.menu.in_submenu = True
        if (key == 'RIGHT'):
            BEEP.play(("A3","C3"), time_ms=30)
            self.cursor_index = (self.cursor_index + 1) % 3
            input_accepted = True

        elif (key == "LEFT"):
            BEEP.play(("F3","A3"), time_ms=30)
            self.cursor_index = (self.cursor_index - 1) % 3
            input_accepted = True

        elif (key == "UP"):
            BEEP.play("D3", time_ms=30)
            self.value[self.cursor_index] += 1
            self.value[self.cursor_index] %= _MAX_RANGE[self.cursor_index]
            self._callback(self.instant_callback)
            input_accepted = True

        elif (key == "DOWN"):
            BEEP.play("C3", time_ms=30)
            self.value[self.cursor_index] -= 1
            self.value[self.cursor_index] %= _MAX_RANGE[self.cursor_index]
            self._callback(self.instant_callback)
            input_accepted = True

        elif (key in ('G0', 'ENT')) and self.in_item:
            BEEP.play(("F3","A3","C4"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False

            self._callback(self.callback)
            return True

        elif key == "ESC" and self.in_item:
            self.value = self.init_value.copy() # reset value
            BEEP.play(("A3","F3","C3"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False
            self._callback(self.instant_callback)
            return True

        self.in_item = True
        self.draw_rgb_win()
        return input_accepted


    def draw_rgb_win(self):
        """Draw the RGB color selection window."""
        _CENTERED_X = const((_DISPLAY_CENTER_LEFT, _DISPLAY_WIDTH_CENTER, _DISPLAY_CENTER_RIGHT))

        win = self.trans_popupwin()
        win.draw()

        rgb_text = (f"R{math.floor(self.value[0]*8.225806)}",
                    f"G{math.floor(self.value[1]*4.04762)}",
                    f"B{math.floor(self.value[2]*8.225806)}")

        for i, item in enumerate(self.value):
            x = _CENTERED_X[i]
            if i == self.cursor_index:
                draw_centered_text(str(item), x, _RGB_INPUT_Y, CONFIG.palette[9], font=font)
            else:
                draw_centered_text(str(item), x, _RGB_INPUT_Y, CONFIG.palette[6], font=font)

            draw_centered_text(str(rgb_text[i]), x + 1, _RGB_HINT_Y, CONFIG.palette[0])
            draw_centered_text(str(rgb_text[i]), x, _RGB_HINT_Y - 1, CONFIG.palette[11 + i])

        # draw pointer
        draw_select_arrow(
            _CENTERED_X[self.cursor_index], _SELECTION_ARROW_Y,
            color.combine_color565(self.value[0],self.value[1],self.value[2])
            )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Int Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_INT_SELECTOR_Y = const(_MH_DISPLAY_HEIGHT * 53 // 100)
_INT_ARROW_UP_Y = const(_INT_SELECTOR_Y-12)
_INT_ARROW_DOWN_Y = const(_INT_SELECTOR_Y+10+_FONT_HEIGHT)

class IntItem(MenuItem):
    """Item for creating Integer selection options."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        *,
        callback:callable|None=None,
        instant_callback:callable|None=None,
        min_int:int=0,
        max_int:int=10,
        **kwargs):  # noqa: ARG002
        """Init the IntItem."""
        super().__init__(menu=menu, text=text, value=value, callback=callback, instant_callback=instant_callback)
        self.in_item = False
        self.min_int = min_int
        self.max_int = max_int
        self.init_value = value


    def handle_input(self, key):
        """React accordingly to given keypress."""
        self.menu.in_submenu = True

        if not self.in_item:
            # remember original value
            self.init_value = self.value

        key = UserInput.ext_dir_dict.get(key, key)

        if (key == "UP"):
            self.value += 1
            if self.value > self.max_int:
                self.value = self.min_int
            self._callback(self.instant_callback)
            BEEP.play("G3", time_ms=30)

        elif (key == "DOWN"):
            self.value -= 1
            if self.value < self.min_int:
                self.value = self.max_int
            self._callback(self.instant_callback)
            BEEP.play("E3", time_ms=30)

        elif (key in ('G0', 'ENT')) and self.in_item:
            BEEP.play(("E3","G3","B4"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            self._callback(self.callback)
            return

        elif key == "ESC" and self.in_item:
            self.value = self.init_value # reset value
            BEEP.play(("B4","G3","E3"), time_ms=20)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            self._callback(self.instant_callback)
            return

        self.in_item = True
        self.draw_win()


    def draw_win(self):
        """Draw the popup window for the IntItem."""
        win = self.trans_popupwin()
        win.draw()
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _INT_ARROW_UP_Y, CONFIG.palette[5])
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _INT_ARROW_DOWN_Y, CONFIG.palette[5], direction=-1)

        draw_centered_text(str(self.value), _DISPLAY_WIDTH_CENTER, _INT_SELECTOR_Y, CONFIG.palette[8], font=font)



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Write Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class WriteItem(MenuItem):
    """Item for creating text entry options."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:int,
        *,
        callback:callable|None=None,
        hide:bool=False,
        **kwargs):  # noqa: ARG002
        """Init the WriteItem."""
        super().__init__(menu=menu, text=text, value=value, callback=callback)
        self.in_item = False
        self.hide = hide
        self.init_value = value


    def __repr__(self):
        if self.hide:
            if self.value:
                return '*****'
            return ''
        return repr(self.value)


    def draw_win(self):
        """Draw the text entry window."""
        win = self.trans_popupwin()
        win.draw()
        win.text(self.value)


    def handle_input(self, key):
        """React accordingly to given key."""
        self.menu.in_submenu = True

        if not self.in_item:
            # remember original value
            self.init_value = self.value

        if (key in ('G0', 'ENT')) and self.in_item:
            BEEP.play(("A3","C4","E4"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            self._callback(self.callback)
            return

        if key == "ESC" and self.in_item:
            self.value = self.init_value # reset value
            BEEP.play(("A3","E3","C3"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            return

        if key == "SPC":
            BEEP.play("E3", time_ms=30)
            self.value += " "

        elif len(key) == 1:
            BEEP.play("A3", time_ms=30)
            self.value += key

        elif key == "BSPC":
            BEEP.play(("C4","C3"), time_ms=30)
            self.value = self.value[:-1]

        self.in_item = True
        self.draw_win()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Choice Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_DISPLAY_HEIGHT_HALF = const(_MH_DISPLAY_HEIGHT // 2)
_CHOICE_ARROW_UP = const(_DISPLAY_HEIGHT_HALF - 14)
_CHOICE_ARROW_DOWN = const(_DISPLAY_HEIGHT_HALF + 48)

class ChoiceItem(MenuItem):
    """Item for creating multiple choice options."""

    def __init__(
        self,
        menu:Menu,
        text:str,
        value:str,
        choices:list|tuple,
        callback:callable|None=None,
        instant_callback:callable|None=None,
        **kwargs):  # noqa: ARG002
        """Initialize the ChoiceItem."""
        self.in_item = False
        self.choices = choices

        self.idx = choices.index(value)

        super().__init__(menu=menu, text=text, value=value, callback=callback, instant_callback=instant_callback)


    def _move_choice(self, add):
        self.idx = (self.idx + add) % len(self.choices)
        self.value = self.choices[self.idx]
        if self.instant_callback:
            self.instant_callback(self, self.value)


    def handle_input(self, key):
        """React accordingly to given key."""
        self.menu.in_submenu = True

        if not self.in_item:
            # remember original value
            self.init_value = self.value

        # convert extra keys into navigation keys
        # (e.g. (",", ".", "/", ";") -> arrow keys on Cardputer)
        key = UserInput.ext_dir_dict.get(key, key)

        if (key == "UP"):
            self._move_choice(-1)
            BEEP.play("B4", time_ms=30)

        elif (key == "DOWN"):
            self._move_choice(1)
            BEEP.play("A4", time_ms=30)


        elif (key in ('G0', 'ENT')) and self.in_item:
            BEEP.play(("A3","B3","C4"), time_ms=30)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            if self.callback:
                self.callback(self, self.value)
            return

        elif key == "ESC" and self.in_item:
            self.value = self.init_value # reset value
            self.idx = self.choices.index(self.value)
            BEEP.play(("C4","B3","A3"), time_ms=20)
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.draw()
            if self.instant_callback:
                self.instant_callback(self, self.value)
            return

        self.in_item = True
        self.draw_win()


    def draw_win(self):
        """Draw the choice selection window."""
        win = self.trans_popupwin()
        win.draw()
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _CHOICE_ARROW_UP, CONFIG.palette[5])
        draw_small_arrow(_DISPLAY_WIDTH_CENTER, _CHOICE_ARROW_DOWN, CONFIG.palette[5], direction=-1)
        largest_width = len(max(self.choices, key=len))
        box_w = largest_width * 8 + 8
        box_x = _DISPLAY_WIDTH_CENTER - (box_w // 2)

        for i in range(3):
            idx = (self.idx - 1 + i) % len(self.choices)
            DISPLAY.rect(box_x, _DISPLAY_HEIGHT_HALF - 2 + (i * 13), box_w, 12, CONFIG.palette[5], fill=True)
            draw_centered_text(
                str(self.choices[idx]),
                _DISPLAY_WIDTH_CENTER,
                _DISPLAY_HEIGHT_HALF + (i * 13),
                CONFIG.palette[9 if i == 1 else 7],
                )



# ____________________________________________________________________________________________________________
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Popup Window ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_WINDOW_PADDING = const(10)

_WINDOW_WIDTH = const(_MH_DISPLAY_WIDTH-(_WINDOW_PADDING*2))
_WINDOW_HEIGHT = const(_MH_DISPLAY_HEIGHT-(_WINDOW_PADDING*2))

_WINDOW_TITLE_Y = const(_MH_DISPLAY_HEIGHT * 12 // 100)
_WINDOW_WRITE_Y = const(_MH_DISPLAY_HEIGHT * 60 // 100)
_WINDOW_WRITE_Y_OVERFLOW = const(_WINDOW_WRITE_Y - _FONT_HEIGHT)

_MAX_TEXT_LEN = const(_WINDOW_WIDTH // _FONT_WIDTH)

class PopUpWin:
    """A popup window that you can write on."""

    def __init__(self, title: str|None = None):
        """Create a PopUpWin."""
        self.title = title

    def text(self, string:str):
        """Write text on the window."""
        if len(string) > _MAX_TEXT_LEN:
            draw_centered_text(
                string[:len(string)-_MAX_TEXT_LEN],
                _DISPLAY_WIDTH_CENTER,
                _WINDOW_WRITE_Y_OVERFLOW,
                CONFIG.palette[8],
                font=font,
            )
            draw_centered_text(
                string[len(string)-_MAX_TEXT_LEN:],
                _DISPLAY_WIDTH_CENTER,
                _WINDOW_WRITE_Y,
                CONFIG.palette[8],
                font=font,
            )
        else:
            draw_centered_text(string, _DISPLAY_WIDTH_CENTER, _WINDOW_WRITE_Y, CONFIG.palette[8], font=font)


    def draw(self):
        """Draw this window."""
        DISPLAY.fill_rect(_WINDOW_PADDING, _WINDOW_PADDING, _WINDOW_WIDTH, _WINDOW_HEIGHT, CONFIG.palette[3])
        DISPLAY.rect(_WINDOW_PADDING, _WINDOW_PADDING, _WINDOW_WIDTH, _WINDOW_HEIGHT, CONFIG.palette[5])

        for i in range(6):
            DISPLAY.hline(_WINDOW_PADDING+i,
                          _WINDOW_PADDING+_WINDOW_HEIGHT+i,
                          _WINDOW_WIDTH, CONFIG.palette[0])
            DISPLAY.vline(_WINDOW_PADDING+_WINDOW_WIDTH+i,
                          _WINDOW_PADDING+i,
                          _WINDOW_HEIGHT, CONFIG.palette[0])

        if self.title:
            draw_centered_text(
                str(self.title + ":"),
                _DISPLAY_WIDTH_CENTER,
                _WINDOW_TITLE_Y,
                CONFIG.palette[6],
                font=font,
            )





# ___________________________________________________________________________________________________________
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Shape Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def draw_small_arrow(x, y, clr, direction=1):
    """Draw a little indicator arrow."""
    for i in range(8):
        DISPLAY.hline(
            x = (x - i),
            y = y + (i * direction),
            length = 2 + (i*2),
            color = clr)


def draw_select_arrow(x, y, clr):
    """Draw a big ui/selection arrow."""
    x -= 16
    _ARROW_COORDS = array.array('h', (16,0, 17,0, 33,16, 33,24, 0,24, 0,16))

    DISPLAY.polygon(_ARROW_COORDS, x, y, clr, fill=True)
    DISPLAY.polygon(_ARROW_COORDS, x, y, 31695)




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Text Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_MAX_CENTER_TEXT_LEN = const(_MH_DISPLAY_WIDTH // _FONT_WIDTH)
def draw_centered_text(text, x, y, clr, font=None):
    """Draw text centered on the given X coord."""
    # draw text centered on the x axis
    if font and len(text) > _MAX_CENTER_TEXT_LEN:
        font = None
        y += 10

    x = (
        x - len(text) * _FONT_WIDTH_HALF if font
        else x - len(text) * _SMALL_FONT_WIDTH_HALF
    )
    DISPLAY.text(text, x, y, clr, font=font)


def get_text_center(text: str) -> int:
    """Calculate the center of the given text."""
    return int((len(text) * font.WIDTH) // 2)


def get_text_width(text) -> int:
    """Find the total width of the given text (considering UTF8 chars)."""
    width = 0
    for char in text:
        width += 16 if ord(char) < 128 else 32
    return width


# left text
_LEFT_TEXT_UNSELECTED_X = const(10)
_LEFT_TEXT_TINY_X = const(14)
_LEFT_TEXT_ARROW_X = const(-4)
_MAX_LEFT_SIZE = const((_MH_DISPLAY_WIDTH * 2)  // 3)

def draw_left_text(text:str, y_pos:int, selected):
    """Draw the big, leftmost text in the Menu."""
    if get_text_width(text) < _MAX_LEFT_SIZE:
        fnt = font
        x = _LEFT_TEXT_UNSELECTED_X
        y = y_pos
    else:
        fnt = None
        x = _LEFT_TEXT_TINY_X
        y = y_pos + 12

    if selected:
        DISPLAY.text(">", _LEFT_TEXT_ARROW_X, y_pos, CONFIG.palette[8], font=font)
        DISPLAY.text(text, x-2, y, CONFIG.palette[1], font=fnt)
        DISPLAY.text(text, x, y, CONFIG.palette[9], font=fnt)
    else:
        DISPLAY.text(text, x, y, CONFIG.palette[6], font=fnt)


# right text
_RIGHT_TEXT_Y = const((_FONT_HEIGHT-_SMALL_FONT_HEIGHT) // 2)
_RIGHT_TEXT_X_OFFSET = const(40)
_RIGHT_TEXT_X = const(_MH_DISPLAY_WIDTH - _RIGHT_TEXT_X_OFFSET)
_MAX_RIGHT_LEN = const(((_MH_DISPLAY_WIDTH * 1)  // 3) // 8)

def draw_right_text(text:str, y_pos:int, *, selected=False):
    """Draw the smaller, rightmost text (that hints at the value of the MenuItem)."""
    if len(text) > _MAX_RIGHT_LEN:
        text = f"{text[:_MAX_RIGHT_LEN-3]}..."

    x = _RIGHT_TEXT_X - (len(text) * _SMALL_FONT_WIDTH_HALF)

    if len(text) * _SMALL_FONT_WIDTH_HALF > 80:
         x = ((_MH_DISPLAY_WIDTH // 2) + _RIGHT_TEXT_X_OFFSET)

    DISPLAY.text(
        text,
        x, y_pos+_RIGHT_TEXT_Y,
        CONFIG.palette[7] if selected else CONFIG.palette[4]
    )



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Math Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ease_out(x: float) -> float:
    """Apply a easing on the given float."""
    return 1 - ((1 - x) ** 3)

