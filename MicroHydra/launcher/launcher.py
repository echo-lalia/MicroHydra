from machine import Pin, SDCard, SPI, RTC
import time, os, json
from lib import keyboard, beeper
import machine
from lib import st7789py as st7789
from launcher.icons import icons
from font import vga1_8x16 as fontsmall
from font import vga2_16x32 as font


"""

VERSION: 0.1


This program is designed to be used in conjunction with the "apploader.py" program, to select and launch MPy apps for the Cardputer.

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
Because MicroPython completely resets between apps, the only "wasted" ram from the app switching process will be from launcher.py



"""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

black = const(0)
white = const(65535)
default_ui_color = const(53243)
default_bg_color = const(4421)
default_ui_sound = const(True)
default_volume = const(2)

appname_y = const(80)
target_vscsad = const(40)  # scrolling display "center"

display_width = const(240)
display_height = const(135)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Launching Second Thread ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Finding Apps ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def scan_apps():
    # first we need a list of apps located on the flash or SDCard

    main_directory = os.listdir("/")

    # if the sd card is not mounted, we need to mount it.
    if "sd" not in main_directory:
        sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))

        try:
            os.mount(sd, "/sd")
        except OSError:
            print("Could not mount SDCard!")

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
    main_app_list = os.listdir("/apps")
    sd_app_list = []

    if "sd" in main_directory:
        sd_app_list = os.listdir("/sd/apps")

    # now lets collect some separate app names and locations
    app_names = []
    app_paths = {}

    for entry in main_app_list:
        # .py and .mpy support
        if entry.endswith(".py") or entry.endswith(".mpy"):
            this_name = entry[:-3]

            # the purpose of this check is to prevent dealing with duplicated apps.
            # if multiple apps share the same name, then we will simply use the app found most recently.
            if this_name not in app_names:
                app_names.append(this_name)  # for pretty display

            app_paths[f"{this_name}"] = f"/apps/{entry}"

    for entry in sd_app_list:
        # .py and .mpy support
        if entry.endswith(".py") or entry.endswith(".mpy"):
            this_name = entry[:-3]

            if this_name not in app_names:
                app_names.append(this_name)

            app_paths[f"{this_name}"] = f"/sd/apps/{entry}"

    app_names.sort()

    # add an appname to control the beeps
    app_names.append("UI Sound")
    # add an appname to refresh the app list
    app_names.append("Reload Apps")

    return app_names, app_paths


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def launch_app(app_path):
    # print(f'launching {app_path}')
    rtc = machine.RTC()
    rtc.memory(app_path)
    time.sleep_ms(10)


