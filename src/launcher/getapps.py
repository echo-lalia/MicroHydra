"""
This app lets you download new apps from the MicroHydra apps repo.
"""



from lib import userinput
from lib.display import Display
from lib.hydra.config import Config
from lib.hydra.simpleterminal import SimpleTerminal
from lib.device import Device
from lib.zipextractor import ZipExtractor
from lib.hydra.i18n import I18n
import machine
import sys
import network
import requests
import time
import json
import os



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


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

MPY_MATCHES = True

I18N = I18n([
  {"en": "Enabling wifi...", "zh": "正在启用wifi...", "ja": "WiFiを有効にしています..."},
  {"en": "Connected!", "zh": "已连接！", "ja": "接続されました！"},
  {"en": "Getting app catalog...", "zh": "获取应用目录中...", "ja": "アプリカタログを取得中..."},
  {"en": "Failed to get catalog.", "zh": "获取目录失败。", "ja": "カタログの取得に失敗しました。"},
  {"en": "Connecting to GitHub...", "zh": "正在连接到GitHub...", "ja": "GitHubに接続中..."},
  {"en": "Failed to get app.", "zh": "获取应用失败。", "ja": "アプリの取得に失敗しました。"},
  {"en": "Downloading zip...", "zh": "正在下载zip文件...", "ja": "zipファイルをダウンロード中..."},
  {"en": "Finished downloading 'tempapp.zip'", "zh": "已完成下载 'tempapp.zip'", "ja": "'tempapp.zip' のダウンロードが完了しました"},
  {"en": "Finished extracting.", "zh": "解压完成。", "ja": "解凍が完了しました。"},
  {"en": "Removing 'tempapp.zip'...", "zh": "正在删除 'tempapp.zip'...", "ja": "'tempapp.zip' を削除しています..."},
  {"en": "Failed to extract from zip file.", "zh": "从zip文件解压失败。", "ja": "zipファイルからの解凍に失敗しました。"},
  {"en": "Done!", "zh": "完成！", "ja": "完了！"},
  {"en": "Author:", "zh": "作者：", "ja": "著者："},
  {"en": "Description:", "zh": "描述：", "ja": "説明："}
])

#--------------------------------------------------------------------------------------------------
#-------------------------------------- function_definitions: -------------------------------------
#--------------------------------------------------------------------------------------------------


def connect_wifi():
    TERM.print(I18N.trans("Enabling wifi..."))
    NIC.active(True)
    
    attempts = 0
    while not NIC.isconnected():
        try:
            NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
        except OSError as e:
            TERM.print(f"Connection error: {e}")
        TERM.print(f"connecting... {attempts}")
        time.sleep(1)
        attempts += 1
    TERM.print(I18N.trans("Connected!"))


def request_file(file_path):
    return requests.get(
    f'https://api.github.com/repos/echo-lalia/MicroHydra-Apps/contents/catalog-output/{file_path}',
    headers = {
        "accept": "application/vnd.github.v3.raw",
        "User-Agent": f"{Device.name} - MicroHydra",
        }
    )


def fetch_app_catalog():
    """Download compact app catalog from apps repo"""
    
    TERM.print(I18N.trans("Getting app catalog..."))
    
    try:
        response = request_file(f"{Device.name.lower()}.json")
    except Exception as e:
        TERM.print(f"Got error: {e}")
        try:
            response = request_file(f"{Device.name.lower()}.json")
        except:
            TERM.print(I18N.trans("Failed to get catalog."))
            return

    TERM.print(f"Returned code: {response.status_code}")
    
    result = json.loads(response.content)
    response.close()
    return result


# def _request_app(compiled_path, app_name):
#     return requests.get(
#     f'https://api.github.com/repos/echo-lalia/MicroHydra-Apps/contents/catalog-output/{compiled_path}/{app_name}.zip',
#     headers = {
#         "accept": "application/vnd.github.v3.raw",
#         "User-Agent": f"{Device.name} - MicroHydra",
#         }
#     )


