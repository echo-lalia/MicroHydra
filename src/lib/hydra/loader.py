"""Communicate with MicroHydras `main.py`.

Values are stored in the RTC, so that information can be retained on soft reset.
"""
from machine import RTC, reset

_PATH_SEP = const("|//|")

def launch_app(*args: str):
    """Set args and reboot."""
    set_args(*args)
    reset()

def set_args(*args: str):
    """Store given args in RTC.

    First arg should typically be an import path.
    """
    RTC().memory(_PATH_SEP.join(args))

def get_args() -> list[str]:
    """Get the args stored in the RTC."""
    return RTC().memory().decode().split(_PATH_SEP)
