"""
This app lets you download new apps from the MicroHydra apps repo.

This built-in app was partially inspired by RealClearwave's "AppStore.py", 
which was contributed to the MH apps repo with commit 014f080.
Thank you for your contributions!
"""



from lib import userinput
from lib.display import Display
from lib.hydra.config import Config
from lib.hydra.simpleterminal import SimpleTerminal
from lib.device import Device
from lib.zipextractor import ZipExtractor
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


#--------------------------------------------------------------------------------------------------
#-------------------------------------- function_definitions: -------------------------------------
#--------------------------------------------------------------------------------------------------


def connect_wifi():
    TERM.print("Enabling wifi...")
    
    if not NIC.active:
        NIC.active(True)
    
    if not NIC.isconnected():    
        # tell wifi to connect (with FORCE)
        while True:
            try: # keep trying until connect command works
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

    TERM.print("Connected!")


def request_file(file_path):
    TERM.print('Making request...')
    response = requests.get(
    f'https://api.github.com/repos/echo-lalia/MicroHydra-Apps/contents/catalog-output/{file_path}',
    headers = {
        "accept": "application/vnd.github.v3.raw",
        "User-Agent": f"{Device.name} - MicroHydra",
        }
    )
    TERM.print(f"Returned code: {response.status_code}")
    return response


def try_request_file(file_path):
    """Capture errors and keep trying to get requested file."""
    wait = 1 # time to wait between attempts (don't get rate limited)
    while True:
        try:
            return request_file(file_path)
        except OSError as e:
            TERM.print(f"Request failed: {e}")
            time.sleep(wait)
            wait += 1


def fetch_app_catalog():
    """Download compact app catalog from apps repo"""
    
    TERM.print("Getting app catalog...")
    
    response = try_request_file(f"{Device.name.lower()}.json")
    
    result = json.loads(response.content)
    response.close()
    return result


def fetch_app(app_name):
    """Download and extract given app from repo"""
    TERM.print("")
    TERM.print(f"Fetching {app_name}.")
    TERM.print("Connecting to GitHub...")
    
    compiled_path = "compiled" if MPY_MATCHES else "raw"
    
    response = try_request_file(f"{compiled_path}/{app_name}.zip")
    
    TERM.print("Downloading zip...")
    
    # download file in chunks:
    buffer = memoryview(bytearray(1024))
    socket = response.raw
    with open(f"tempapp.zip", "wb") as fd:
        while (n := socket.readinto(buffer)) > 0:
            fd.write(buffer[:n])
    response.close()

    TERM.print("Finished downloading 'tempapp.zip'")
    
    
    # try multiple wbits vals because it's hard to predict what'll error
    # low vals often fail to decode the DEFLATE data
    # high vals run out of memory
    wbits = 8
    while True:
        try:
            TERM.print(f"Extracting zip with wbits={wbits}...")
            ZipExtractor("tempapp.zip").extract('apps', wbits=wbits)
            TERM.print("Finished extracting.")
            TERM.print("Removing 'tempapp.zip'...")
            os.remove('tempapp.zip')
            TERM.print("Done!")
            return
            
        except OSError:
            if wbits >= 15:
                TERM.print("Failed to extract from zip file.")
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
        DISPLAY.text("Author:", _DISPLAY_WIDTH_HALF - 28, _AUTHOR_Y - 10, CONFIG.palette[3])
        DISPLAY.text(
            author,
            _DISPLAY_WIDTH_HALF - (len(author) * 4),
            _AUTHOR_Y,
            CONFIG.palette[5],
            )
        
        # draw description
        DISPLAY.text("Description:", _DISPLAY_WIDTH_HALF - 48, _DESC_Y - 10, CONFIG.palette[3])
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

