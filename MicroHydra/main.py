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
        print("Could not mount SDCard!")

try:
    __import__(app_path)
except Exception as e:
    print(f"Tried to launch {app_path}, but failed: {e}")    
    try:
        __import__("/launcher/launcher.py")
    except ImportError:
        print("App launcher couldn't be imported!")