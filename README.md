<p align="center">
    <a href="https://github.com/echo-lalia/MicroHydra-Apps" alt="Apps">
        <img src="https://img.shields.io/badge/Apps-purple" /></a>
 &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/microhydra-frozen" alt="MicroHydra Firmware">
        <img src="https://img.shields.io/badge/Firmware-purple" /></a>
  &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/Cardputer-MicroHydra/wiki" alt="Wiki">
        <img src="https://img.shields.io/badge/Wiki-slateblue" /></a>
  &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/Cardputer-MicroHydra?tab=GPL-3.0-1-ov-file" alt="License">
        <img src="https://img.shields.io/github/license/echo-lalia/Cardputer-MicroHydra?color=darkslateblue" /></a>
  &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/Cardputer-MicroHydra" alt="Likes">
        <img src="https://img.shields.io/github/stars/echo-lalia/Cardputer-MicroHydra?style=flat&color=darkslateblue" /></a>
</p>


# Cardputer-MicroHydra
MicroHydra is a simple MicroPython based app launcher designed for the M5Stack Cardputer.

<p align="center">
  <img src="https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/15b78e4b-64fc-433a-86d3-979362abd9ab" alt="Microhydra Banner"/>
</p>


This program is still in development, and not all features are fully realized.
This code was built with MicroPython v1.23.0 (preview), for a Generic ESP32-S3 controller.

The main function of MicroHydra is to provide an interface to easily switch between MicroPython apps.   
And to help lower the barriers to entry for anyone wanting to develop apps for their Cardputer. 
Python scripts can be placed in the /apps folder on the flash, or in a /apps folder on a micro sd card. The launcher scans these two locations on startup.   

<br />

Take a look at the [wiki](https://github.com/echo-lalia/Cardputer-MicroHydra/wiki) for some basic guides to get you started with a MicroPython app.

If you're looking for the compiled firmware, that lives over [here](https://github.com/echo-lalia/microhydra-frozen).

And for a work-in-progress repository of MicroHydra apps, see [here](https://github.com/echo-lalia/MicroHydra-Apps)

<br /><br /><br />




# how it works:

This program can be thought of as two main components; the launcher and the apploader.   
The apploader is the "main.py" file in the root directory, and it's the first thing to run when the device is powered on.   
The apploader reads the RTC memory to determine if it should load an app, otherwise, it loads the launcher.

The launcher is the main UI for the app switching functionality. Its primary responsibility is choosing an app, then storing its path in the RTC.memory. 
Once the app path is in the memory, it calls machine.reset() to refresh the system and return to the apploader, after which the apploader loads the target app. 

This approach was chosen to help to prevent issues with memory managment or import conflicts between apps. Resetting the entire device means that the only thing thing loaded before the custom app, is the lightweight apploader.

<br /><br /><br />




# Installing Apps:
Apps are designed to work very simply in this launcher. Any Python file placed in the "apps" folder on the flash, or the SD card, will be found and can be launched as an app. This works with .mpy files too, meaning machine code written in other languages can also be linked and run as an app (though I have not tested this yet)

This means that a simple app can be contained as one script, which will be executed when the app is selected from the launcher.   
It also means more complicated apps can place a startup file in the apps directory, which imports anything it needs from another folder in the filesystem. 

Some apps for MH can be found [here](https://github.com/echo-lalia/MicroHydra-Apps), but there are many other apps (especially work-in-progress apps) living in other locations, as well. 

*Quick note about apps on the SD card: The apps wont be able to use SPI slot 2 for the display (or anything else) because it will be occupied by the SD card. Thankfully, the display works fine in slot 1.*

<br /><br /><br />




# Installing MicroHydra:

You can install MicroHydra a few different ways. 

 - *Install plain .py version on MicroPython:*   
   Flash Micropython to your Cardputer, and copy the contents of the "MicroHydra" folder over to the flash.   
   This is the most convenient way to install for development, because you can simply open up the MH files to see what's going on.   
   You can also find pre-compiled .mpy versions in "compiled.zip", in the releases section. These will use less memory and start faster.   

 - *Flash MH as a compiled firmware:*   
   The latest 'finished' version of MH, frozen into MicroPython, can be found [here](https://github.com/echo-lalia/microhydra-frozen). (Look for the .bin file in 'releases'.)   
   This is a form of MicroPython that has MH built in. This is the fastest and easiest to use form of MH   
   And it can also be downloaded/installed from M5Burner.   
   This has the drawback of not being able to pick apart or modify the core MH files, however.   
   *Make sure you erase the flash before installing. Put your device in download mode by holding G0 when plugging it in, if you are having issues*


<br />
<br />

**Here's a detailed walkthrough for installing MicroPython, and the ".py" form of MicroHydra:**

<br />

Download the code from this repository as a zip file, and extract it somewhere on your computer.   
*Go to the 'releases' section to get .mpy files, or for a stable checkpoint of MH, if you encounter any issues.*

Install Thonny: https://thonny.org/   
*Make sure to use a new version; older versions might fail to flash the ESP32-S3*

<br /> 
<br />
<br />

Open Thonny and click this button in the bottom right:   
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/2464f837-59f0-40d5-860c-52b65d62aa7a)

<br />

Click "configure interpreter", and it should open this menu:   
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/7a51e32e-9864-4d75-bd43-798e99c9d10a)


<br />

click "install or update micropython", and you should see another window:   
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/ef450be6-6025-4bf0-ae0b-e7227209d4ea)

<br />
<br />
<br />

Now you need to plug your Cardputer into the computer with USB. You'll probably have to put it into bootloader mode. 
To do that, press and hold the G0 button on the Cardputer while you plug it into your PC.

The G0 button is on the back edge of the Cardputer, and there's another G0 button on the [Stamp](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/2d65ae77-eb1a-4316-b342-690c7b051d25)   


<br />
<br />
<br />

In "target port" you should now see a device with a name like "USB JTAG". Set the options in the window like this:
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/06022ade-a5c3-4b95-be50-d086f963eb6f)   
And click Install   
*note: version 1.23+ is recommended currently, as it contains an important bugfix affecting MicroHydra's audio*   
*You can also flash the MicroHydra Firmware '.bin' from this menu.*

If installing didn't start, check that the correct device is selected, and it's in bootloader mode.   

<br />

Once It has been flashed with MicroPython, unplug the device and plug it back in.   
Thonny might not automatically detect it right away. If it doesn't, you can select it from the bottom right here:   
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/7835950b-d773-4de7-9d2b-5de1663b2070)   
And you might also need to click the red "stop/restart" button at the top to get it to appear. 

<br />

If you see something like this in the bottom terminal, you've flashed it successfully!   
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/6c4079eb-3921-4f1c-a269-f503a7ccab40)   

<br />
<br />
<br />

To the left in Thonny, there should be a file browser. If there isn't, you need to hit "view">"Files" at the top.   
Navigate to the folder where you downloaded this repository, and into the "MicroHydra" folder. Then, select all of the contents, and hit "Upload to /"   
<img width="271" src="https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/d62bb4ac-f29a-4a7c-8658-e59a886c28fe"> 
![image](https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/85365da5-1aaf-466c-95b1-76b3fc4f9183)

<br />

Once the files are transferred over to the Cardputer, you can test it out by disconnecting it, and powering it on. If everything is working, you should see the main launcher open up!

If you have any issues, feel free to reach out. MH is still growing, and I'm interested to hear of any trouble it might be giving you. 

<p align="center">
  <img src="https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/a0782c5d-5633-489a-a5eb-f6b4e83803ef" alt="Demo GIF"/>
</p>
