import os
from machine import RTC, SDCard, Pin

"""
Use this simple tool to unmount your SD card.
Not sure if this one is actually useful, but I thought I'd provide it for completion sake.


"""



    
try:
    sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
    sd.deinit()
except:
    print("couldn't deinit SDCard")
    
try:
    os.umount('/sd')
except OSError as e:
    print(e)
    print("Could not unmount SDCard!")
