import os
import machine
from lib import sdcard
import sys

sys.path = ['', '/lib', '.frozen', '.frozen/lib']

#default app path is the path to the launcher
# mh_if frozen:
# app_path = ".frozen/launcher/launcher"
# mh_else:
app_path = "/launcher/launcher"
# mh_end_if

# mh_if TDECK:
# # T-Deck must manually power on its peripherals
# machine.Pin(10, machine.Pin.OUT, value=True)
# mh_end_if

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

# only mount the sd card if the app is on the sd card.
if app_path.startswith("/sd"):
    sdcard.SDCard().mount()

# import the requested app!
try:
    __import__(app_path)
except Exception as e:
    with open('log.txt', 'a') as log:
        log.write(f"Tried to launch '{app_path}', but failed: '{e}'\n")
    try:
        # mh_if frozen:
        # __import__(".frozen/launcher/launcher")
        # mh_else:
        __import__("/launcher/launcher")
        # mh_end_if
    except ImportError:
        print("Launcher couldn't be imported")