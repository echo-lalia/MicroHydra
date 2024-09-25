"""This app lets you download new apps from the MicroHydra apps repo.

This built-in app was partially inspired by RealClearwave's "AppStore.py",
which was contributed to the MH apps repo with commit 014f080.
Thank you for your contributions!
"""



import json
import os
import sys
import time

import machine
import network
import requests

from lib import userinput
from lib.device import Device
from lib.display import Display
from lib.hydra.config import Config
from lib.hydra.i18n import I18n
from lib.hydra.simpleterminal import SimpleTerminal
from lib.zipextractor import ZipExtractor


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


_TRANS = const("""[
{"en": "Enabling wifi...", "zh": "正在启用wifi...", "ja": "WiFiを有効にしています..."},
{"en": "Connected!", "zh": "已连接!", "ja": "接続されました!"},
{"en": "Getting app catalog...", "zh": "获取应用目录中...", "ja": "アプリカタログを取得中..."},
{"en": "Failed to get catalog.", "zh": "获取目录失败。", "ja": "カタログの取得に失敗しました。"},
{"en": "Connecting to GitHub...", "zh": "正在连接到GitHub...", "ja": "GitHubに接続中..."},
{"en": "Failed to get app.", "zh": "获取应用失败。", "ja": "アプリの取得に失敗しました。"},
{"en": "Downloading zip...", "zh": "正在下载zip文件...", "ja": "zipファイルをダウンロード中..."},
{"en": "Finished downloading 'tempapp.zip'", "zh": "已完成下载 'tempapp.zip'", "ja": "'tempapp.zip' のダウンロードが完了しました"},
{"en": "Finished extracting.", "zh": "解压完成。", "ja": "解凍が完了しました。"},
{"en": "Removing 'tempapp.zip'...", "zh": "正在删除 'tempapp.zip'...", "ja": "'tempapp.zip' を削除しています..."},
{"en": "Failed to extract from zip file.", "zh": "从zip文件解压失败。", "ja": "zipファイルからの解凍に失敗しました。"},
{"en": "Done!", "zh": "完成!", "ja": "完了!"},
{"en": "Author:", "zh": "作者:", "ja": "著者:"},
{"en": "Description:", "zh": "描述:", "ja": "説明:"}
]""")  # noqa: E501

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL_OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = Display(
    # mh_if spi_ram:
    # use_tiny_buf=False,
    # mh_else:
    use_tiny_buf=True,
    # mh_end_if
    )

# object for accessing microhydra config (Delete if unneeded)
CONFIG = Config()

# object for reading keypresses (or other user input)
INPUT = userinput.UserInput()

NIC = network.WLAN(network.STA_IF)


TERM = SimpleTerminal()

I18N = I18n(_TRANS)

# --------------------------------------------------------------------------------------------------
# -------------------------------------- function_definitions: -------------------------------------
# --------------------------------------------------------------------------------------------------


def connect_wifi():
    """Connect to the configured WiFi network."""
    TERM.print(I18N["Enabling wifi..."])

    if not NIC.active():
        NIC.active(True)

    if not NIC.isconnected():
        # tell wifi to connect (with FORCE)
        while True:
            try:  # keep trying until connect command works
                NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
                break
            except OSError as e:
                TERM.print(f"Error: {e}")
                time.sleep_ms(500)

        # now wait until connected
        attempts = 0
        while not NIC.isconnected():
            TERM.print(f"connecting... {attempts}")
            time.sleep_ms(500)
            attempts += 1

    TERM.print(I18N["Connected!"])


def request_file(file_path: str) -> requests.Response:
    """Get the specific app file from GitHub."""
    TERM.print('Making request...')
    response = requests.get(  # noqa: S113 # no point using a timeout here
        f'https://raw.githubusercontent.com/echo-lalia/MicroHydra-Apps/main/catalog-output/{file_path}',
        headers={
            "accept": "application/vnd.github.v3.raw",
            "User-Agent": f"{Device.name} - MicroHydra",
            },
        )
    TERM.print(f"Returned code: {response.status_code}")
    return response


def try_request_file(file_path: str) -> requests.Response:
    """Capture errors and keep trying to get requested file."""
    wait = 1  # time to wait between attempts (don't get rate limited)
    while True:
        try:
            return request_file(file_path)
        except (OSError, ValueError) as e:  # noqa: PERF203
            TERM.print(f"Request failed: {e}")
            time.sleep(wait)
            wait += 1


def fetch_app_catalog() -> dict:
    """Download compact app catalog from apps repo."""

    TERM.print(I18N["Getting app catalog..."])

    response = try_request_file(f"{Device.name.lower()}.json")

    result = json.loads(response.content)
    response.close()
    return result


_MAX_WBITS = const(15)
def fetch_app(app_name, mpy_matches):
    """Download and extract given app from repo."""
    TERM.print("")
    TERM.print(f"Fetching {app_name}.")
    TERM.print(I18N["Connecting to GitHub..."])

    compiled_path = "compiled" if mpy_matches else "raw"

    response = try_request_file(f"{compiled_path}/{app_name}.zip")

    TERM.print(I18N["Downloading zip..."])

    # download file in chunks:
    buffer = memoryview(bytearray(1024))
    socket = response.raw
    with open("tempapp.zip", "wb") as fd:
        while (n := socket.readinto(buffer)) > 0:
            fd.write(buffer[:n])
    response.close()

    TERM.print(I18N["Finished downloading 'tempapp.zip'"])


    # try multiple wbits vals because it's hard to predict what'll error
    # low vals often fail to decode the DEFLATE data
    # high vals run out of memory
    wbits = 8
    while True:
        try:
            TERM.print(f"Extracting zip with wbits={wbits}...")
            ZipExtractor("tempapp.zip").extract('apps', wbits=wbits)
            TERM.print(I18N["Finished extracting."])
            TERM.print(I18N["Removing 'tempapp.zip'..."])
            os.remove('tempapp.zip')
            TERM.print(I18N["Done!"])

        except OSError:
            if wbits >= _MAX_WBITS:
                TERM.print(I18N["Failed to extract from zip file."])
                return
        else:  # return if extraction was a success
            return

        wbits += 1


