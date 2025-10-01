"""Global values that are used by the MicroHydra build scripts."""
import os


# The version to use for this build of MicroHydra
MICROHYDRA_VERSION = (2, 5, 0)

# Relative to src/, this list of files should only be included in the "frozen" MicroHydra firmware
ONLY_INCLUDE_IF_FROZEN = [
    os.path.join('font', 'utf8_8x8.py')
]

# Relative to src/, this list of files should only be included in the non-frozen MicroHydra firmware
DONT_INCLUDE_IF_FROZEN = [
    os.path.join('font', 'utf8_8x8.bin')
]

# These file/dir names in `devices/` should not define new devices
NON_DEVICE_FILES = ['default.yml', 'esp32_mpy_build', 'rp2_mpy_build', 'README.md']

# pairs of microhydra source folders (relative to devices/), and micropython paths to copy them to (relative to MicroPython/)
MPY_BUILD_COPY_FOLDERS = [
    ('esp32_mpy_build', os.path.join('ports', 'esp32')),
    ('rp2_mpy_build', os.path.join('ports', 'rp2')),
]

# src files that shouldn't be compiled
NO_COMPILE = ('main.py', 'apptemplate.py')
