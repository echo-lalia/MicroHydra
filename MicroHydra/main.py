import os
import machine
from sys import path

#default app path is the path to the launcher
app_path = "/launcher/launcher.py"

if machine.reset_cause() != machine.PWRON_RESET: #if this was not a power reset, we are probably launching an app!
    rtc = machine.RTC()
    app_path = rtc.memory().decode()
    
    # special case for passing data along to an app:
    if "|//|" in app_path:
        paths = app_path.split("|//|")
        rtc.memory(app_path.replace(paths[0] + "|//|", ""))
        app_path = paths[0]
    else:
        rtc.memory("/launcher/launcher.py") # for when we reset again

#add apps directory to PATH
path.append('/apps')

# only mount the sd card if the app is on the sd card.
if app_path.startswith("/sd"):
    sd = machine.SDCard(slot=2, sck=machine.Pin(40), miso=machine.Pin(39), mosi=machine.Pin(14), cs=machine.Pin(12))
    try:
        os.mount(sd, '/sd')
        path.append('/sd/apps')
    except OSError:
        with open('log.txt', 'a') as log:
            log.write(f"Couldn't mount SDCard!\n")

# import the requested app!
MAIN_RUN_PRGM = ""

try:
    if '.mpy' in app_path:
        __import__(app_path)
    else:
        with open(app_path,'r') as f:
            tt = f.read()
        
        if 'st7789' in tt or 'ST7789' in tt: #Adapted for CardPuter
            __import__(app_path)
        else:
            rtc.memory('$' + app_path)
            __import__("/launcher/terminal.py")
except Exception as e:
    with open('log.txt', 'a') as log:
        log.write(f"Tried to launch '{app_path}', but failed: '{e}'\n")
    try:
        __import__("/launcher/launcher.py")
    except ImportError:
        print("Launcher couldn't be imported")