# --------------------------------------------------------------------------------------------------
# ---------------------------------------- ClassDefinitions: ---------------------------------------
# --------------------------------------------------------------------------------------------------

_AUTHOR_Y = const(_MH_DISPLAY_HEIGHT // 2)
_NAME_Y = const(_MH_DISPLAY_HEIGHT // 4 - 8)
_DESC_Y = const(_AUTHOR_Y + _NAME_Y)
_MAX_H_CHARS = const(_MH_DISPLAY_WIDTH // 8)


class CatalogDisplay:
    """Construct for displaying and selecting catalog options."""

    def __init__(self, catalog: dict):
        """Create a Catalog using given dict."""
        self.mpy_version = catalog.pop("mpy_version")

        self.names = list(catalog.keys())
        # sort alphabetically without uppercase/lowercase discrimination:
        self.names.sort(key=lambda st: st.lower())

        self.catalog = catalog

        self.idx = 0

    def move(self, val: int):
        """Move the selector index by `val`."""
        self.idx += val
        self.idx %= len(self.names)


    def jump_to(self, letter):
        """Jump to the next app that starts with the given letter."""
        # search for that letter in the app list
        for i in range(1, len(self.names)):
            # scan to the right, starting at self.idx
            i = (i + self.idx) % len(self.names)
            name = self.names[i]
            if name.lower().startswith(letter):
                self.idx = i
                return


    @staticmethod
    def split_lines(text: str) -> list:
        """Split a string into multiple lines, based on max line-length."""
        lines = []
        current_line = ''
        words = text.split()

        for word in words:
            if len(word) + len(current_line) >= _MAX_H_CHARS:
                lines.append(current_line)
                current_line = word
            elif len(current_line) == 0:
                current_line += word
            else:
                current_line += ' ' + word

        lines.append(current_line)  # add final line

        return lines


    def draw(self):
        """Draw the selected option to the display."""
        name = self.names[self.idx]
        # separate author
        *desc, author = self.catalog[name].split(' - ')
        desc = ' - '.join(desc)

        # blackout bg
        DISPLAY.fill(CONFIG.palette[2])

        # draw box around name
        DISPLAY.rect(0, _NAME_Y - 8, _MH_DISPLAY_WIDTH, 24, CONFIG.palette[3], fill=True)

        # draw name
        DISPLAY.text('<', 8, _NAME_Y, CONFIG.palette[4])
        DISPLAY.text('>', _MH_DISPLAY_WIDTH - 16, _NAME_Y, CONFIG.palette[4])
        DISPLAY.text(name, _DISPLAY_WIDTH_HALF - (len(name) * 4), _NAME_Y+1, CONFIG.palette[5])
        DISPLAY.text(name, _DISPLAY_WIDTH_HALF - (len(name) * 4), _NAME_Y, CONFIG.palette[8])

        # draw author
        DISPLAY.text(I18N["Author:"], _DISPLAY_WIDTH_HALF - 28, _AUTHOR_Y - 10, CONFIG.palette[3])
        DISPLAY.text(
            author,
            _DISPLAY_WIDTH_HALF - (len(author) * 4),
            _AUTHOR_Y,
            CONFIG.palette[5],
            )

        # draw description
        DISPLAY.text(
            I18N["Description:"],
            _DISPLAY_WIDTH_HALF - 48,
            _DESC_Y - 10,
            CONFIG.palette[3],
            )
        desc_y = _DESC_Y
        desc_lines = self.split_lines(desc)
        for line in desc_lines:
            DISPLAY.text(
                line,
                _DISPLAY_WIDTH_HALF - (len(line) * 4),
                desc_y,
                CONFIG.palette[6],
                )
            desc_y += 9

        DISPLAY.show()


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop of the program."""

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    connect_wifi()
    catalog = fetch_app_catalog()

    # Compare MPY version for downloading compiled files
    mpy_str = f"{sys.implementation._mpy & 0xff}.{sys.implementation._mpy >> 8 & 3}"  # noqa: SLF001
    mpy_matches = (mpy_str == catalog["mpy_version"])

    # sleep so user can see confirmation message
    time.sleep_ms(400)

    catalog_display = CatalogDisplay(catalog)
    catalog_display.draw()


    while True:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # get list of newly pressed keys
        keys = INPUT.get_new_keys()
        INPUT.ext_dir_keys(keys)

        # if there are keys, convert them to a string, and store for display
        if keys:
            for key in keys:
                if key == 'RIGHT':
                    catalog_display.move(1)
                elif key == 'LEFT':
                    catalog_display.move(-1)
                elif key in {'G0', 'ENT', 'SPC'}:
                    fetch_app(catalog_display.names[catalog_display.idx], mpy_matches)
                    time.sleep(2)

                elif key in {'ESC', 'BSPC'}:
                    NIC.active(False)
                    machine.reset()

                elif len(key) == 1:
                    catalog_display.jump_to(key)

            catalog_display.draw()


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # do nothing for 10 milliseconds
        time.sleep_ms(10)



# start the main loop
main_loop()
