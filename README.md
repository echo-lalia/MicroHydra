# Cardputer-MicroHydra
MicroHydra is a simple MicroPython based app launcher designed for the M5Stack Cardputer.

This program is still in early development, but it seems to be working so far. 
This code was built with MicroPython v1.22.1, for a Generic ESP32-S3 controller.

The main function of MicroHydra is to provide an interface to easily switch between MicroPython apps.   
Python scripts can be placed in the /apps folder on the flash, or in a /apps folder on a micro sd card. The launcher scans these two locations on startup. 

# how it works:

This program can be thought of as two main components; the launcher and the apploader.   
The apploader is the "main.py" file in the root directory, and it's the first thing to run when the device is powered on.   
The apploader reads the RTC memory to determine if it should load an app, otherwise, it loads the launcher.

The launcher is the main UI for the app switching functionality. Its primary responsibility is choosing an app, then storing it's path in the RTC.memory. 
Once the app path is in the memory, it calls machine.reset() to refresh the system and return to the apploader, after which the apploader loads the target app. 

This approach was chosen to help to prevent issues with memory managment or import conflicts between apps. Resetting the entire device means that the only thing thing loaded before the custom app, is the lightweight apploader.

