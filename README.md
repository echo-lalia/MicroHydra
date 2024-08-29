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


# MicroHydra
MicroHydra is a simple MicroPython based app launcher with some OS-like features.

<p align="center">
  <img src="https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/15b78e4b-64fc-433a-86d3-979362abd9ab" alt="Microhydra Banner"/>
</p>

This code was built with MicroPython v1.23, for the ESP32-S3.

The main function of MicroHydra is to provide an interface to easily switch between MicroPython apps.   
And to help lower the barriers to entry for anyone wanting to develop apps for their Cardputer (or other supported device!). 
Python scripts can be placed in your device's /apps folder (on the flash), or in a /apps folder on a micro sd card. The launcher scans these two locations on startup.   

<br />

Take a look at the [wiki](https://github.com/echo-lalia/MicroHydra/wiki) for some basic guides to get you started with a MicroPython app.

And for a repository of community-made MicroHydra apps, see [here](https://github.com/echo-lalia/MicroHydra-Apps).

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

Some apps for MH can be found [here](https://github.com/echo-lalia/MicroHydra-Apps), but there are other apps (especially work-in-progress apps) living in other locations, as well. 

<br /><br /><br />




# Installing MicroHydra:

You can install MicroHydra a few different ways. 

 - [*Install on top of a normal MicroPython installation:*](#In-MicroPython)   
   Flash Micropython to your Cardputer, and copy the contents of the `DEVICENAME_compiled.zip` (or `DEVICENAME_raw.zip`) file from the "releases" section to the flash on your device.   
    > This is the most convenient way to install for development, because you can simply open up the MicroHydra files to see what's goin on. However, the `raw` (as in, ending with ".py") form of the software is much more susceptible to memory issues than the other installation methods, so it's reccomended that you use the compiled (`.mpy`) version for any files that you aren't specifically working inside of.



 - [*Flash MH as a compiled firmware:*](#As-a-complete-firmware)   
   You can flash MicroHydra (along with MicroPython) directly to your device using the `DEVICENAME.bin` file from the "Releases" section. (You can also usually find the most recent builds on M5Burner). This is the fastest and easiest to use form of MH!   
   > In this installation, the MicroHydra files have been 'frozen' into the MicroPython firmware. This makes the built-in files load *much* faster, and makes them all use less memory.  
   *Make sure you erase the flash before installing, and put your device in download mode by holding G0 when plugging it in.*

> **Note for developers:** *The contents of `src/` must be processed in order to output device-specific MicroHydra builds. To learn more, take a look at [this](https://github.com/echo-lalia/MicroHydra/wiki/multi-platform) page in the wiki.*

-----

<br /><br />
<br /><br />
<br /><br />
<br /><br />
<br /><br />
<br /><br />







# In MicroPython

*This is a detailed guide for installing MicroHydra on a regular MicroPython installation, using Thonny.*

<br /> 
<br />

## Install Thonny

Thonny is a tool that provides a very easy way to flash MicroPython, edit code, and view/edit the files on the device.

You can follow the instructions here to install it: https://thonny.org/   
> *Make sure to use a new version; older versions might fail to flash the ESP32-S3*
>
> *Some sources of Thonny (such as with certain built-in package managers) can result in strange issues with permissions or missing dependencies. If you encounter an issue with thonny when setting it up, and there is no other clear solution to your problem, it might be a good idea to try installing from another source.*

<br /> 
<br />
<br />

## Flash MicroPython
Next we need to flash MicroPython on your device 

Open Thonny, click this button in the bottom right, and click "Configure interpreter":   
<p>
  <img src="misc\images\thonnyhamburgermenu.png" height="300" hspace="10"/><img src="misc\images\thonnyconfigureinterpreter.png" height="300" hspace="10"/>
</p>

<br />

It should open this menu:   
<img src="misc\images\thonnyinterpreteroptions.png" width="500"/>


<br />

click "install or update micropython", and you should see another window:   
<p>
  <img src="misc\images\thonnyinstallmicropython.png" height="300" hspace="10"/><img src="misc\images\thonnyinstallmicropythonwindow.png" height="300" hspace="10"/>
</p>

<br />
<br />




Now you need to put your device into bootloader mode, and connect it to your computer. To do this, simply hold the `G0` button as you connect it to your PC.

<img src="misc\images\cardputerg0.jpg" width="200"/>

> *You can also hold `G0` and tap the reset button to get to bootloader mode.*  
> *If you are using a device like the TDeck, which doesn't power on when plugged in, you must hold `g0` and then flip the power switch on.*

<br />
<br />

In "target port" you should now see a device with a name like "USB JTAG". Set the options as shown, and click "Install":  
<img src="misc\images\thonnyflashsettings.png" width="400"/>
> *For a device with Octal-SPIRAM (like the TDeck), you will have to download a specific Octal-SPIRAM variant from the [MicroPython website.](https://micropython.org/download/ESP32_GENERIC_S3/)*

> *If installing didn't start, check that the correct device is selected, and it's in bootloader mode.*   

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

## Install MicroHydra

Now you can download and install MicroHydra.  
To get the apropriate files for your device, you should head to the "Releases" section of the GitHub page, and look for a `DEVICENAME_compiled.zip` or `DEVICENAME_raw.zip` file.

<p>
  <img src="misc\images\releases.png" height="300" hspace="10"/><img src="misc\images\releasecompiled.png" height="300" hspace="20"/>
</p>

Extract the .zip file, and head back over to Thonny.

We need to use Thonnys file browser. If you don't see it to your left, you can bring it up by clicking view>Files in the top left.
<img width="400" src="misc\images\thonnyfiles.png"> 

<br />

On the top half of the file browser, navigate to the folder where you extracted the MicroHydra zip file.  
Then, select all of the contents, and hit `Upload to /`   
<img height="260" src="misc\images\thonnyuploadfiles.png"> <img height="260" src="misc\images\thonnyuploadfiles2.png"> 

<br />

Once the files are transferred over, you can test it out by disconnecting it, and powering it on. If everything is working, you should see the main launcher open up!

If you have any issues, feel free to reach out. MH is still growing, and I'm interested to hear of any trouble it might be giving you. 

----

<br /><br />
<br /><br />
<br /><br />
<br /><br />
<br /><br />
<br /><br />







# As a complete firmware

*This is a detailed guide for flashing the MicroHydra firmware on your device, using Thonny.*

<br /> 
<br />

## Install Thonny

Thonny is a tool that provides a very easy way to flash MicroPython, edit code, and view/edit the files on the device.

You can follow the instructions here to install it: https://thonny.org/   
> *Make sure to use a new version; older versions might fail to flash the ESP32-S3*
>
> *Some sources of Thonny (such as with certain built-in package managers) can result in strange issues with permissions or missing dependencies. If you encounter an issue with thonny when setting it up, and there is no other clear solution to your problem, it might be a good idea to try installing from another source.*

<br /> 
<br />
<br />


## Flash MicroHydra

Now you can download and install MicroHydra.  
To get the apropriate firmware for your device, you should head to the "Releases" section of the GitHub page, look for a `DEVICENAME.bin` file, and download it.

<p>
  <img src="misc\images\releases.png" height="300" hspace="10"/><img src="misc\images\releasebin.png" height="300" hspace="20"/>
</p>

Open Thonny, click this button in the bottom right, and click "Configure interpreter":   
<p>
  <img src="misc\images\thonnyhamburgermenu.png" height="300" hspace="10"/><img src="misc\images\thonnyconfigureinterpreter.png" height="300" hspace="10"/>
</p>

<br />

It should open this menu:   
<img src="misc\images\thonnyinterpreteroptions.png" width="500"/>


<br />

click "install or update micropython", and you should see another window:   
<p>
  <img src="misc\images\thonnyinstallmicropython.png" height="300" hspace="10"/><img src="misc\images\thonnyinstallmicropythonwindow.png" height="300" hspace="10"/>
</p>

<br />
<br />




Now you need to put your device into bootloader mode, and connect it to your computer. To do this, simply hold the `G0` button as you connect it to your PC.

<img src="misc\images\cardputerg0.jpg" width="200"/>

> *You can also hold `G0` and tap the reset button to get to bootloader mode.*  
> *If you are using a device like the TDeck, which doesn't power on when plugged in, you must hold `g0` and then flip the power switch on.*


<br />
<br />

Next we will select the firmware .bin file we downloaded.  
Click the little menu button and click `Select local MicroPython image ...`  
<img src="misc\images\thonnylocalmicropython.png" width="400"/>  
Navigate to the .bin file you downloaded, and select it.  
Make sure you also select your device in the "Target port" dropdown (it should have a name like "USB JTAG").

Your window should look something like this:  
<img src="misc\images\thonnyflashbin.png" width="400"/>  

Click "Install", and let it do its thing!

> *If installing didn't start, check that the correct device is selected, and it's in bootloader mode.*   

Once it's flashed, you can test it out by disconnecting it, and powering it on. If everything is working, you should see the main launcher open up!

If you have any issues, feel free to reach out. MH is still growing, and I'm interested to hear of any trouble it might be giving you. 

----

<br />
<br />
<br />


<img src="https://github.com/echo-lalia/Cardputer-MicroHydra/assets/108598670/a0782c5d-5633-489a-a5eb-f6b4e83803ef" alt="Demo GIF"/>
