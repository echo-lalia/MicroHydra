"""MicroHydra main launcher.

This program is designed to be used in conjunction with "main.py" apploader,
to select and launch MicroPython apps.

The basic app loading logic works like this:
 - apploader reads reset cause and RTC.memory to determine which app to launch
 - apploader launches 'launcher.py' when hard reset, or when RTC.memory is blank
 - launcher scans app directories on flash and SDCard to find apps, allows user to select app
 - launcher stores path to app in RTC.memory, and soft-resets the device
 - apploader reads RTC.memory again, and imports given app
 - pressing the reset button will relaunch the launcher program,
   and so will calling machine.reset() from the app.

This approach was chosen to reduce the chance of conflicts or memory errors when switching apps.
Because MicroPython completely resets between apps,
the only "wasted" ram from the app switching process will be from main.py


Copyright (C) 2024  Ethan Lacasse

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import math
import os
import time

import framebuf
import machine

# mh_if wifi:
# import network
# import ntptime
# mh_end_if

from font import vga2_16x32 as font
from launcher.icons import appicons
from lib import battlevel, display, sdcard, userinput
from lib.display.rawbitmap import RawBitmap
from lib.hydra import beeper, loader, statusbar
from lib.hydra.config import Config
from lib.hydra.i18n import I18n


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_WIDTH = const(320)
_MH_DISPLAY_HEIGHT = const(320)
_MH_DISPLAY_BACKLIGHT = const(12)

_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH//2)

_FONT_WIDTH = const(16)
_FONT_HEIGHT = const(32)
_FONT_WIDTH_HALF = const(_FONT_WIDTH // 2)

_SMALL_FONT_WIDTH = const(8)
_SMALL_FONT_HEIGHT = const(8)


_ICON_HEIGHT = const(32)
_ICON_WIDTH = const(32)

_STATUSBAR_HEIGHT = const(18)
_SCROLLBAR_HEIGHT = const(4)

# somewhat arbitrary padding calculation:
_Y_PADDING = const(
    (_MH_DISPLAY_HEIGHT
    - _STATUSBAR_HEIGHT
    - _ICON_HEIGHT
    - _FONT_HEIGHT
    - _SCROLLBAR_HEIGHT
    - 4)
    // 5
    )


_ICON_Y = const(_MH_DISPLAY_HEIGHT * 27 // 100)
_APPNAME_Y = const(_ICON_Y + _ICON_HEIGHT + _Y_PADDING)


_SCROLL_ANIMATION_TIME = const(350)
_SCROLL_ANIMATION_QUICK = const(150)


_ASCII_MAX = const(128)


_TRANS = const("""[
    {"en": "Loading...", "zh": "加载中...", "ja": "読み込み中..."},
    {"en": "Files", "zh": "文件", "ja": "ファイル"},
    {"en": "Terminal", "zh": "终端", "ja": "端末"},
    {"en": "Get Apps", "zh": "应用商店", "ja": "アプリストア"},
    {"en": "Reload Apps", "zh": "重新加载应用", "ja": "アプリ再読"},
    {"en": "UI Sound", "zh": "界面声音", "ja": "UIサウンド"},
    {"en": "Settings", "zh": "设置", "ja": "設定"},
    {"en": "On", "zh": "开", "ja": "オン"},
    {"en": "Off", "zh": "关", "ja": "オフ"}
]""")



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# wifi loves to give unknown runtime errors, just try it twice:
# mh_if wifi:
# try:
#     NIC = network.WLAN(network.STA_IF)
# except RuntimeError as e:
#     print(e)
#     try:
#         NIC = network.WLAN(network.STA_IF)
#     except RuntimeError as e:
#         NIC = None
#         print("Wifi WLAN object couldnt be created. Gave this error:", e)
# 
# SYNC_NTP_ATTEMPTS = 0
# CONNECT_WIFI_ATTEMPTS = 0
# SYNCING_CLOCK = None
# mh_end_if


DISPLAY = display.Display(
    # mh_if spi_ram:
    # use_tiny_buf=False,
    # mh_else:
    use_tiny_buf=True,
    # mh_end_if
    )

BEEP = beeper.Beeper()
CONFIG = Config()
KB = userinput.UserInput()
STATUSBAR = statusbar.StatusBar()

SD = sdcard.SDCard()
RTC = machine.RTC()

I18N = I18n(_TRANS)

APP_NAMES = None
APP_PATHS = None
APP_SELECTOR_INDEX = 0
PREV_SELECTOR_INDEX = 0


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Finding Apps ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def scan_apps():
    """Scan for apps in /apps and /sd/apps."""
    global APP_NAMES, APP_PATHS  # noqa: PLW0603

    # first we need a list of apps located on the flash or SDCard
    SD.mount()
    main_directory = os.listdir("/")

    sd_directory = []
    if "sd" in main_directory:
        sd_directory = os.listdir("/sd")

    # if the apps folder does not exist, create it.
    if "apps" not in main_directory:
        os.mkdir("/apps")
        main_directory = os.listdir("/")

    # do the same for the sdcard apps directory
    if "apps" not in sd_directory and "sd" in main_directory:
        os.mkdir("/sd/apps")
        sd_directory = os.listdir("/sd")

    # if everything above worked, sdcard should be mounted (if available),
    # and both app directories should exist. now look inside to find our apps:
    main_app_list = list(os.ilistdir("/apps"))
    sd_app_list = []

    if "sd" in main_directory:
        try:
            sd_app_list = list(os.ilistdir("/sd/apps"))
        except OSError as e:
            print(e)
            print(
                "SDCard mounted but cant be opened; assuming it's been removed. Unmounting /sd.")
            os.umount('/sd')

    # now lets collect some separate app names and locations
    app_names = []
    app_paths = {}

    for entry in main_app_list:
        this_name, this_path = get_app_paths(entry, "/apps/")
        if this_name:
            this_name = this_name.replace('.cli', '')
            if this_name not in app_names:
                app_names.append(this_name)

            app_paths[this_name] = this_path

    for entry in sd_app_list:
        this_name, this_path = get_app_paths(entry, "/sd/apps/")
        if this_name:
            this_name = this_name.replace('.cli', '')
            if this_name not in app_names:
                app_names.append(this_name)

            app_paths[this_name] = this_path

    # sort alphabetically without uppercase/lowercase discrimination:
    app_names.sort(key=lambda element: element.lower())

    # add built-in app names
    app_names += [
        "Files",
        "Terminal",
        "Reload Apps",
        "UI Sound",
        "Settings",
        # mh_if wifi:
        # "Get Apps",
        # mh_end_if
        ]

    # add paths for built-in apps
    # mh_if frozen:
    # app_paths.update({
    #     "Files": ".frozen/launcher/files",
    #     "Terminal": ".frozen/launcher/terminal",
    #     "Settings": ".frozen/launcher/settings",
    #     })
    # mh_else:
    app_paths.update({
        "Files": "/launcher/files",
        "Terminal": "/launcher/terminal",
        "Settings": "/launcher/settings",
        })
    # mh_end_if

    # Conditionally also add "Get Apps"
    # (Ideally this should be handled more gracefully, but the MicroHydra preprocessor needs a bit of work.)
    # mh_if wifi and frozen:
    # app_paths["Get Apps"] = ".frozen/launcher/getapps"
    # mh_else_if wifi:
    app_paths["Get Apps"] = "/launcher/getapps"
    # mh_end_if

    APP_NAMES = app_names
    APP_PATHS = app_paths


def get_app_paths(ientry: tuple, current_dir: str) -> tuple[str|None, str|None]:
    """Get an apps name and full path.

    Returns app_name, app_path
    """
    # process results of ilistdir to capture app paths.
    _DIR_FLAG = const(16384)
    _FILE_FLAG = const(32768)

    entry = ientry[0]
    is_dir = (ientry[1] == _DIR_FLAG)

    if entry.endswith(".py"):
        return entry[:-3], current_dir + entry

    if entry.endswith(".mpy"):
        return entry[:-4], current_dir + entry

    if is_dir:
        # check for apps as module folders
        dir_content = os.listdir(current_dir + entry)
        if "__init__.py" in dir_content or "__init__.mpy" in dir_content:
            return entry, current_dir + entry

    return None, None



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def launch_app(app_path):
    """Reboot into given app."""
    print(f"Launching '{app_path}'...")
    if app_path.endswith(".cli.py"):
        loader.launch_app(APP_PATHS['Terminal'], f"${app_path}")
    loader.launch_app(app_path)


def center_text_x(text: str) -> int:
    """Calculate the x coordinate to draw a text string, to make it horizontally centered.

    This function calculates the total width of the given text.
    """
    # calculate length
    x = _DISPLAY_WIDTH_HALF
    for char in text:
        if ord(char) > _ASCII_MAX:
            x -= _FONT_WIDTH
        else:
            x -= _FONT_WIDTH_HALF
    return x


def ease_out_cubic(x: float) -> float:
    """Apply cubic ease out function."""
    return 1 - ((1 - x) ** 3)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Graphics Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_MIN_SCROLLBAR_WIDTH = const(20)
_SCROLLBAR_PADDING = const(6)

_SCROLLBAR_FILL_HEIGHT = const(_SCROLLBAR_HEIGHT - 2)
_SCROLLBAR_Y = const(_MH_DISPLAY_HEIGHT - _SCROLLBAR_HEIGHT)  # highlight y
_SCROLLBAR_FILL_Y = const(_SCROLLBAR_Y + 1)
_SCROLLBAR_SHADOW_Y = const(_MH_DISPLAY_HEIGHT - 1)
_SCROLLBAR_FULL_WIDTH = const(_MH_DISPLAY_WIDTH - (_SCROLLBAR_PADDING * 2))


def draw_scrollbar():
    """Draw the scrollbar on the display."""
    scrollbar_width = max(
        _SCROLLBAR_FULL_WIDTH // len(APP_NAMES),
        _MIN_SCROLLBAR_WIDTH,
        )

    scrollbar_x = (
        _SCROLLBAR_FULL_WIDTH
        * APP_SELECTOR_INDEX
        // len(APP_NAMES)
        + _SCROLLBAR_PADDING
        )

    # blackout:
    DISPLAY.fill_rect(
        0, _SCROLLBAR_Y,
        _MH_DISPLAY_WIDTH, _SCROLLBAR_HEIGHT,
        CONFIG.palette[2],
        )

    # draw fill:
    DISPLAY.fill_rect(
        scrollbar_x,
        _SCROLLBAR_FILL_Y,
        scrollbar_width,
        _SCROLLBAR_FILL_HEIGHT,
        CONFIG.palette[4],
        )

    # draw highlight and shadow:
    DISPLAY.hline(
        scrollbar_x,
        _SCROLLBAR_Y,
        scrollbar_width,
        CONFIG.palette[6],
        )
    DISPLAY.hline(
        scrollbar_x,
        _SCROLLBAR_SHADOW_Y,
        scrollbar_width,
        CONFIG.palette[0],
        )


def draw_app_selector(icon):
    """Update and draw the app selector graphics."""
    icon.move()
    icon.draw()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ICONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_FLASH_ICON_IDX = const(0)
_SD_ICON_IDX = const(1)
_GEAR_ICON_IDX = const(2)
_REFRESH_ICON_IDX = const(3)
_FILE_ICON_IDX = const(4)
_TERMINAL_ICON_IDX = const(5)
_GETAPPS_ICON_IDX = const(6)

_ICON_WIDTH_HALF = const(_ICON_WIDTH // 2)

_ICON_CENTERED_X = const(_DISPLAY_WIDTH_HALF - (_ICON_WIDTH // 2))
_ICON_OFF_X = const(_DISPLAY_WIDTH_HALF - ((_FONT_WIDTH * 3) // 2))
_ICON_ERASE_X = const(_ICON_OFF_X)
_ICON_ERASE_WIDTH = const(_FONT_WIDTH * 3)

_ICON_BITMAP_SIZE = const(_ICON_HEIGHT * _ICON_WIDTH)
_ICON_BUFFER_LEN = const(_ICON_BITMAP_SIZE // 2)


class IconWidget:
    """Responsible for handling icon graphics."""

    def __init__(self):
        """Initialize the IconWidget."""
        self.drawn_icon = None
        self.next_icon = None
        self.direction = 0
        self.x = _DISPLAY_WIDTH_HALF
        self.prev_x = 0
        self.scroll_start_ms = time.ticks_ms()
        self.anim_time = _SCROLL_ANIMATION_TIME
        self.anim_fac = 0.0

        self.force_update()


    def force_update(self):
        """Force an update to the next icon."""
        draw_scrollbar()
        draw_app_name()
        self.next_icon = self._choose_icon()
        self.drawn_icon = self.next_icon
        self.prev_x = 0


    def _animate_scroll(self) -> int:
        if not self.direction:
            return 0

        fac = time.ticks_diff(
            time.ticks_ms(),
            self.scroll_start_ms,
            ) / self.anim_time

        if fac >= 1:
            self.direction = 0
            self.anim_fac = 0.0
            return 0

        fac = ease_out_cubic(fac)
        self.anim_fac = fac

        return math.floor(
            fac * _MH_DISPLAY_WIDTH if self.direction < 0 else fac * -_MH_DISPLAY_WIDTH,
        )


    def start_scroll(self, direction=0):
        """Initialize the scrolling animation."""
        if self.next_icon != self.drawn_icon:
            self.force_update()
            self.anim_time = _SCROLL_ANIMATION_QUICK
        else:
            self.anim_time = _SCROLL_ANIMATION_TIME

        draw_scrollbar()
        draw_app_name()
        self.direction = direction
        self.scroll_start_ms = time.ticks_ms()
        self.next_icon = self._choose_icon()


    def _draw_bitmap_icon(self, custom_bmp=None):
        _MAX_EXT_WIDTH = const((_ICON_WIDTH*3) // 2)

        if 0.01 < self.anim_fac < 0.99 and self.x != _DISPLAY_WIDTH_HALF:
            # squish in and out of frame
            fac = self.anim_fac*2.0 if self.anim_fac<0.5 else 1.0 - (self.anim_fac - 0.5)*2
            ext_width = int(fac * _MAX_EXT_WIDTH)
        else:
            ext_width = 0

        DISPLAY.bitmap(
            appicons if custom_bmp is None else custom_bmp,
            self.x - _ICON_WIDTH_HALF - (ext_width >> 1),
            _ICON_Y + (ext_width>>2),
            index=0 if custom_bmp else self.drawn_icon,
            draw_width=_ICON_WIDTH + ext_width,
            draw_height=_ICON_HEIGHT - (ext_width>>1),
            palette=(CONFIG.palette[2], CONFIG.palette[8]),
            )


    def _draw_str_icon(self):
        clr_idx = 4 if self.drawn_icon == 'Off' else 8
        icon_str = I18N[self.drawn_icon]
        DISPLAY.text(
            icon_str,
            self.x - (len(icon_str) * _FONT_WIDTH_HALF),
            _ICON_Y,
            CONFIG.palette[clr_idx],
            font=font,
            )


    def draw(self):
        """Draw the icon on the display."""
        if self.x == _DISPLAY_WIDTH_HALF \
        and self.prev_x == _DISPLAY_WIDTH_HALF:
            return

        self._erase_icon()

        # update drawn icon when icon wraps around screen:
        if self.drawn_icon != self.next_icon \
        and ((self.direction == -1 and self.x < _DISPLAY_WIDTH_HALF)
        or (self.direction == +1 and self.x > _DISPLAY_WIDTH_HALF)):
            self.drawn_icon = self.next_icon

            # if this is a custom icon, it needs to be loaded
            if isinstance(self.drawn_icon, str) and self.drawn_icon.endswith(".raw"):
                with open(self.drawn_icon, 'rb') as f:
                    f.readinto(self.buf)

        if isinstance(self.drawn_icon, RawBitmap):
            self._draw_bitmap_icon(self.drawn_icon)

        if isinstance(self.drawn_icon, int):
            self._draw_bitmap_icon()

        elif isinstance(self.drawn_icon, str):
            self._draw_str_icon()


    def _choose_icon(self) -> int|str:
        current_app_text = APP_NAMES[APP_SELECTOR_INDEX]

        # special menu options for settings
        if current_app_text == "UI Sound":
            return "On" if CONFIG['ui_sound'] else "Off"

        builtin_icon_idxs = {
            "Settings": 2,
            "Reload Apps": 3,
            "Files": 4,
            "Terminal": 5,
            "Get Apps": 6,
            }
        if current_app_text in builtin_icon_idxs:
            return builtin_icon_idxs[current_app_text]

        current_app_path = APP_PATHS[current_app_text]

        if current_app_path.endswith('.cli.py'):
            return _TERMINAL_ICON_IDX

        if not (current_app_path.endswith('.py') or current_app_path.endswith('.mpy')):
            # too many ways for `os.listdir` to fail here, so just capture the error:
            try:
                if 'icon.raw' in os.listdir(current_app_path):
                    return RawBitmap(f"{current_app_path}/icon.raw", 32, 32, (CONFIG.palette[2], CONFIG.palette[8]))
            except OSError:
                pass

        # default to sd or flash storage icon
        if current_app_path.startswith("/sd"):
            return _SD_ICON_IDX
        return _FLASH_ICON_IDX


    @staticmethod
    def _erase_icon():
        DISPLAY.rect(
            0,
            _ICON_Y,
            _MH_DISPLAY_WIDTH,
            _ICON_HEIGHT,
            CONFIG.palette[2],
            fill=True,
            )


    def move(self):
        """Update the new icon x position."""
        if not self.direction:
            self.x = _DISPLAY_WIDTH_HALF
        x = self._animate_scroll()
        self.prev_x = self.x
        self.x = (x + _DISPLAY_WIDTH_HALF) % _MH_DISPLAY_WIDTH




_APP_NAME_MAX_LEN = const(_MH_DISPLAY_WIDTH // _FONT_WIDTH)
_APP_NAME_LEN_MINUS_THREE = const(_APP_NAME_MAX_LEN - 3)


def draw_app_name():
    """Draw the current app name on the display."""
    current_app_text = APP_NAMES[APP_SELECTOR_INDEX]

    # crop text for display
    if len(current_app_text) > _APP_NAME_MAX_LEN:
        current_app_text = f"{current_app_text[:_APP_NAME_LEN_MINUS_THREE]}..."

    # blackout the old text
    DISPLAY.rect(0, _APPNAME_Y, _MH_DISPLAY_WIDTH, _FONT_HEIGHT, CONFIG.palette[2], fill=True)

    # translate text (if applicable)
    current_app_text = I18N[current_app_text]
    # and draw app name
    DISPLAY.text(
        current_app_text,
        center_text_x(current_app_text), _APPNAME_Y,
        CONFIG.palette[8],
        font=font,
        )


_MAX_WIFI_ATTEMPTS = const(1000)
_MAX_NTP_ATTEMPTS = const(10)


# mh_if wifi:
# def init_sync_clock():
#     global SYNCING_CLOCK  # noqa: PLW0603
#     # sync our RTC on boot, if set in settings
#     SYNCING_CLOCK = CONFIG['sync_clock']
# 
#     if (CONFIG['wifi_ssid'] == ''
#     or RTC.datetime()[0] != 2000
#     or NIC is None):
#         SYNCING_CLOCK = False
# 
#     if SYNCING_CLOCK:  # enable wifi if we are syncing the clock
#         if not NIC.active():  # turn on wifi if it isn't already
#             NIC.active(True)
#         if not NIC.isconnected():  # try connecting
#             try:
#                 NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
#             except OSError as e:
#                 print("wifi_sync_rtc had this error when connecting:", e)
# 
# def try_sync_clock():
#     """Try syncing the RTC using ntptime."""
#     global SYNCING_CLOCK, SYNC_NTP_ATTEMPTS, CONNECT_WIFI_ATTEMPTS  # noqa: PLW0603
# 
#     if NIC.isconnected():
#         try:
#             ntptime.settime()
#         except OSError:
#             SYNC_NTP_ATTEMPTS += 1
# 
#         if RTC.datetime()[0] != 2000:
#             NIC.disconnect()
#             NIC.active(False)  # shut off wifi
#             SYNCING_CLOCK = False
#             # apply our timezone offset
#             time_list = list(RTC.datetime())
#             time_list[4] += CONFIG["timezone"]
#             RTC.datetime(tuple(time_list))
#             print(
#                 f'RTC successfully synced to {RTC.datetime()} with {SYNC_NTP_ATTEMPTS} attempts.')
#             # Redraw statusbar
#             display.Display.draw_overlays = True
# 
#         elif SYNC_NTP_ATTEMPTS >= _MAX_NTP_ATTEMPTS:
#             NIC.disconnect()
#             NIC.active(False)  # shut off wifi
#             SYNCING_CLOCK = False
#             print(f"Syncing RTC aborted after {SYNC_NTP_ATTEMPTS} attemps")
# 
#     elif CONNECT_WIFI_ATTEMPTS >= _MAX_WIFI_ATTEMPTS:
#         NIC.disconnect()
#         NIC.active(False)  # shut off wifi
#         SYNCING_CLOCK = False
#         print(
#             f"Connecting to wifi aborted after {CONNECT_WIFI_ATTEMPTS} loops")
#     else:
#         CONNECT_WIFI_ATTEMPTS += 1
# mh_end_if


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# --------------------------------------------------------------------------------------------------
def main_loop():
    """Run the main loop."""
    global APP_SELECTOR_INDEX, PREV_SELECTOR_INDEX  # noqa: PLW0603
    # mh_if wifi:
    # global SYNCING_CLOCK  # noqa: PLW0603
    # mh_end_if

    # scan apps asap to populate app names/paths and SD
    scan_apps()

    # mh_if wifi:
    # init_sync_clock()
    # mh_end_if

    new_keys = []

    # starupp sound
    BEEP.play(
        ('C3',
            ('C4', 'E4', 'G4'),
            ('C4', 'E4', 'G4'),
         ))

    # init diplsay
    DISPLAY.fill(CONFIG.palette[2])

    icon = IconWidget()
    icon.draw()


    while True:

        # ----------------------- check for key presses on the keyboard. Only if they weren't already pressed. ---------
        new_keys = KB.get_new_keys()

        # mh_if CARDPUTER:
        # # Cardputer should use extended movement keys in the launcher
        # KB.ext_dir_keys(new_keys)
        # mh_end_if

        # mh_if touchscreen:
        # # add swipes to direcitonal input
        # touch_events = KB.get_touch_events()
        # for event in touch_events:
        #     if hasattr(event, 'direction'):
        #         if event.direction == 'RIGHT':
        #             new_keys.append('LEFT')
        #         elif event.direction == 'LEFT':
        #             new_keys.append('RIGHT')
        # mh_end_if

        if new_keys:

            # ~~~~~~ check if the arrow keys are newly pressed ~~~~~
            if "RIGHT" in new_keys:  # right arrow
                PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                APP_SELECTOR_INDEX = (APP_SELECTOR_INDEX + 1) % len(APP_NAMES)

                # animation:
                icon.start_scroll(1)

                BEEP.play((("D3", 'F3'), "A3"), 20)

            elif "LEFT" in new_keys:  # left arrow
                PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                APP_SELECTOR_INDEX = (APP_SELECTOR_INDEX - 1) % len(APP_NAMES)

                # animation:
                icon.start_scroll(-1)

                BEEP.play((("C3", "E3"), "G3"), 20)

            # ~~~~~~~~~~ check if GO or ENTER are pressed ~~~~~~~~~~
            if "G0" in new_keys or "ENT" in new_keys:

                # special "settings" app options will have their own behaviour, otherwise launch the app
                if APP_NAMES[APP_SELECTOR_INDEX] == "UI Sound":
                    CONFIG['ui_sound'] = not CONFIG['ui_sound']
                    icon.force_update()
                    icon.draw()

                    if CONFIG['ui_sound'] == 0:  # currently muted, then unmute
                        BEEP.play(
                            ("C3", "E3", "G3", ("C4", "E4", "G4"), ("C4", "E4", "G4")), 80)


                elif APP_NAMES[APP_SELECTOR_INDEX] == "Reload Apps":
                    scan_apps()
                    APP_SELECTOR_INDEX = 0
                    icon.start_scroll(-1)

                    BEEP.play(('C4', 'E4', 'G4'), 80)

                else:  # ~~~~~~~~~~~~~~~~~~~ LAUNCH THE APP! ~~~~~~~~~~~~~~~~~~~~

                    # save CONFIG if it has been changed:
                    CONFIG.save()

                    # shut off the display
                    DISPLAY.fill(0)
                    DISPLAY.sleep_mode(True)
                    machine.Pin(_MH_DISPLAY_BACKLIGHT, machine.Pin.OUT).value(0)  # backlight off
                    DISPLAY.spi.deinit()

                    if SD is not None:
                        try:
                            SD.deinit()
                        except:
                            print("Tried to deinit SDCard, but failed.")

                    BEEP.play(('C4', 'B4', 'C5', 'C5'), 100)

                    launch_app(APP_PATHS[APP_NAMES[APP_SELECTOR_INDEX]])

            else:  # keyboard shortcuts!
                for key in new_keys:
                    # jump to letter:
                    # filter special keys
                    if len(key) == 1 and key in 'abcdefghijklmnopqrstuvwxyz1234567890':
                        # search for that letter in the app list
                        for idx in range(len(APP_NAMES)):
                            # this lets us scan starting at the current APP_SELECTOR_INDEX
                            idx = (idx + APP_SELECTOR_INDEX) % len(APP_NAMES)
                            name = APP_NAMES[idx]
                            if name.lower().startswith(key) and idx != APP_SELECTOR_INDEX:
                                # animation:
                                if idx < APP_SELECTOR_INDEX:
                                    direction = -1
                                elif idx > APP_SELECTOR_INDEX:
                                    direction = 1
                                else:
                                    direction = 0
                                # go there!
                                PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                                APP_SELECTOR_INDEX = idx
                                icon.start_scroll(direction)
                                BEEP.play(("G3"), 100)

                                break

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Graphics: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        draw_app_selector(icon)
        DISPLAY.show()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ WIFI and RTC: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # mh_if wifi:
        # if SYNCING_CLOCK:
        #     try_sync_clock()
        # mh_end_if

        # short sleep makes the animation look a little less flickery
        # mh_if not short_sleeps:
        time.sleep_ms(5)
        # mh_end_if


# run the main loop!
main_loop()
