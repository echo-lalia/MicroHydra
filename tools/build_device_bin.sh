#!/bin/bash

# Check if the board name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <board_name>"
    exit 1
fi

BOARD_NAME=$1

# Navigate to the esp-idf directory
cd esp-idf || { echo "Failed to enter esp-idf directory"; exit 1; }

# Source the export.sh script
source export.sh || { echo "Failed to source export.sh"; exit 1; }

echo "esp-idf setup done."

# Navigate to the MicroPython esp32 port directory
cd ../MicroPython/ports/esp32 || { echo "Failed to enter MicroPython/ports/esp32 directory"; exit 1; }

# Initialize submodules and build MicroPython for the specified board
make BOARD=${BOARD_NAME} submodules || { echo "Failed to initialize submodules"; exit 1; }
make BOARD=${BOARD_NAME} || { echo "Failed to build MicroPython"; exit 1; }

echo "Build complete for board: ${BOARD_NAME}"
