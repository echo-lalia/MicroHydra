
import time, os, math, ntptime, network, framebuf
from lib import keyboard, beeper, battlevel
import machine
from launcher import st7789hybrid as st7789
from launcher.icons import icons, battery
from font import vga1_8x16 as fontsmall
from font import vga2_16x32 as font
from lib.mhconfig import Config

#bump up our clock speed so the UI feels smoother (240mhz is the max officially supported, but the default is 160mhz)
machine.freq(240_000_000)

"""

VERSION: 0.11

CHANGES:
    Overhaul launcher.py! (FINALLY)
    
    
This program is designed to be used in conjunction with "main.py" apploader, to select and launch MPy apps.

The basic app loading logic works like this:
 - apploader reads reset cause and RTC.memory to determine which app to launch
 - apploader launches 'launcher.py' when hard reset, or when RTC.memory is blank
 - launcher scans app directories on flash and SDCard to find apps
 - launcher shows list of apps, allows user to select one
 - launcher stores path to app in RTC.memory, and soft-resets the device
 - apploader reads RTC.memory to find path of app to load
 - apploader clears the RTC.memory, and imports app at the given path
 - app at given path now has control of device.
 - pressing the reset button will relaunch the launcher program, and so will calling machine.reset() from the app. 

This approach was chosen to reduce the chance of conflicts or memory errors when switching apps.
Because MicroPython completely resets between apps, the only "wasted" ram from the app switching process will be from main.py

"""


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_ICON_Y = const(36)
_APPNAME_Y = const(80)


_DISPLAY_WIDTH = const(240)
_DISPLAY_HEIGHT = const(135)

_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH//2)

_FONT_WIDTH = const(16)
_FONT_HEIGHT = const(32)
_SMALLFONT_WIDTH = const(8)
_SMALLFONT_HEIGHT = const(16)

_ICON_HEIGHT = const(32)
_ICON_WIDTH = const(32)

_ICON_FBUF_WIDTH = const(_FONT_WIDTH*3) # wide enough to fit the word "off"

_SCROLL_ANIMATION_TIME = const(400)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#wifi loves to give unknown runtime errors, just try it twice:
try:
    NIC = network.WLAN(network.STA_IF)
except RuntimeError as e:
    print(e)
    try:
        NIC = network.WLAN(network.STA_IF)
    except RuntimeError as e:
        NIC = None
        print("Wifi WLAN object couldnt be created. Gave this error:",e)
        import micropython
        print(micropython.mem_info())

