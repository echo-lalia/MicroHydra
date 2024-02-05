import os
import machine
from machine import RTC

#default app path is the path to the launcher
app_path = "/launcher/launcher.py"


    
if machine.reset_cause() != machine.PWRON_RESET: #if this was not a power reset, we are probably launching an app!
    rtc = machine.RTC()
    app_path = rtc.memory().decode()
    rtc.memory("/launcher/launcher.py") # just in case we reset again


# only mount the sd card if the app is on the sd card.
if len(app_path) >= 4: # if the string is too short it cant possibly be on sd.
    if app_path[:3] == "/sd":
        from machine import SDCard, Pin # trying to save memory by only importing this if we have to
        sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
        try:
            os.mount(sd, '/sd')
        except OSError:
            print("Could not mount SDCard!")



try:
    __import__(app_path)
except ImportError:
    print(f"Tried to launch {app_path}, but failed!")
    
    try:
        __import__("/launcher/launcher.py")
    except ImportError:
        print("App launcher couldn't be imported!")
except ValueError:
    print(f"Tried to launch {app_path}, but failed!")
    try:
        __import__("/launcher/launcher.py")
    except ImportError:
        print("App launcher couldn't be imported!")