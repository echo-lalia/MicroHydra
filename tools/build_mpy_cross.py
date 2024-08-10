"""
Script tries to build mpy-cross for MicroHydra.
"""

import subprocess
import os




def make_mpy_cross():
    subprocess.call(["make", "-C", "MicroPython/mpy-cross"])


def launch_wsl():
    """Attempt to use WSL if run from Windows"""
    subprocess.call('wsl -e sh -c "python3 tools/build_mpy_cross.py"')


# build process is convoluted on Windows (and not supported by this script)
#  so if we are on Windows, try launching WSL instead:
is_windows = os.name == 'nt'

if is_windows:
    print("Running in Windows, attempting to use WSL...")
    launch_wsl()
else:
    print("Building mpy_cross...")
    make_mpy_cross()
