# sdcard

[sdcard](https://github.com/echo-lalia/MicroHydra/blob/main/src/lib/sdcard/mhsdcard.py) provides an interface to mount and unmount the SD Card device.

At its core, the module is a wrapper around the same interface that MicroPython uses.

It exposes a singular class, SDCard.

## constructor:

`sdcard.SDCard()`

> Create the class necessary for mounting the device.

> Args: None.

## mount:

`SDCard.mount()`

> Mounts the available sd card device at /sd in the filesystem.

> This method always returns `None`.

> If the sd card is already mounted, this method does nothing.

> Additionally, if an error is encountered, a message may be sent to `stdout`.

## deinit:

`SDCard.deinit()`

> Unmounts the mounted sd card device.

> Attempting to unmount a mounted device, may cause a system error. See [MicroPython's vfs.umount](https://docs.micropython.org/en/latest/library/vfs.html#vfs.umount) for details.
