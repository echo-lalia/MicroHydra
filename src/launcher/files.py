"""File browser app.

This file browser app for MicroHydra provides a simple way to view and manage files on the device.
It is also able to launch specific file types
using built-in file viewing/editing apps (such as HyDE.py)
"""

import math
import os
import time

import machine

from font import vga2_16x32 as font
from lib import sdcard, userinput
from lib.display import Display
from lib.hydra import beeper, popup
from lib.hydra.config import Config
from lib.hydra.i18n import I18n


_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)


_TRANS = const("""[
  {"en": "Paste", "zh": "粘贴", "ja": "貼り付け"},
  {"en": "New Directory", "zh": "新建目录", "ja": "新しいディレクトリ"},
  {"en": "New File", "zh": "新建文件", "ja": "新しいファイル"},
  {"en": "Refresh", "zh": "刷新", "ja": "更新"},
  {"en": "Exit to launcher", "zh": "退出到启动器", "ja": "ランチャーに戻る"},
  {"en": "Directory name:", "zh": "目录名称:", "ja": "ディレクトリ名:"},
  {"en": "File name:", "zh": "文件名称:", "ja": "ファイル名:"},
  {"en": "Exiting...", "zh": "正在退出...", "ja": "終了中..."},
  {"en": "open", "zh": "打开", "ja": "開く"},
  {"en": "copy", "zh": "复制", "ja": "コピー"},
  {"en": "rename", "zh": "重命名", "ja": "名前を変更"},
  {"en": "delete", "zh": "删除", "ja": "削除"},
  {"en": "Opening...", "zh": "正在打开...", "ja": "開いています..."}
]""")


