import machine
import os



_MH_SDCARD_SLOT = const(2)
_MH_SDCARD_SCK = const(40)
_MH_SDCARD_MISO = const(38)
_MH_SDCARD_MOSI = const(41)
_MH_SDCARD_CS = const(39)



class SDCard:
    def __init__(self):
        self.sd = machine.SDCard(
            slot=_MH_SDCARD_SLOT,
            sck=machine.Pin(_MH_SDCARD_SCK),
            miso=machine.Pin(_MH_SDCARD_MISO), 
            mosi=machine.Pin(_MH_SDCARD_MOSI),
            cs=machine.Pin(_MH_SDCARD_CS)
            )


    def mount(self):
        if "sd" in os.listdir("/"):
            return
        try:
            os.mount(self.sd, '/sd')
        except (OSError, NameError, AttributeError) as e:
            print(f"Could not mount SDCard: {e}")


    def deinit(self):
        os.umount('/sd')
        self.sd.deinit()


    def __del__(self):
        self.deinit()
