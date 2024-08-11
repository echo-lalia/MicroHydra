#!/bin/bash

# Run file parsing script to create device-specific python files
python3 tools/parse_files.py

# build mpy-cross so we can compile .mpy files
python3 tools/build_mpy_cross.py

# compile .mpy files for each device
python3 tools/compile_hydra_mpy.py


# now get ready to build .bin files
# first, ensure esp-idf is set up
python3 tools/setup_esp_idf.py

# now create device folders under esp32/boards
python3 tools/create_frozen_folders.py

# now run script to build each device
python3 tools/compile_firmwares.py

echo "microhydra_build_all.sh has completed it's work. "