def fetch_app(app_name):
    """Download and extract given app from repo"""
    TERM.print("")
    TERM.print(f"Fetching {app_name}.")
    TERM.print(I18N.trans("Connecting to GitHub..."))
    
    compiled_path = "compiled" if MPY_MATCHES else "raw"
    
    
    
    try:
        response = request_file(f"{compiled_path}/{app_name}.zip")
    except OSError as e:
        TERM.print(f"ERROR: {e}")
        try:
            response = request_file(f"{compiled_path}/{app_name}.zip")
        except:
            TERM.print(I18N.trans("Failed to get app."))
            return

    TERM.print(f"Returned code: {response.status_code}")
    
    TERM.print(I18N.trans("Downloading zip..."))
    
    
    buffer = memoryview(bytearray(1024))
    
    socket = response.raw
    with open(f"tempapp.zip", "wb") as fd:
        while (n := socket.readinto(buffer)) > 0:
            fd.write(buffer[:n])
    response.close()

    TERM.print(I18N.trans("Finished downloading 'tempapp.zip'"))
    
    
    # try multiple wbits vals because it's hard to predict what'll error
    # low vals often fail to decode the DEFLATE data
    # high vals run out of memory
    wbits = 8
    while True:
        try:
            TERM.print(f"Extracting zip with wbits={wbits}...")
            ZipExtractor("tempapp.zip").extract('apps', wbits=wbits)
            TERM.print(I18N.trans("Finished extracting."))
            TERM.print(I18N.trans("Removing 'tempapp.zip'..."))
            os.remove('tempapp.zip')
            TERM.print(I18N.trans("Done!"))
            return
            
        except OSError as e:
            if wbits >= 15:
                TERM.print(I18N.trans("Failed to extract from zip file."))
                return
        wbits += 1


#--------------------------------------------------------------------------------------------------
#---------------------------------------- ClassDefinitions: ---------------------------------------
#--------------------------------------------------------------------------------------------------

_AUTHOR_Y = const(_MH_DISPLAY_HEIGHT // 2)
_NAME_Y = const(_MH_DISPLAY_HEIGHT // 4 - 8)
_DESC_Y = const(_AUTHOR_Y + _NAME_Y)
_MAX_H_CHARS = const(_MH_DISPLAY_WIDTH // 8)

class CatalogDisplay:
    def __init__(self, catalog):
        self.mpy_version = catalog.pop("mpy_version")
        
        self.names = list(catalog.keys()) 
        self.catalog = catalog
        
        self.idx = 0

    def move(self, val):
        self.idx += val
        self.idx %= len(self.names)


    @staticmethod
    def split_lines(text:str):
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
            
        lines.append(current_line) # add final line
            
        return lines


    def draw(self):
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
        DISPLAY.text(I18N.trans("Author:"), _DISPLAY_WIDTH_HALF - 28, _AUTHOR_Y - 10, CONFIG.palette[3])
        DISPLAY.text(
            author,
            _DISPLAY_WIDTH_HALF - (len(author) * 4),
            _AUTHOR_Y,
            CONFIG.palette[5],
            )
        
        # draw description
        DISPLAY.text(I18N.trans("Description:"), _DISPLAY_WIDTH_HALF - 48, _DESC_Y - 10, CONFIG.palette[3])
        desc_y = _DESC_Y
        desc_lines = self.split_lines(desc)
        for line in desc_lines:
            DISPLAY.text(
                line,
                _DISPLAY_WIDTH_HALF - (len(line) * 4),
                desc_y,
                CONFIG.palette[6]
                )
            desc_y += 9
        
        
        DISPLAY.show()


#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    global MPY_MATCHES

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    
    connect_wifi()
    catalog = fetch_app_catalog()

    
    # Compare MPY version for downloading compiled files
    mpy_str = f"{sys.implementation._mpy & 0xff}.{sys.implementation._mpy >> 8 & 3}"
    if mpy_str != catalog['mpy_version']:
        MPY_MATCHES = False


    catalog_display = CatalogDisplay(catalog)
    catalog_display.draw()

    time.sleep_ms(400)

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
                elif key in ('G0', 'ENT', 'SPC'):
                    fetch_app(catalog_display.names[catalog_display.idx])
                    time.sleep(2)
                
                elif key in ('ESC', 'q', 'BSPC'):
                    NIC.active(False)
                    machine.reset()
                
            catalog_display.draw()


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # do nothing for 10 milliseconds
        time.sleep_ms(10)



# start the main loop
main_loop()