_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_ITEMS_PER_SCREEN = const(_MH_DISPLAY_HEIGHT // 32)
_ITEMS_PER_SCREEN_MINUS = const(_ITEMS_PER_SCREEN - 1)
_LEFT_PADDING = const(_MH_DISPLAY_WIDTH // 24)

# calculate padding around items based on amount of unused space
_CHAR_PADDING = const((_MH_DISPLAY_HEIGHT - (_ITEMS_PER_SCREEN * 32)) // _ITEMS_PER_SCREEN)
_LINE_HEIGHT = const(32 + _CHAR_PADDING)

# calculate top padding based on remainder from padded item positions
_TOP_PADDING = const((_MH_DISPLAY_HEIGHT - (_LINE_HEIGHT * _ITEMS_PER_SCREEN) + 1) // 2)

_CHARS_PER_SCREEN = const(_MH_DISPLAY_WIDTH // 16)

_SCROLLBAR_WIDTH = const(3)
_SCROLLBAR_START_X = const(_MH_DISPLAY_WIDTH - _SCROLLBAR_WIDTH)

# for horizontal text scroll animation:
_SCROLL_TIME = const(5000)  # ms per one text scroll

# Delimiter for multiple main.py paths
_PATH_JOIN = const("|//|")

# hamburger menu icon:
_HAMBURGER_WIDTH = const(32)
_HAMBURGER_X = const(_DISPLAY_WIDTH_HALF - (_HAMBURGER_WIDTH // 2))
_HAMBURGER_HEIGHT = const(2)
_HAMBURGER_PADDING = const(10)
_HAMBURGER_OFFSET = const(6)


_DIR_MARKER = const(0x4000)

# mh_if frozen:
# FILE_HANDLERS = {
#     "": ".frozen/launcher/HyDE.py", # default
#     "py": ".frozen/launcher/HyDE.py",
#     "txt": ".frozen/launcher/HyDE.py",
#     }
# mh_else:
FILE_HANDLERS = {
    "": "/launcher/HyDE.py",  # default
    "py": "/launcher/HyDE.py",
    "txt": "/launcher/HyDE.py",
    }
# mh_end_if


I18N = I18n(_TRANS)

kb = userinput.UserInput()
tft = Display()

config = Config()
beep = beeper.Beeper()
overlay = popup.UIOverlay(i18n=I18N)

sd = sdcard.SDCard()

# copied_file = None
clipboard = None



class ListView:
    """Container for filelist."""

    def __init__(
            self,
            tft: Display,
            config: Config,
            items: list,
            dir_dict: dict):
        """Create a ListView.

        Args:
            tft: a Display object
            config: A Config object
            items: A list of file items
            dir_dict: A dict of bools denoting which items are directories
        """
        self.tft = tft
        self.config = config
        self.items = items
        self.dir_dict = dir_dict
        self.view_index = 0
        self.cursor_index = 0


    @staticmethod
    def draw_hamburger_menu(tft, y, color):
        """Draw a simple hamburger menu."""
        for i in range(3):
            tft.rect(
                _HAMBURGER_X,
                y + _HAMBURGER_PADDING + _HAMBURGER_OFFSET*i,
                _HAMBURGER_WIDTH,
                _HAMBURGER_HEIGHT,
                color,
            )


    def draw(self):
        """Draw list to display."""
        tft = self.tft
        tft.fill(self.config.palette[2])

        for idx in range(_ITEMS_PER_SCREEN):
            item_index = idx + self.view_index
            # only draw rows with items
            if item_index >= len(self.items):
                break

            mytext = self.items[item_index]

            # style based on selected:
            if item_index == self.cursor_index:
                # draw selection box
                tft.rect(
                    0,
                    idx*_LINE_HEIGHT + _TOP_PADDING,
                    _SCROLLBAR_START_X,
                    32,
                    self.config.palette[1],
                    fill=True,
                    )
                clr_idx = 8
            else:
                clr_idx = 6

            # special stylilng on menu button
            if mytext == "/.../":
                self.draw_hamburger_menu(tft, idx * _LINE_HEIGHT + _TOP_PADDING, self.config.palette[clr_idx])
                break  # hamburger menu is always last

            # special styling for directories
            if self.dir_dict[self.items[item_index]]:
                mytext += "/"
                clr_idx -= 1

            # scroll text if too long
            if len(mytext) > _CHARS_PER_SCREEN:
                scroll_distance = (len(mytext) - _CHARS_PER_SCREEN) * -16
                x = int(ping_pong_ease(time.ticks_ms(), _SCROLL_TIME) * scroll_distance)
            else:
                x = _LEFT_PADDING

            tft.text(
                mytext,
                x,
                idx * _LINE_HEIGHT + _TOP_PADDING,
                self.config.palette[clr_idx],
                font=font,
                )

        # draw scrollbar
        scrollbar_height = _MH_DISPLAY_HEIGHT // max(1, (len(self.items) - _ITEMS_PER_SCREEN_MINUS))
        scrollbar_y = int(
            (self.view_index / max(len(self.items) - _ITEMS_PER_SCREEN, 1))
            * (_MH_DISPLAY_HEIGHT - scrollbar_height),
            )
        tft.rect(
            _SCROLLBAR_START_X,
            scrollbar_y,
            _SCROLLBAR_WIDTH,
            scrollbar_height,
            self.config.palette[4],
            fill=True,
            )


    def clamp_cursor(self):
        """Keep cursor in item range + keep view on cursor."""
        self.cursor_index %= len(self.items)
        self._view_to_cursor()


    def _view_to_cursor(self):
        if self.cursor_index < self.view_index:
            self.view_index = self.cursor_index
        if self.cursor_index >= self.view_index + _ITEMS_PER_SCREEN:
            self.view_index = self.cursor_index - _ITEMS_PER_SCREEN + 1


    def up(self):
        """Move cursor up."""
        self.cursor_index = (self.cursor_index - 1) % len(self.items)
        self._view_to_cursor()


    def down(self):
        """Move cursor down."""
        self.cursor_index = (self.cursor_index + 1) % len(self.items)
        self._view_to_cursor()


def ease_in_out_sine(x: float) -> float:
    """Apply an easing function to given float."""
    return -(math.cos(math.pi * x) - 1) / 2


def ping_pong_ease(value: int, modulo: int) -> float:
    """Get 'ping-pong' easing for given value and max.

    "ping pong"s a value in a given modulo range,
    and applies an easing function to the result,
    returning a float between 0.0 and 1.0
    """
    odd_pong = ((value // modulo) % 2 == 1)

    fac = ease_in_out_sine((value % modulo) / modulo)

    if odd_pong:
        return 1 - (fac)
    return (fac)



def path_join(*args) -> str:
    """Join multiple paths together."""
    path = "/".join(args)
    # Remove any repeated slashes
    while "//" in path:
        path = path.replace("//", "/")
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    return path


def path_split(path_str) -> tuple[str, str]:
    """Split last element off of path. (similar to os.path.split)."""
    # Early return on root dir
    if path_str == "/":
        return "/", ""

    *head, tail = path_str.split("/")
    head = path_join(*head)
    return head, tail


def prev_dir():
    """Move back to the previous directory (similar to "..")."""
    # this funciton is needed because ".." doesn't work as expected with SDCards
    # If you chdir("..") on "/sd" you will not move.
    # And, if you chdir("..") back to "/" from anywhere else,
    # "/sd" won't show up on os.listdir()
    head = path_split(os.getcwd())[0]
    if not head:
        head = "/"
    os.chdir(head)


def parse_files()  -> tuple[list, dict]:
    """Get a list of directories/files, and a dictionary of which is which.

    Parse result of os.ilistdir() into a sorted list,
    Returns a tuple, where the first item is a list of the directory contents,
    and the second item is a dictionary, marking list items as directories.
    """
    dirdict = {}
    dirlist = []
    filelist = []
    # add directories to the top
    for ilist in os.ilistdir():
        name = ilist[0]; itype = ilist[1]
        if itype == _DIR_MARKER:
            dirlist.append(name)
            dirdict[name] = True
        else:
            filelist.append(name)
            dirdict[name] = False
    dirlist.sort()
    filelist.sort()
    # append special option to view for adding new files
    filelist.append("/.../")

    return (dirlist + filelist, dirdict)


def ext_options(overlay):
    """Create popup with options for new file or directory."""
    cwd = os.getcwd()

    options = ["Paste", "New Directory", "New File", "Refresh", "Exit to launcher"]

    if clipboard is None:
        # dont give the paste option if there's nothing to paste.
        options.pop(0)

    option = overlay.popup_options(options, title=f"{cwd}:")
    if option == "New Directory":
        beep.play(("D3"), 30)
        name = overlay.text_entry(title="Directory name:")
        beep.play(("G3"), 30)
        try:
            os.mkdir(name)
        except Exception as e:  # noqa: BLE001
            overlay.error(e)

    elif option == "New File":
        beep.play(("B3"), 30)
        name = overlay.text_entry(title="File name:")
        beep.play(("G3"), 30)
        try:
            with open(name, "w") as newfile:
                newfile.write("")
        except Exception as e:  # noqa: BLE001
            overlay.error(e)

    elif option == "Refresh":
        beep.play(("B3", "G3", "D3"), 30)
        sd.mount()
        os.sync()

    elif option == "Paste":
        beep.play(("D3", "G3", "D3"), 30)

        source_path, file_name = clipboard

        source = path_join(source_path, file_name)
        dest = path_join(cwd, file_name)

        if source == dest:
            dest += ".bak"

        with open(source, "rb") as old_file, open(dest, "wb") as new_file:
            while True:
                l = old_file.read(512)
                if not l:
                    break
                new_file.write(l)


    elif option == "Exit to launcher":
        overlay.draw_textbox("Exiting...")
        tft.show()
        rtc = machine.RTC()
        rtc.memory('')
        machine.reset()


def file_options(file, overlay):
    """Create popup with file options for given file."""
    global clipboard  # noqa: PLW0603

    options = ("open", "copy", "rename", "delete")
    option = overlay.popup_options(options, title=f'"{file}":')

    if option == "open":
        beep.play(("G3"), 30)
        open_file(file)
    elif option == "copy":
        # store copied file to clipboard
        clipboard = (os.getcwd(), file)

        beep.play(("D3", "G3", "D3"), 30)


    elif option == "rename":
        beep.play(("B3"), 30)
        new_name = overlay.text_entry(start_value=file, title=f"Rename '{file}':")
        os.rename(file, new_name)

    elif option == "delete":
        beep.play(("D3"), 30)
        confirm = overlay.popup_options(
            (("cancel",), ("confirm",)),
            title=f'Delete "{file}"?',
            depth=1,
            )
        if confirm == "confirm":
            beep.play(("D3", "B3", "G3", "G3"), 30)
            os.remove(file)


def open_file(file):
    """Reboot/open a file with relevant file handler."""
    cwd = os.getcwd()
    if not cwd.endswith("/"):
        cwd += "/"
    filepath = cwd + file

    # visual feedback
    overlay.draw_textbox(f"Opening {filepath}...")
    tft.show()

    filetype = file.split(".")[-1].lower()
    if filetype not in FILE_HANDLERS:
        filetype = ""
    handler = FILE_HANDLERS[filetype]

    full_path = handler + _PATH_JOIN + filepath

    # write path to RTC memory
    rtc = machine.RTC()
    rtc.memory(full_path)
    time.sleep_ms(10)
    machine.reset()


def refresh_files(view: ListView) -> tuple[list, dict]:
    """Reload and set the ListView."""
    file_list, dir_dict = parse_files()
    view.items = file_list
    view.dir_dict = dir_dict
    view.clamp_cursor()
    return file_list, dir_dict


def panic_recover() -> tuple[ListView, list, dict]:
    """When an error would cause a crash, try recovering instead."""
    os.chdir('/')
    file_list, dir_dict = parse_files()
    view = ListView(tft, config, file_list, dir_dict)
    return view, file_list, dir_dict


def handle_input(key, view, file_list, dir_dict) -> tuple[list, dict]:
    """React to user inputs."""
    if key == "UP":
        view.up()
        beep.play(("G3", "B3"), 30)
    elif key == "DOWN":
        view.down()
        beep.play(("D3", "B3"), 30)

    elif key in {kb.main_action, kb.secondary_action}:
        beep.play(("G3", "B3", "D3"), 30)
        selection_name = file_list[view.cursor_index]
        if selection_name == "/.../":  # new file
            ext_options(overlay)
            file_list, dir_dict = refresh_files(view)

        elif dir_dict[selection_name]:
            # this is a directory, open it
            os.chdir(selection_name)
            file_list, dir_dict = refresh_files(view)
        else:
            # this is a file, give file options
            file_options(file_list[view.cursor_index], overlay)
            file_list, dir_dict = refresh_files(view)

    elif key ==  "BSPC":
        beep.play(("D3", "B3", "G3"), 30)
        prev_dir()
        file_list, dir_dict = refresh_files(view)

    elif key == kb.aux_action:
        ext_options(overlay)
        file_list, dir_dict = refresh_files(view)

    return file_list, dir_dict


def main_loop(tft, kb, config, overlay):
    """Run the main loop."""

    new_keys = kb.get_new_keys()
    sd.mount()
    file_list, dir_dict = parse_files()

    view = ListView(tft, config, file_list, dir_dict)

    while True:
        new_keys = kb.get_new_keys()
        kb.ext_dir_keys(new_keys)

        try:
            for key in new_keys:
                file_list, dir_dict = handle_input(key, view, file_list, dir_dict)

        except (OSError, UnicodeError) as e:
            # File operations can sometimes have unexpected results
            overlay.error(repr(e))
            view, file_list, dir_dict = panic_recover()

        view.draw()
        tft.show()

        time.sleep_ms(10)


main_loop(tft, kb, config, overlay)