def center_text_x(text, char_width=16):
    """
    Calculate the x coordinate to draw a text string, to make it horizontally centered. (plus the text width)
    """
    str_width = len(text) * char_width
    # display is 240 px wide
    start_coord = 120 - (str_width // 2)

    return start_coord, str_width


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# --------------------------------------------------------------------------------------------------


def main_loop():

    # bump up our clock speed so the UI feels smoother (240mhz is the max officially supported, but the default is 160mhz)
    machine.freq(240_000_000)

    # before anything else, we should scan for apps
    app_names, app_paths = scan_apps()
    app_selector_index = 0
    prev_selector_index = 0

    # init the keyboard
    kb = keyboard.KeyBoard()
    pressed_keys = []
    prev_pressed_keys = []

    # init driver for the graphics
    spi = SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None)
    tft = st7789.ST7789(
        spi,
        display_height,
        display_width,
        reset=Pin(33, Pin.OUT),
        cs=Pin(37, Pin.OUT),
        dc=Pin(34, Pin.OUT),
        backlight=Pin(38, Pin.OUT),
        rotation=1,
        color_order=st7789.BGR,
    )

    tft.vscrdef(40, display_width, 40)
    tft.vscsad(target_vscsad)

    # variables:
    config_modified = False
    # load config
    try:
        with open("config.json", "r") as conf:
            config = json.loads(conf.read())
            ui_color = config["ui_color"]
            bg_color = config["bg_color"]
            ui_sound = config["ui_sound"]
            volume = config["volume"]
    except:
        print("could not load settings from config.json. reloading default values.")
        config_modified = True
        ui_color = default_ui_color
        bg_color = default_bg_color
        ui_sound = default_ui_sound
        volume = default_volume

    force_redraw_display = True

    launching = False
    current_vscsad = 40

    # init the beeper!
    beep = beeper.Beeper()

    # starupp sound
    if ui_sound:
        beep.play("C4 D4 D4", 0.12, volume)
    # init diplsay
    tft.fill_rect(-40, 0, 280, display_height, bg_color)

    while True:

        # ----------------------- check for key presses on the keyboard. Only if they weren't already pressed. --------------------------
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:

            # ~~~~~~ check if the arrow keys are newly pressed ~~~~~
            if "/" in pressed_keys and "/" not in prev_pressed_keys:  # right arrow
                app_selector_index += 1

                # animation:
                current_vscsad -= 40
                tft.vscsad(80)
                if current_vscsad < 0:
                    current_vscsad = 0

                if ui_sound:
                    beep.play("D6 C5", 0.1, volume)

            elif "," in pressed_keys and "," not in prev_pressed_keys:  # left arrow
                app_selector_index -= 1

                current_vscsad += 40
                tft.vscsad(0)
                if current_vscsad > 80:
                    current_vscsad = 80

                if ui_sound:
                    beep.play("D6 C5", 0.1, volume)

            # ~~~~~~~~~~ check if GO or ENTER are pressed ~~~~~~~~~~
            if "GO" in pressed_keys or "ENT" in pressed_keys:

                # special "settings" app options will have their own behaviour, otherwise launch the app
                if app_names[app_selector_index] == "UI Sound":

                    if ui_sound == 0:  # currently muted, then unmute
                        nvs.set_i32("sound", 1)
                        ui_sound = True
                        force_redraw_display = True
                        beep.play("C4 G4 G4", 0.2, volume)
                        config_modified = True
                    else:  # currently unmuted, then mute
                        nvs.set_i32("sound", 0)
                        ui_sound = False
                        force_redraw_display = True
                        config_modified = True

                elif app_names[app_selector_index] == "Reload Apps":
                    app_names, app_paths = scan_apps()
                    app_selector_index = 0
                    if ui_sound:
                        beep.play("D4 C4 D4", 0.08, volume)

                else:  # ~~~~~~~~~~~~~~~~~~~ LAUNCH THE APP! ~~~~~~~~~~~~~~~~~~~~

                    # save config if it has been changed:
                    if config_modified:
                        with open("config.json", "w") as conf:
                            config = {
                                "ui_color": ui_color,
                                "bg_color": bg_color,
                                "ui_sound": ui_sound,
                                "volume": volume,
                            }
                            conf.write(json.dumps(config))

                    # shut off the display
                    tft.fill(black)
                    tft.sleep_mode(True)
                    Pin(38, Pin.OUT).value(0)  # backlight off
                    spi.deinit()

                    if ui_sound:
                        beep.play("C4 B4 C5 C5", 0.14, volume)

                    launch_app(app_paths[app_names[app_selector_index]])

            # once we parse the keypresses for this loop, we need to store them for next loop
            prev_pressed_keys = pressed_keys

        # wrap around our selector index, in case we go over or under the target amount
        app_selector_index = app_selector_index % len(app_names)

        time.sleep_ms(
            10
        )  # this loop runs about 3000 times a second without sleeps. The sleeps actually help things feel smoother.

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Graphics: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # decide now if we will be redrawing the text.
        # we are capturing this so that we can black out and redraw the screen in two parts
        redraw = (app_selector_index != prev_selector_index) or force_redraw_display

        prev_app_text = app_names[prev_selector_index]
        current_app_text = app_names[app_selector_index]

        if redraw:  # blackout that text
            time.sleep_ms(1)
            if len(prev_app_text) > 15:
                prev_app_text = prev_app_text[:12] + "..."
            if len(current_app_text) > 15:
                current_app_text = current_app_text[:12] + "..."

            # blackout the old text
            prev_txt_start, prev_txt_width = center_text_x(prev_app_text)
            tft.fill_rect(prev_txt_start, 50, prev_txt_width, appname_y, bg_color)
            tft.fill_rect(96, 30, 48, 32, bg_color)
            time.sleep_ms(1)

        # if vscsad/scrolling is not centered, move it toward center!
        if current_vscsad != target_vscsad:
            tft.vscsad(current_vscsad)
            if current_vscsad < target_vscsad:
                current_vscsad += 1 + (abs(current_vscsad - target_vscsad) // 8)
            elif current_vscsad > target_vscsad:
                current_vscsad -= 1 + (abs(current_vscsad - target_vscsad) // 8)

        # only update the text on the display when we need to!
        if redraw:

            # draw new text
            tft.text(
                font,
                current_app_text,
                center_text_x(current_app_text)[0],
                appname_y,
                ui_color,
                bg_color,
            )

            # special menu options for settings
            if current_app_text == "UI Sound":
                if ui_sound:
                    tft.text(font, "On", center_text_x("On")[0], 30, white, bg_color)
                else:
                    tft.text(font, "Off", center_text_x("Off")[0], 30, white, bg_color)
            elif current_app_text == "Reload Apps":
                tft.bitmap_icons(icons, icons.RELOAD, (bg_color, ui_color), 104, 30)
            elif app_paths[app_names[app_selector_index]][:3] == "/sd":
                tft.bitmap_icons(icons, icons.SDCARD, (bg_color, ui_color), 104, 30)
            else:
                tft.bitmap_icons(icons, icons.FLASH, (bg_color, ui_color), 104, 30)
            time.sleep_ms(10)

        # reset vars for next loop
        force_redraw_display = False

        # update prev app selector index to current one for next cycle
        prev_selector_index = app_selector_index


# run the main loop!
main_loop()
