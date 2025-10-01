#!/bin/bash

# Check if at least one board name is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <board_name1> <board_name2> ... <board_nameN>"
    exit 1
fi

# Navigate to the esp-idf directory
cd esp-idf || { echo "Failed to enter esp-idf directory"; exit 1; }

# Source the export.sh script
source export.sh || { echo "Failed to source export.sh"; exit 1; }

echo "esp-idf setup done."

# Navigate to the MicroPython esp32 port directory
cd ../MicroPython/ports/esp32 || { echo "Failed to enter MicroPython/ports/esp32 directory"; exit 1; }

# Loop through all provided board names and build MicroPython for each
for BOARD_NAME in "$@"
do
    echo "Building MicroPython for board: ${BOARD_NAME}"
    make BOARD=${BOARD_NAME} submodules || { echo "Failed to initialize submodules for ${BOARD_NAME}"; exit 1; }
    make BOARD=${BOARD_NAME} || { echo "Failed to build MicroPython for ${BOARD_NAME}"; exit 1; }
    echo "Build complete for board: ${BOARD_NAME}"
done

echo "All builds completed."
