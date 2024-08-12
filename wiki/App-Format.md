### Format of MicroHydra apps:
MicroHydra apps can be placed in the apps folder on the device's main storage, or in the apps folder on an SD Card (The launcher will create these folders automatically if they don't exist.)

<br/>

All that is needed to make a valid MicroHydra app, is a .py file with some MicroPython code, placed in the apps folder. The file name becomes the app name, and it will be run by the app loader when launched by MicroHydra.   
This is the simplest form of a MH app, and several apps in the [apps](https://github.com/echo-lalia/MicroHydra-Apps) repo are designed like this. 

<br/>

Apps that are more complex can be made as a folder, instead. This can allow you to bundle in dependencies, or split the code up into multiple files for better readability. A MicroHydra app as a folder works essentially the same as a normal Python module, where a file named `__init__.py` inside that folder will be run at launch.

If you decide to format your app as a folder, you'll probably want to use 'relative' imports to access the other modules in the app folder.   
However, relative imports don't work when running from the editor. My usual solution to this is to use both relative, and absolute imports, in a try/except statement. Here's what that looks like:

``` Python
try:
    # relative import for launching the app normally
    from . import myothermodule
except:
    # absolute path for launching from the editor (which causes the above to fail)
    from apps.myappname import myothermodule
```

<br/><br/><br/>

### App Icons:
The MicroHydra launcher has very constrained memory.   
Because of this, the launcher uses compressed vector/polygon icon definitions to generate the icons on-the-fly, rather than using bitmap icons.   
The icons definitions are stored as strings, and then unpacked into arguments for the FrameBuffer.polygon method. 

I created [this](https://github.com/echo-lalia/polygon-tool/tree/main) tool to help with the creation of these icon definitions (and to help with plotting out other polygons for MicroPython). 

You can use it to draw out the shape the icon should be in, then hit the "pack" button to compress it down into a smaller string. That string (*without* quotes) can then be placed in an `__icon__.txt` file in the folder alongside `__init__.py`.

**Important note:** *Because the launcher must generate the icon on-the-fly as it comes into view, it's important that app icons not be too complex, otherwise there will be a noticeable lag when scrolling past your app.*

*I also do realize that this polygonal icon system is kind of a weird solution. I have an interest in adding support for custom bitmap icons for apps in the future, if possible. But for now, this is a decently fast, low-memory solution to the problem.*