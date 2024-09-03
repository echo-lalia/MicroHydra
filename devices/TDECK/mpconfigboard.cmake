set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)
set(IDF_TARGET esp32s3)

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    ${SDKCONFIG_IDF_VERSION_SPECIFIC}
    boards/sdkconfig.usb
    boards/sdkconfig.ble
    boards/sdkconfig.spiram_sx
    boards/ESP32_GENERIC_S3/sdkconfig.board
)


set(SDKCONFIG_DEFAULTS
    ${SDKCONFIG_DEFAULTS}
    boards/sdkconfig.240mhz
    boards/sdkconfig.spiram_oct
)

list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="MicroHydra on TDeck with Octal-SPIRAM"
)

if(MICROPY_BOARD_VARIANT STREQUAL "FLASH_4M")
    set(SDKCONFIG_DEFAULTS
        ${SDKCONFIG_DEFAULTS}
        boards/ESP32_GENERIC_S3/sdkconfig.flash_4m
    )
endif()
