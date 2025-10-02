"""Communicate with MicroHydras `main.py`.

Values are stored in the RTC or flash, so that information can be retained on soft reset.
"""
# mh_if esp32:
# from machine import RTC, reset
# mh_else:
from machine import reset
# mh_end_if

_PATH_SEP = const("|//|")

def launch_app(*args: str):
    """Set args and reboot."""
    set_args(*args)
    reset()

def set_args(*args: str):
    """Store given args in RTC (for esp32) or flash.

    First arg should typically be an import path.
    """
    # mh_if esp32:
    # RTC().memory(_PATH_SEP.join(args))
    # mh_else:
    with open('/mhargs', 'w') as f:
        f.write(_PATH_SEP.join(args))
    # mh_end_if


def get_args() -> list[str]:
    """Get the args stored in the RTC or flash."""
    # mh_if esp32:
    # return RTC().memory().decode().split(_PATH_SEP)
    # mh_else:
    try:
        with open('/mhargs', 'r') as f:
            return f.read().split(_PATH_SEP)
    except OSError:
        pass
    return ['']
    # mh_end_if