#init driver for the graphics
DISPLAY = st7789.ST7789(
    machine.SPI(1, baudrate=40000000, sck=machine.Pin(36), mosi=machine.Pin(35), miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789.BGR
    )
DISPLAY.vscrdef(20,240,40)

NAME_FBUF = framebuf.FrameBuffer(
    bytearray(_FONT_HEIGHT * _DISPLAY_WIDTH * 2),
    _DISPLAY_WIDTH, _FONT_HEIGHT, framebuf.RGB565,
    )
ICON_FBUF = framebuf.FrameBuffer(
    bytearray(_ICON_HEIGHT * _ICON_FBUF_WIDTH * 2),
    _ICON_FBUF_WIDTH, _ICON_HEIGHT, framebuf.RGB565,
    )

BEEP = beeper.Beeper()
CONFIG = Config()
KB = keyboard.KeyBoard()
SD = None
RTC = machine.RTC()
BATT = battlevel.Battery()

SYNC_NTP_ATTEMPTS = 0
CONNECT_WIFI_ATTEMPTS = 0
SYNCING_CLOCK = None

APP_NAMES = None
APP_PATHS = None
APP_SELECTOR_INDEX = 0
PREV_SELECTOR_INDEX = 0
LASTDRAWN_MINUTE = -1

SCROLL_START_MS = 0
SCROLL_DIRECTION = 0
IS_SCROLLING = True
ICON_UPDATED = False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Finding Apps ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def scan_apps():
    global SD, APP_NAMES, APP_PATHS
    # first we need a list of apps located on the flash or SDCard

    main_directory = os.listdir("/")
    
    # if the sd card is not mounted, we need to mount it.
    if "sd" not in main_directory:
        try:
            SD = machine.SDCard(slot=2, sck=machine.Pin(40), miso=machine.Pin(39), mosi=machine.Pin(14), cs=machine.Pin(12))
        except OSError as e:
            print(e)
            print("SDCard couldn't be initialized. This might be because it was already initialized and not properly deinitialized.")
            try:
                SD.deinit()
            except:
                print("Couldn't deinitialize SDCard")
                
        try:
            os.mount(SD, '/sd')
        except (OSError, NameError, AttributeError) as e:
            print(e)
            print("Could not mount SDCard.")
            
        main_directory = os.listdir("/")

    sd_directory = []
    if "sd" in main_directory:
        sd_directory = os.listdir("/sd")

    # if the apps folder does not exist, create it.
    if "apps" not in main_directory:
        os.mkdir("/apps")
        main_directory = os.listdir("/")
        
    # do the same for the sdcard apps directory
    if "apps" not in sd_directory and "sd" in main_directory:
        os.mkdir("/sd/apps")
        sd_directory = os.listdir("/sd")



    # if everything above worked, sdcard should be mounted (if available), and both app directories should exist. now look inside to find our apps:
    main_app_list = list(os.ilistdir("/apps"))
    sd_app_list = []

    if "sd" in main_directory:
        try:
            sd_app_list = list(os.ilistdir("/sd/apps"))
        except OSError as e:
            print(e)
            print("SDCard mounted but cant be opened; assuming it's been removed. Unmounting /sd.")
            os.umount('/sd')


    
    # now lets collect some separate app names and locations
    app_names = []
    app_paths = {}
    
    for entry in main_app_list:
        this_name, this_path = get_app_paths(entry, "/apps/")
        if this_name:
            
            if this_name not in app_names:
                app_names.append(this_name)
                
            app_paths[this_name] = this_path
        
    for entry in sd_app_list:
        this_name, this_path = get_app_paths(entry, "/sd/apps/")
        if this_name:
            
            if this_name not in app_names:
                app_names.append(this_name)
                
            app_paths[this_name] = this_path
            
            
    #sort alphabetically without uppercase/lowercase discrimination:
    app_names.sort(key=lambda element: element.lower())
    
    #add an appname for builtin file browser
    app_names.append("Files")
    app_paths["Files"] = "/launcher/files.py"
    #add an appname to refresh the app list
    app_names.append("Reload Apps")
    #add an appname to control the beeps
    app_names.append("UI Sound")
    #add an appname to open settings app
    app_names.append("Settings")
    app_paths["Settings"] = "/launcher/settings.py"
    

    APP_NAMES = app_names
    APP_PATHS = app_paths


def get_app_paths(ientry, current_dir):
    # process results of ilistdir to capture app paths. 
    _DIR_FLAG = const(16384)
    _FILE_FLAG = const(32768)
    
    entry = ientry[0]
    is_dir = (ientry[1] == _DIR_FLAG)
    
    app_name = None
    app_path = None
    
    if entry.endswith(".py"):
        app_name = entry[:-3]
        app_path = current_dir + app_name
    elif entry.endswith(".mpy"):
        app_name = entry[:-4]
        app_path = current_dir + app_name
        
    elif is_dir:
        # check for apps as module folders
        dir_content = os.listdir(current_dir + entry)
        if "__init__.py" in dir_content or "__init__.mpy" in dir_content:
            app_name = entry
            app_path = current_dir + entry
    
    return app_name, app_path


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def launch_app(app_path):
    RTC.memory(app_path)
    print(f"Launching '{app_path}...'")
    # reset clock speed to default. 
    machine.freq(160_000_000)
    time.sleep_ms(10)
    machine.reset()


def center_text_x(text, char_width = 16):
    """
        Calculate the x coordinate to draw a text string, to make it horizontally centered. (plus the text width)
    """
    str_width = len(text) * char_width
    # display is 240 px wide
    start_coord = 120 - (str_width // 2)
    
    return start_coord

def ease_out_cubic(x):
    return 1 - ((1 - x) ** 3)
        
def time_24_to_12(hour_24,minute):
    ampm = 'am'
    if hour_24 >= 12:
        ampm = 'pm'
        
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
        
    time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
    return time_string, ampm

def play_sound(notes,time_ms=40):
    if CONFIG['ui_sound']:
        BEEP.play(notes,time_ms,CONFIG['volume'])


def draw_statusbar(t=None):
    global LASTDRAWN_MINUTE
    
    _STATUSBAR_HEIGHT = const(18)
    _CLOCK_X = const(6)
    _CLOCK_Y = const(2)
    _CLOCK_AMPM_PADDING = const(2)
    _CLOCK_AMPM_Y = const(1)
    
    _BATTERY_X = const(_DISPLAY_WIDTH - 28)
    _BATTERY_Y = const(4)
    
    _CLOCK_AMPM_X_OFFSET = const(_CLOCK_AMPM_PADDING+_CLOCK_X)
    _CLOCK_ERASE_WIDTH = const((_SMALLFONT_WIDTH*7)+_CLOCK_AMPM_PADDING)
    
    
    # erase clock
    DISPLAY.fill_rect(_CLOCK_X,_CLOCK_Y,_CLOCK_ERASE_WIDTH, _SMALLFONT_HEIGHT, CONFIG.palette[2])
    
    #clock
    _,_,_, hour_24, minute, _,_,_ = time.localtime()
    formatted_time, ampm = time_24_to_12(hour_24, minute)
    
    DISPLAY.text(
        fontsmall, formatted_time,
        _CLOCK_X,_CLOCK_Y,
        CONFIG.palette[4], CONFIG.palette[2])
    
    DISPLAY.text(
        fontsmall, ampm,
        _CLOCK_AMPM_X_OFFSET + (len(formatted_time) * _SMALLFONT_WIDTH), _CLOCK_AMPM_Y,
        CONFIG.palette[3], CONFIG.palette[2])
    
    LASTDRAWN_MINUTE = minute
    
    #battery
    batt_lvl = BATT.read_level()
    if batt_lvl == 3:
        DISPLAY.bitmap_icons(battery, battery.FULL, (CONFIG.palette[2],CONFIG.palette[4]),_BATTERY_X, _BATTERY_Y)
    elif batt_lvl == 2:
        DISPLAY.bitmap_icons(battery, battery.HIGH, (CONFIG.palette[2],CONFIG.palette[4]),_BATTERY_X, _BATTERY_Y)
    elif batt_lvl == 1:
        DISPLAY.bitmap_icons(battery, battery.LOW, (CONFIG.palette[2],CONFIG.palette[4]),_BATTERY_X, _BATTERY_Y)
    else:
        DISPLAY.bitmap_icons(battery, battery.EMPTY, (CONFIG.palette[2],CONFIG.rgb_colors[0]),_BATTERY_X, _BATTERY_Y)
    
    
def draw_scrollbar():
    _MIN_SCROLLBAR_WIDTH = const(20)
    _SCROLLBAR_HEIGHT = const(3)
    _SCROLLBAR_PADDING = const(5)
    
    _SCROLLBAR_FILL_HEIGHT = const(_SCROLLBAR_HEIGHT-1)
    _SCROLLBAR_Y = const(_DISPLAY_HEIGHT-_SCROLLBAR_HEIGHT)
    _SCROLLBAR_FILL_Y = const(_SCROLLBAR_Y+1)
    _SCROLLBAR_FULL_WIDTH = const(_DISPLAY_WIDTH-(_SCROLLBAR_PADDING*2))
    
    scrollbar_width = max(_SCROLLBAR_FULL_WIDTH // len(APP_NAMES), _MIN_SCROLLBAR_WIDTH)
    scrollbar_x = (
        ((_SCROLLBAR_FULL_WIDTH // len(APP_NAMES))
        * APP_SELECTOR_INDEX)
        + _SCROLLBAR_PADDING
        )

    
    # blackout:
    DISPLAY.fill_rect(_SCROLLBAR_PADDING, _SCROLLBAR_Y, _SCROLLBAR_FULL_WIDTH, _SCROLLBAR_HEIGHT, CONFIG.palette[1])
    
    # draw fill:
    DISPLAY.fill_rect(
        scrollbar_x, _SCROLLBAR_FILL_Y,
        scrollbar_width, _SCROLLBAR_FILL_HEIGHT,
        CONFIG.palette[2])
    
    # draw highlight:
    DISPLAY.hline(
        scrollbar_x, _SCROLLBAR_Y, scrollbar_width, CONFIG.palette[3])
    
def draw_app_selector():
    global ICON_UPDATED, IS_SCROLLING
    
    _BLIT_NAME_WIDTH = const(_DISPLAY_WIDTH-1) # TODO: trim this down
    _BLIT_NAME_Y_END = const(_APPNAME_Y+_FONT_HEIGHT-1)
    
    _BLIT_ICON_X_START = const((_DISPLAY_WIDTH // 2) - (_ICON_FBUF_WIDTH // 2))
    _BLIT_ICON_SECOND_X = const(_BLIT_ICON_X_START-_DISPLAY_WIDTH)
    _BLIT_ICON_X_END = const(_BLIT_ICON_X_START + _ICON_FBUF_WIDTH)
    _BLIT_ICON_Y_END = const(_ICON_Y + _ICON_HEIGHT)
    
    if not IS_SCROLLING:
        time.sleep_ms(5)
        return
    
    _TOTAL_SELECTOR_HEIGHT = const((_APPNAME_Y + _FONT_HEIGHT) - _ICON_Y)
    
    x = animate_scroll()
    
    draw_name_fbuf(x)
    
    if not ICON_UPDATED and abs(x) > _DISPLAY_WIDTH_HALF:
        draw_icon_fbuf()
        ICON_UPDATED = True
    
    if x == 0:
        DISPLAY.blit_buffer(ICON_FBUF, _BLIT_ICON_X_START, _ICON_Y, _ICON_FBUF_WIDTH, _ICON_HEIGHT)
        
    else:
        # calc icon position first so we can erase around it
        icon_x2 = _BLIT_ICON_X_START+x
        
        icon_x = icon_x2+_DISPLAY_WIDTH if SCROLL_DIRECTION > 0 else icon_x2-_DISPLAY_WIDTH
        icon_end_x = icon_x + _ICON_FBUF_WIDTH
        
        # erase to left of icon
        if icon_x > 0:
            DISPLAY.fill_rect(0, _ICON_Y, icon_x, _ICON_HEIGHT, CONFIG.palette[1])
        # erase to right of icon
        if icon_end_x < _DISPLAY_WIDTH:
            DISPLAY.fill_rect(icon_end_x, _ICON_Y, _DISPLAY_WIDTH - icon_end_x, _ICON_HEIGHT+1, CONFIG.palette[1])
        
        DISPLAY.blit_buffer(ICON_FBUF, icon_x2, _ICON_Y, _ICON_FBUF_WIDTH, _ICON_HEIGHT)
        
        # draw second/dissapearing icon
        DISPLAY.blit_buffer(
            ICON_FBUF,
            icon_x,
            _ICON_Y,
            _ICON_FBUF_WIDTH, _ICON_HEIGHT)
        
    # finally, draw app name(s)
    DISPLAY.blit_buffer(NAME_FBUF, 0, _APPNAME_Y, _DISPLAY_WIDTH, _FONT_HEIGHT)
    
    
    
def start_scroll(direct=1):
    global SCROLL_DIRECTION, SCROLL_START_MS, IS_SCROLLING, ICON_UPDATED
    SCROLL_DIRECTION = direct
    SCROLL_START_MS = time.ticks_ms()
    IS_SCROLLING = True
    ICON_UPDATED = False
    
def animate_scroll() -> int:
    global IS_SCROLLING
    
    if not IS_SCROLLING:
        return 0
    
    fac = time.ticks_diff(time.ticks_ms(), SCROLL_START_MS) / _SCROLL_ANIMATION_TIME
    if fac >= 1:
        IS_SCROLLING = False
        return 0
    
    fac = ease_out_cubic(fac)
    
    return math.floor(
        fac * _DISPLAY_WIDTH if SCROLL_DIRECTION < 0 else fac * -_DISPLAY_WIDTH
        )
    
    
    
def draw_icon_fbuf():
    
    _ICON_CENTERED_X = const((_ICON_FBUF_WIDTH - _ICON_WIDTH) // 2)
    _ICON_ONECHAR_X = const((_ICON_FBUF_WIDTH//2) - (_FONT_WIDTH // 2))
    
    current_app_text = APP_NAMES[APP_SELECTOR_INDEX]
    
    #blackout old icon
    DISPLAY.fill(CONFIG.palette[1], fbuf=ICON_FBUF)
    
    #special menu options for settings
    if current_app_text == "UI Sound":
        if CONFIG['ui_sound']:
            DISPLAY.fbuf_bitmap_text(
                font, ICON_FBUF, "On",
                _ICON_CENTERED_X, 0,
                CONFIG.palette[5])
        else:
            DISPLAY.fbuf_bitmap_text(
                font, ICON_FBUF, "Off",
                0, 0,
                CONFIG.palette[3])
            
    elif current_app_text == "Files":
        # Reusing the sd icon for files to save ram. This feels very inelegant, but it works for now.
        # I'd like to redo all of this at some point. 
        DISPLAY.bitmap_icons(icons, icons.SDCARD, (CONFIG['bg_color'],CONFIG.palette[5]),_ICON_CENTERED_X, 0, fbuf=ICON_FBUF)
        ICON_FBUF.rect(7, 2, 20, 6, CONFIG.palette[5], True)
        ICON_FBUF.rect(2, 15, 4, 6, CONFIG.palette[5], True)
        DISPLAY.fbuf_bitmap_text(font, ICON_FBUF, "/", _ICON_ONECHAR_X, 40, CONFIG.palette[1])
        ICON_FBUF.rect(7, 33, 16, 4,CONFIG.palette[1], True)
        ICON_FBUF.vline(6, 25, 6, CONFIG.palette[5])
            
    elif current_app_text == "Reload Apps":
        DISPLAY.bitmap_icons(icons, icons.RELOAD, (CONFIG['bg_color'],CONFIG['ui_color']),_ICON_CENTERED_X, 0, fbuf=ICON_FBUF)
        
    elif current_app_text == "Settings":
        DISPLAY.bitmap_icons(icons, icons.GEAR, (CONFIG['bg_color'],CONFIG['ui_color']),_ICON_CENTERED_X, 0, fbuf=ICON_FBUF)
        
    elif APP_PATHS[APP_NAMES[APP_SELECTOR_INDEX]][:3] == "/sd":
        DISPLAY.bitmap_icons(icons, icons.SDCARD, (CONFIG['bg_color'],CONFIG['ui_color']),_ICON_CENTERED_X, 0, fbuf=ICON_FBUF)
    else:
        DISPLAY.bitmap_icons(icons, icons.FLASH, (CONFIG['bg_color'],CONFIG['ui_color']),_ICON_CENTERED_X, 0, fbuf=ICON_FBUF)
    
def draw_name_fbuf(x=0):
    current_app_text = APP_NAMES[APP_SELECTOR_INDEX]
    
    #crop text for display
    if len(current_app_text) > 15:
        current_app_text = current_app_text[:12] + "..."
    
    #blackout the old text
    DISPLAY.fill(CONFIG['bg_color'], fbuf=NAME_FBUF)

    #draw new text
    if x:
        prev_app_text = APP_NAMES[PREV_SELECTOR_INDEX]
        
        DISPLAY.fbuf_bitmap_text(
            font, NAME_FBUF, prev_app_text,
            center_text_x(prev_app_text)+x, 0,
            CONFIG['ui_color'])
        
        DISPLAY.fbuf_bitmap_text(
            font, NAME_FBUF, current_app_text,
            _DISPLAY_WIDTH+center_text_x(current_app_text)+x if SCROLL_DIRECTION > 0 else -_DISPLAY_WIDTH+center_text_x(current_app_text)+x,
            #center_text_x(current_app_text)+x,
            0,
            CONFIG['ui_color'])
    else:
        DISPLAY.fbuf_bitmap_text(
            font, NAME_FBUF, current_app_text,
            center_text_x(current_app_text)+x, 0,
            CONFIG['ui_color'])

def try_sync_clock():
    global SYNCING_CLOCK, RTC, SYNC_NTP_ATTEMPTS, CONNECT_WIFI_ATTEMPTS
    
    _MAX_WIFI_ATTEMPTS = const(1000)
    _MAX_NTP_ATTEMPTS = const(10)

    if NIC.isconnected():
        try:
            ntptime.settime()
        except OSError:
            SYNC_NTP_ATTEMPTS += 1
            
        if RTC.datetime()[0] != 2000:
            NIC.disconnect()
            NIC.active(False) #shut off wifi
            SYNCING_CLOCK = False
            #apply our timezone offset
            time_list = list(RTC.datetime())
            time_list[4] = time_list[4] + CONFIG['timezone']
            RTC.datetime(tuple(time_list))
            print(f'RTC successfully synced to {RTC.datetime()} with {SYNC_NTP_ATTEMPTS} attempts.')
            draw_statusbar()
            
        elif SYNC_NTP_ATTEMPTS >= _MAX_NTP_ATTEMPTS:
            NIC.disconnect()
            NIC.active(False) #shut off wifi
            SYNCING_CLOCK = False
            print(f"Syncing RTC aborted after {SYNC_NTP_ATTEMPTS} attemps")
        
    elif CONNECT_WIFI_ATTEMPTS >= _MAX_WIFI_ATTEMPTS:
        NIC.disconnect()
        NIC.active(False) #shut off wifi
        SYNCING_CLOCK = False
        print(f"Connecting to wifi aborted after {CONNECT_WIFI_ATTEMPTS} loops")
    else:
        CONNECT_WIFI_ATTEMPTS += 1

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#--------------------------------------------------------------------------------------------------


def main_loop():
    global APP_SELECTOR_INDEX, PREV_SELECTOR_INDEX, SYNCING_CLOCK
    
    # scan apps asap to populate app names/paths and SD
    scan_apps()
        
    # sync our RTC on boot, if set in settings
    SYNCING_CLOCK = CONFIG['sync_clock']
        
    if (CONFIG['wifi_ssid'] == ''
        or RTC.datetime()[0] != 2000
        or NIC == None):
        SYNCING_CLOCK = False
        
    if SYNCING_CLOCK: #enable wifi if we are syncing the clock
        if not NIC.active(): # turn on wifi if it isn't already
            NIC.active(True)
        if not NIC.isconnected(): # try connecting
            try:
                NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
            except OSError as e:
                print("wifi_sync_rtc had this error when connecting:",e)
    
    new_keys = []
    
    
    #nonscroll_elements_displayed = False
    
    #force_redraw_display = True
    
    #this is used as a flag to tell a future loop to redraw the frame mid-scroll animation
    #elayed_redraw = False
    
    #scroll_direction = 0 #1 for right, -1 for left, 0 for center
    #refresh_timer = 0
    
    #starupp sound
    play_sound(
            ('C3',
            ('C4','E4','G4'),
            ('C4','E4','G4'),
            ))
        
    #init diplsay
    DISPLAY.fill(CONFIG['bg_color'])
    DISPLAY.fill_rect(0,0,_DISPLAY_WIDTH, _STATUSBAR_HEIGHT, CONFIG.palette[2])
    DISPLAY.hline(0,_STATUSBAR_HEIGHT,_DISPLAY_WIDTH,CONFIG.palette[0])
    
    draw_scrollbar()
    draw_statusbar()
    draw_icon_fbuf()
#     timer = machine.Timer(0)
#     timer.init(
#         mode = machine.Timer.PERIODIC,
#         period = 5000,
#         callback = draw_statusbar
#         )
    
    while True:
        
        
        # ----------------------- check for key presses on the keyboard. Only if they weren't already pressed. --------------------------
        new_keys = KB.get_new_keys()
        if new_keys:
            
            # ~~~~~~ check if the arrow keys are newly pressed ~~~~~
            if "/" in new_keys: # right arrow
                PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                APP_SELECTOR_INDEX = (APP_SELECTOR_INDEX + 1) % len(APP_NAMES)
                draw_scrollbar()
                
                #animation:
                start_scroll()
                
                play_sound((("D3",'F3'),"A3"), 20)

                
            elif "," in new_keys: # left arrow
                PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                APP_SELECTOR_INDEX = (APP_SELECTOR_INDEX - 1) % len(APP_NAMES)
                draw_scrollbar()
                
                #animation:
                start_scroll(-1)
                
                play_sound((("C3","E3"),"G3"), 20)
                
            
        
            # ~~~~~~~~~~ check if GO or ENTER are pressed ~~~~~~~~~~
            if "GO" in new_keys or "ENT" in new_keys:
                
                # special "settings" app options will have their own behaviour, otherwise launch the app
                if APP_NAMES[APP_SELECTOR_INDEX] == "UI Sound":
                    
                    if CONFIG['ui_sound'] == 0: # currently muted, then unmute
                        CONFIG['ui_sound'] = True
                        #force_redraw_display = True
                        play_sound(("C3","E3","G3",("C4","E4","G4"),("C4","E4","G4")), 80)
                        
                    else: # currently unmuted, then mute
                        CONFIG['ui_sound'] = False
                        #force_redraw_display = True
                
                elif APP_NAMES[APP_SELECTOR_INDEX] == "Reload Apps":
                    scan_apps()
                    APP_SELECTOR_INDEX = 0
                    play_sound(('C4','E4','G4'),80)
                        
                else: # ~~~~~~~~~~~~~~~~~~~ LAUNCH THE APP! ~~~~~~~~~~~~~~~~~~~~
                    
                    #save CONFIG if it has been changed:
                    CONFIG.save()
                        
                    # shut off the display
                    DISPLAY.fill(0)
                    DISPLAY.sleep_mode(True)
                    machine.Pin(38, machine.Pin.OUT).value(0) #backlight off
                    DISPLAY.spi.deinit()
                    
                    if sd != None:
                        try:
                            sd.deinit()
                        except:
                            print("Tried to deinit SDCard, but failed.")
                            
                    play_sound(('C4','B4','C5','C5'),100)
                        
                    launch_app(APP_PATHS[APP_NAMES[APP_SELECTOR_INDEX]])

            else: # keyboard shortcuts!
                for key in new_keys:
                    # jump to letter:
                    if len(key) == 1 and key in 'abcdefghijklmnopqrstuvwxyz1234567890': # filter special keys and repeated presses
                            #search for that letter in the app list
                            for idx in range(len(APP_NAMES)):
                                # this lets us scan starting at the current APP_SELECTOR_INDEX
                                idx = (idx + APP_SELECTOR_INDEX) % len(APP_NAMES)
                                name = APP_NAMES[idx]
                                if name.lower().startswith(key) and idx != APP_SELECTOR_INDEX:
                                    #animation:
                                    if APP_SELECTOR_INDEX > idx:
                                        start_scroll(-1)
                                    elif APP_SELECTOR_INDEX < idx:
                                        start_scroll(1)
                                    # go there!
                                    PREV_SELECTOR_INDEX = APP_SELECTOR_INDEX
                                    APP_SELECTOR_INDEX = idx
                                    play_sound(("G3"), 100)
                                    draw_scrollbar()
                                    break
    
        #time.sleep_ms(4) #this loop runs about 3000 times a second without sleeps. The sleeps actually help things feel smoother.
        
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Graphics: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        if time.localtime()[4] != LASTDRAWN_MINUTE:
            draw_statusbar()
            
        draw_app_selector()
        
        #reset vars for next loop
        #force_redraw_display = False
            
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ WIFI and RTC: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        if SYNCING_CLOCK:
            try_sync_clock()
        
# run the main loop!
main_loop()




