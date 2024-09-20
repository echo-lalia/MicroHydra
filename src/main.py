"""Base 'apploader' for MicroHydra."""

import machine
from lib import sdcard
import sys



# mh_if frozen:
# _LAUNCHER = const(".frozen/launcher/launcher")
# mh_else:
_LAUNCHER = const("/launcher/launcher")
# mh_end_if
sys.path = ['', '/lib', '.frozen', '.frozen/lib']



#default app path is the path to the launcher
app_path = _LAUNCHER

# mh_if TDECK:
# # T-Deck must manually power on its peripherals
# machine.Pin(10, machine.Pin.OUT, value=True)
# mh_end_if

# if this was not a power reset, we are probably launching an app:
if machine.reset_cause() != machine.PWRON_RESET:
    rtc = machine.RTC()
    app_path = rtc.memory().decode()

    # special case for passing data along to an app:
    if "|//|" in app_path:
        paths = app_path.split("|//|")
        rtc.memory(app_path.replace(paths[0] + "|//|", ""))
        app_path = paths[0]
    else:
        # for when we reset again
        rtc.memory(_LAUNCHER)

# only mount the sd card if the app is on the sd card.
if app_path.startswith("/sd"):
    sdcard.SDCard().mount()

# import the requested app!
try:
    if app_path.endswith('.cli.py'): # CLI based app
        rtc.memory('$' + app_path)
        __import__("/launcher/terminal.py")
    else:
        __import__(app_path)

except Exception as e:  # noqa: BLE001
    with open('log.txt', 'a') as log:
        log.write(f"[{app_path}]\n")
        sys.print_exception(e, log)
    # reboot
    rtc.memory(_LAUNCHER)
    machine.reset()

