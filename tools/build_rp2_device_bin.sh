#!/bin/bash

# Check if at least one board name is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <board_name1> <board_name2> ... <board_nameN>"
    exit 1
fi

# Navigate to the MicroPython rp2 port directory
cd MicroPython/ports/rp2 || { echo "Failed to enter MicroPython/ports/rp2 directory"; exit 1; }

# Loop through all provided board names and build MicroPython for each
for BOARD_NAME in "$@"
do
    echo "Building MicroPython for board: ${BOARD_NAME}"
    make BOARD=${BOARD_NAME} submodules || { echo "Failed to initialize submodules for ${BOARD_NAME}"; exit 1; }
    make BOARD=${BOARD_NAME} clean || { echo "Failed to clean for ${BOARD_NAME}"; exit 1; }
    make BOARD=${BOARD_NAME} || { echo "Failed to build MicroPython for ${BOARD_NAME}"; exit 1; }
    echo "Build complete for board: ${BOARD_NAME}"
done

echo "All builds completed."
