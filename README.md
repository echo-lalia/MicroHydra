# Cardputer-MicroHydra
MicroHydra is a simple MicroPython based app launcher designed for the M5Stack Cardputer.

This program is still in early development, but it seems to be working so far. 
This code was built with MicroPython v1.22.1, for a Generic ESP32-S3 controller.

The main function of MicroHydra is to provide an interface to easily switch between MicroPython apps.   
And to help lower the barriers to entry for anyone wanting to develop apps for their Cardputer. 
Python scripts can be placed in the /apps folder on the flash, or in a /apps folder on a micro sd card. The launcher scans these two locations on startup.   

<br />

Take a look at the [wiki](https://github.com/echo-lalia/Cardputer-MicroHydra/wiki) for some basic guides to get you started with a MicroPython app.

If you're looking for the compiled firmware, that lives over [here](https://github.com/echo-lalia/microhydra-frozen).

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

*Quick note about apps on the SD card: The apps wont be able to use SPI slot 2 for the display (or anything else) because it will be occupied by the SD card. Thankfully, the display works fine in slot 1.*

<br /><br /><br />




# Installing MicroHydra:

Flash Micropython to your Cardputer, and copy the contents of the "MicroHydra" folder over to the flash. 

<br />
<br />

**Here's a detailed walkthrough:**

<br />

Download this repository as a zip file, and extract it somewhere on your computer. 

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

