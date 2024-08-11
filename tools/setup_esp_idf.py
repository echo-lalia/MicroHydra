"""
Script tries to setup esp-idf for building MicroPython.
"""

import subprocess
import os




def setup_idf():
    subprocess.call(["sudo", "./esp-idf/install.sh"])


def launch_wsl():
    """Attempt to use WSL if run from Windows"""
    subprocess.call('wsl -e sh -c "python3 tools/setup_esp_idf.py"')


# build process is convoluted on Windows (and not supported by this script)
#  so if we are on Windows, try launching WSL instead:
is_windows = os.name == 'nt'

if is_windows:
    print("Running in Windows, attempting to use WSL...")
    launch_wsl()
else:
    print("Building mpy_cross...")
    setup_idf()
