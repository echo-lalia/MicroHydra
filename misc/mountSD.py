from lib.sdcard import SDCard

"""
Use this simple tool to mount your SD card. This is useful for transferring files via USB and for editing apps on the SD card.

PS: Probably not a good idea to store important files on the SD card because it could easily become corrupted during testing.

If you're using Thonny to transfer files to and from the device, you probably need to hit "refresh" in the file view to see "/sd" there.

"""

sd = SDCard()
sd.mount()
