"""This simple module configures and mounts an SDCard."""

import machine
import os



_MH_SDCARD_SLOT = const(2)
_MH_SDCARD_SCK = const(40)
_MH_SDCARD_MISO = const(38)
_MH_SDCARD_MOSI = const(41)
_MH_SDCARD_CS = const(39)



class SDCard:
    """SDCard control."""

    def __init__(self):
        """Initialize the SDCard."""
        self.sd = machine.SDCard(
            slot=_MH_SDCARD_SLOT,
            sck=machine.Pin(_MH_SDCARD_SCK),
            miso=machine.Pin(_MH_SDCARD_MISO),
            mosi=machine.Pin(_MH_SDCARD_MOSI),
            cs=machine.Pin(_MH_SDCARD_CS)
            )


    def mount(self):
        """Mount the SDCard."""
        if "sd" in os.listdir("/"):
            return
        try:
            os.mount(self.sd, '/sd')
        except (OSError, NameError, AttributeError) as e:
            print(f"Could not mount SDCard: {e}")


    def deinit(self):
        """Unmount and deinit the SDCard."""
        os.umount('/sd')
        self.sd.deinit()
