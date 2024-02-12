from machine import Pin, SPI
import machine
import time, os, json, math
from lib import keyboard, beeper
from lib import st7789py as st7789
from lib import microhydra as mh
from font import vga2_16x32 as font
from font import vga1_8x16 as fontsmall






#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

black = const(0)
white = const(65535)
default_ui_color = const(53243)
default_bg_color = const(4421)
default_ui_sound = const(True)
default_volume = const(2)

display_width = const(240)
display_height = const(135)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Define Settings: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


setting_names = [
    'volume',
    'ui_color',
    'bg_color',
    'wifi_ssid',
    'wifi_pass',
    'sync_clock',
    'timezone',
    'confirm'
    ]


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Setting Picker Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_color(tft, font, kb, beep, setting_name, previous_color, ui_color, bg_color, ui_sound, volume): # ~~~~~~~~~~~~~~~~~~~~~~~ get_color ~~~~~~~~~~~~~~~~~~~~~~~~~
    
    r,g,b = mh.separate_color565(previous_color)
    
    # draw pop-up menu box
    tft.fill_rect(10,10,220,115,bg_color)
    tft.rect(9,9,222,117,ui_color)
    tft.hline(10,126,222,black)
    tft.hline(11,127,222,black)
    tft.hline(12,128,222,black)
    tft.hline(13,129,222,black)
    tft.vline(231,10,117,black)
    tft.vline(232,11,117,black)
    tft.vline(233,12,117,black)
    tft.vline(234,13,117,black)
    
    tft.text(font, setting_name, 120 - ((len(setting_name)* 16) // 2), 20, ui_color, bg_color)
    
    rgb_select_index = 0
    
    pressed_keys = []
    prev_pressed_keys = kb.get_pressed_keys()
    
    redraw = True
    
    up_hold_timer = 0
    down_hold_timer = 0
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys:
            if "," in pressed_keys and "," not in prev_pressed_keys: # left arrow
                rgb_select_index -= 1
                rgb_select_index %= 3
                if ui_sound:
                    beep.play(("C3","A3"), 80, volume)
                redraw = True

                refresh_display = True
            elif "/" in pressed_keys and "/" not in prev_pressed_keys: # right arrow
                rgb_select_index += 1
                if ui_sound:
                    beep.play(("C3","A3"), 80, volume)
                rgb_select_index %= 3
                redraw = True
            elif ";" in pressed_keys: # up arrow
                if ";" not in prev_pressed_keys: # newly pressed
                    if rgb_select_index == 0:
                        r += 1
                        r %= 32
                    elif rgb_select_index == 1:
                        g += 1
                        g %= 64
                    elif rgb_select_index == 2:
                        b += 1
                        b %= 32
                    if ui_sound:
                        beep.play("D4", 100, volume)
                    redraw = True
                    up_hold_timer = 0
                    
                else: # up button held
                    
                    up_hold_timer += 1
                    if up_hold_timer > 1000:
                        up_hold_timer = 800
                        if rgb_select_index == 0:
                            r += 1
                            r %= 32
                        elif rgb_select_index == 1:
                            g += 1
                            g %= 64
                        elif rgb_select_index == 2:
                            b += 1
                            b %= 32
                        if ui_sound:
                            beep.play("D4", 100, volume)
                        redraw = True
                        
                
            elif "." in pressed_keys: # down arrow
                if "." not in prev_pressed_keys:
                    if rgb_select_index == 0:
                        r -= 1
                        r %= 32
                    elif rgb_select_index == 1:
                        g -= 1
                        g %= 64
                    elif rgb_select_index == 2:
                        b -= 1
                        b %= 32
                    if ui_sound:
                        beep.play("D4", 100, volume)
                    redraw = True
                    down_hold_timer = 0
                    
                else:
                    down_hold_timer += 1
                    if down_hold_timer > 1000:
                        down_hold_timer = 800
                        if rgb_select_index == 0:
                            r -= 1
                            r %= 32
                        elif rgb_select_index == 1:
                            g -= 1
                            g %= 64
                        elif rgb_select_index == 2:
                            b -= 1
                            b %= 32
                        if ui_sound:
                            beep.play("D4", 100, volume)
                        redraw = True
                
                
                
            elif ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                if ui_sound:
                    beep.play(("C4","D4","E4"), 50, volume)
                return mh.combine_color565(r,g,b)
                
            

                    
        
        # graphics!
        
        if redraw:
            tft.fill_rect(62, 60, 128, 32, bg_color)
            
            #draw the numbers
            for idx, clr in enumerate((r,g,b)):
                if idx == rgb_select_index:
                    tft.text(font, str(clr), 62 + (44*idx), 60, white, black)
                else:
                    tft.text(font, str(clr), 62 + (44*idx), 60, ui_color, bg_color)
            
            # pointer!
            tft.fill_rect(62, 94, 120, 24, bg_color)
            for i in range(0,16):
                tft.hline(
                    x = (78 - i) + (42 * rgb_select_index),
                    y = 94 + i,
                    length = 2 + (i*2),
                    color = mh.combine_color565(r,g,b))
            tft.fill_rect(62 + (42 * rgb_select_index), 110, 34, 8, mh.combine_color565(r,g,b))

            
            
            redraw = False

        prev_pressed_keys = pressed_keys
            
            
            
            
            
def get_volume(tft, font, kb, beep, setting_name, previous_vol, ui_color, bg_color, ui_sound): # ~~~~~~~~~~~~~~~~~~~~~~~ get_volume ~~~~~~~~~~~~~~~~~~~~~~~~~
    
    current_value = previous_vol
    
    # draw pop-up menu box
    tft.fill_rect(10,10,220,115,bg_color)
    tft.rect(9,9,222,117,ui_color)
    tft.hline(10,126,222,black)
    tft.hline(11,127,222,black)
    tft.hline(12,128,222,black)
    tft.hline(13,129,222,black)
    tft.vline(231,10,117,black)
    tft.vline(232,11,117,black)
    tft.vline(233,12,117,black)
    tft.vline(234,13,117,black)
    
    # arrows
    for i in range(0,8):
        tft.hline(
            x = (119 - i),
            y = 60 + i,
            length = 2 + (i*2),
            color = ui_color)
        tft.hline(
            x = (119 - i),
            y = 116 - i,
            length = 2 + (i*2),
            color = ui_color)
    
    tft.text(font, setting_name, 120 - ((len(setting_name)* 16) // 2), 20, ui_color, bg_color)
    
    pressed_keys = []
    prev_pressed_keys = kb.get_pressed_keys()
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ";" in pressed_keys and ";" not in prev_pressed_keys: # up arrow
                current_value += 1
                current_value %= 11
                if ui_sound:
                    beep.play("D3", 140, current_value)
                redraw = True
            elif "." in pressed_keys and "." not in prev_pressed_keys: # down arrow
                current_value -= 1
                current_value %= 11
                if ui_sound:
                    beep.play("D3", 140, current_value)
                redraw = True
            elif ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                if ui_sound:
                    beep.play(("C4","D4","E4"), 50, current_value)
                return current_value
        
        # graphics!
        
        if redraw:
            tft.fill_rect(62, 75, 128, 32, bg_color)
            
            tft.text(font, str(current_value), 112 - ((current_value == 10) * 8), 75, ui_color, bg_color)

            
            
            redraw = False

        prev_pressed_keys = pressed_keys
        
        
        
def get_text(tft, font, kb, beep, setting_name, previous_value, ui_color, bg_color, ui_sound, volume): # ~~~~~~~~~~~~~~~~~~~~~~~ get_text ~~~~~~~~~~~~~~~~~~~~~~~~~
    
    current_value = previous_value
    
    # draw pop-up menu box
    tft.fill_rect(10,10,220,115,bg_color)
    tft.rect(9,9,222,117,ui_color)
    tft.hline(10,126,222,black)
    tft.hline(11,127,222,black)
    tft.hline(12,128,222,black)
    tft.hline(13,129,222,black)
    tft.vline(231,10,117,black)
    tft.vline(232,11,117,black)
    tft.vline(233,12,117,black)
    tft.vline(234,13,117,black)
    
    # arrows
    
    tft.text(font, setting_name, 120 - ((len(setting_name)* 16) // 2), 20, ui_color, bg_color)
    
    pressed_keys = []
    prev_pressed_keys = kb.get_pressed_keys()
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                if ui_sound:
                    beep.play(("C4","D4","E4"), 50, volume)
                return current_value
            
            elif 'BSPC' in pressed_keys and 'BSPC' not in prev_pressed_keys:
                current_value = current_value[0:-1]
                redraw = True
            elif 'SPC' in pressed_keys and 'SPC' not in prev_pressed_keys:
                current_value = current_value + ' '
                redraw = True
            else:
                for key in pressed_keys:
                    if len(key) == 1 and key not in prev_pressed_keys:
                        current_value += key
                    redraw = True
        
        # graphics!
        if redraw:
            tft.fill_rect(12, 59, 216, 64, bg_color)
            if len(current_value) <= 12:
                tft.text(font, current_value, 120 - (len(current_value) * 8), 75, ui_color, bg_color)
            else:
                tft.text(font, current_value[0:12], 24, 59, ui_color, bg_color)
                tft.text(font, current_value[12:], 120 - (len(current_value[12:]) * 8), 91, ui_color, bg_color)

            
            
            redraw = False

        prev_pressed_keys = pressed_keys
        
        
        
        
        
            
def get_bool(tft, font, kb, beep, setting_name, previous_val, ui_color, bg_color, ui_sound, volume): # ~~~~~~~~~~~~~~~~~~~~~~~ get_bool ~~~~~~~~~~~~~~~~~~~~~~~~~
    
    current_value = previous_val
    
    # draw pop-up menu box
    tft.fill_rect(10,10,220,115,bg_color)
    tft.rect(9,9,222,117,ui_color)
    tft.hline(10,126,222,black)
    tft.hline(11,127,222,black)
    tft.hline(12,128,222,black)
    tft.hline(13,129,222,black)
    tft.vline(231,10,117,black)
    tft.vline(232,11,117,black)
    tft.vline(233,12,117,black)
    tft.vline(234,13,117,black)
    
    # arrows
    for i in range(0,8):
        tft.hline(
            x = (119 - i),
            y = 60 + i,
            length = 2 + (i*2),
            color = ui_color)
        tft.hline(
            x = (119 - i),
            y = 116 - i,
            length = 2 + (i*2),
            color = ui_color)
    
    tft.text(font, setting_name, 120 - ((len(setting_name)* 16) // 2), 20, ui_color, bg_color)
    
    pressed_keys = []
    prev_pressed_keys = kb.get_pressed_keys()
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ";" in pressed_keys and ";" not in prev_pressed_keys: # up arrow
                current_value = not current_value
                if ui_sound:
                    beep.play("D3", 140, volume)
                redraw = True
            elif "." in pressed_keys and "." not in prev_pressed_keys: # down arrow
                current_value = not current_value
                if ui_sound:
                    beep.play("D3", 140, volume)
                redraw = True
            elif ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                if ui_sound:
                    beep.play(("C4","D4","E4"), 50, volume)
                return current_value
        
        # graphics!
        if redraw:
            tft.fill_rect(62, 75, 128, 32, bg_color)
            if current_value:
                tft.text(font, 'ON', 104, 75, ui_color, bg_color)
            else:
                tft.text(font, 'OFF', 96, 75, ui_color, bg_color)

            redraw = False

        prev_pressed_keys = pressed_keys
        

def get_int(tft, font, kb, beep, setting_name, previous_val, minimum, maximum, ui_color, bg_color, ui_sound, volume): # ~~~~~~~~~~~~~~~~~~~~~~~ get_int ~~~~~~~~~~~~~~~~~~~~~~~~~
    
    current_value = previous_val
    
    # draw pop-up menu box
    tft.fill_rect(10,10,220,115,bg_color)
    tft.rect(9,9,222,117,ui_color)
    tft.hline(10,126,222,black)
    tft.hline(11,127,222,black)
    tft.hline(12,128,222,black)
    tft.hline(13,129,222,black)
    tft.vline(231,10,117,black)
    tft.vline(232,11,117,black)
    tft.vline(233,12,117,black)
    tft.vline(234,13,117,black)
    
    # arrows
    for i in range(0,8):
        tft.hline(
            x = (119 - i),
            y = 60 + i,
            length = 2 + (i*2),
            color = ui_color)
        tft.hline(
            x = (119 - i),
            y = 116 - i,
            length = 2 + (i*2),
            color = ui_color)
    
    tft.text(font, setting_name, 120 - ((len(setting_name)* 16) // 2), 20, ui_color, bg_color)
    
    pressed_keys = []
    prev_pressed_keys = kb.get_pressed_keys()
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ";" in pressed_keys and ";" not in prev_pressed_keys: # up arrow
                current_value += 1
                if current_value > maximum:
                    current_value = minimum
                if ui_sound:
                    beep.play("D3", 140, volume)
                redraw = True
            elif "." in pressed_keys and "." not in prev_pressed_keys: # down arrow
                current_value -= 1
                if current_value < minimum:
                    current_value = maximum
                if ui_sound:
                    beep.play("D3", 140, volume)
                redraw = True
            elif ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                if ui_sound:
                    beep.play(("C4","D4","E4"), 50, volume)
                return current_value
        
        # graphics!
        if redraw:
            tft.fill_rect(62, 75, 128, 32, bg_color)
            tft.text(font, str(current_value), 120 - (len(str(current_value)) * 8), 75, ui_color, bg_color)

            redraw = False

        prev_pressed_keys = pressed_keys
        

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#--------------------------------------------------------------------------------------------------




def main_loop():
    
    #init the keyboard
    kb = keyboard.KeyBoard()
    pressed_keys = []
    prev_pressed_keys = []
    
    
    
    
    #init driver for the graphics
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
    color_order=st7789.BGR
    )
    
    
    
    
    # variables:

    #load config
    config = {}
    try:
        with open("config.json", "r") as conf:
            config = json.loads(conf.read())
            ui_color = config["ui_color"]
            bg_color = config["bg_color"]
            ui_sound = config["ui_sound"]
            volume = config["volume"]
            wifi_ssid = config["wifi_ssid"]
            wifi_pass = config["wifi_pass"]
            sync_clock = config["sync_clock"]
            timezone = config["timezone"]
    except:
        print("could not load settings from config.json. reloading default values.")
        config_modified = True
        ui_sound = True
        ui_color = default_ui_color
        bg_color = default_bg_color
        volume = default_volume
        wifi_ssid = ''
        wifi_pass = ''
        sync_clock = True
        timezone = 0
        with open("config.json", "w") as conf:
            config = {"ui_color":default_ui_color, "bg_color":default_bg_color, "ui_sound":default_ui_sound, "volume":default_volume, "wifi_ssid":'', "wifi_pass":'', "sync_clock":True, 'timezone':0}
            conf.write(json.dumps(config))
        
    
    force_redraw_display = True
    refresh_display = True
    
    mid_color = mh.mix_color565(ui_color, bg_color)
    
    cursor_index = 0
    prev_cursor_index = 0
    setting_screen_index = 0
    
    
    #init the beeper!
    beep = beeper.Beeper()
    
    #init diplsay
    tft.fill_rect(0,0,display_width, display_height, bg_color)
    
    
    while True:
        
        
        # ----------------------- check for key presses on the keyboard. Only if they weren't already pressed. --------------------------
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            # ~~~~~~ check if the arrow keys are newly pressed ~~~~~
            if ";" in pressed_keys and ";" not in prev_pressed_keys: # up arrow
                cursor_index -= 1
                if ui_sound:
                    beep.play(("E3","C3"), 100, volume)
                if cursor_index < 0:
                    cursor_index = 0
                refresh_display = True
            elif "." in pressed_keys and "." not in prev_pressed_keys: # down arrow
                cursor_index += 1
                if ui_sound:
                    beep.play(("D3","C3"), 100, volume)
                if cursor_index >= len(setting_names):
                    cursor_index = len(setting_names) - 1
                refresh_display = True
            
            if "GO" in pressed_keys or "ENT" in pressed_keys:
                # SETTINGS EDIT
                
                if setting_names[cursor_index] == 'ui_color':
                    ui_color = get_color(tft, font, kb, beep, 'ui_color:', ui_color, ui_color, bg_color, ui_sound, volume)
                    config["ui_color"] = ui_color
                    mid_color = mh.mix_color565(ui_color, bg_color)
                    force_redraw_display = True
                    
                elif setting_names[cursor_index] == 'bg_color':
                    bg_color = get_color(tft, font, kb, beep, 'bg_color:', bg_color, ui_color, bg_color, ui_sound, volume)
                    config["bg_color"] = bg_color
                    mid_color = mh.mix_color565(ui_color, bg_color)
                    force_redraw_display = True
                
                elif setting_names[cursor_index] == 'volume':
                    volume = get_volume(tft, font, kb, beep, 'volume:', volume, ui_color, bg_color, ui_sound)
                    config["volume"] = volume
                    force_redraw_display = True
                    
                elif setting_names[cursor_index] == 'wifi_ssid':
                    wifi_ssid = get_text(tft, font, kb, beep, 'wifi_ssid:', wifi_ssid, ui_color, bg_color, ui_sound, volume)
                    config["wifi_ssid"] = wifi_ssid
                    force_redraw_display = True
                elif setting_names[cursor_index] == 'wifi_pass':
                    wifi_pass = get_text(tft, font, kb, beep, 'wifi_pass:', wifi_pass, ui_color, bg_color, ui_sound, volume)
                    config["wifi_pass"] = wifi_pass
                    force_redraw_display = True
                elif setting_names[cursor_index] == 'sync_clock':
                    sync_clock = get_bool(tft, font, kb, beep, 'sync_clock:', sync_clock, ui_color, bg_color, ui_sound, volume)
                    config["sync_clock"] = sync_clock
                    force_redraw_display = True
                elif setting_names[cursor_index] == 'timezone':
                    timezone = get_int(tft, font, kb, beep, 'timezone:', timezone, -13,13, ui_color, bg_color, ui_sound, volume)
                    config["timezone"] = timezone
                    force_redraw_display = True
                    
                elif setting_names[cursor_index] == 'confirm': 
                    with open("config.json", "w") as conf: #save changes
                        conf.write(json.dumps(config))
                    if ui_sound:
                        beep.play(("C4","D4",("C3","E3","D3")), 100, volume)
                    del beep
                    # shut off the display
                    tft.fill(black)
                    tft.sleep_mode(True)
                    Pin(38, Pin.OUT).value(0) #backlight off
                    spi.deinit()
                    # return home
                    time.sleep_ms(10)
                    machine.reset()
                    
                    
            # once we parse the keypresses for this loop, we need to store them for next loop
            prev_pressed_keys = pressed_keys
            
        #scroll up and down logic
        if cursor_index >= setting_screen_index + 4:
            setting_screen_index += 1
            force_redraw_display = True
        elif cursor_index < setting_screen_index:
            setting_screen_index -= 1
            force_redraw_display = True
            
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Graphics: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        
        #write out all text
        if refresh_display or force_redraw_display:
            
            #blackout previous text
            if not force_redraw_display:
                tft.fill_rect(x=0, y=(32 * (prev_cursor_index - setting_screen_index)) + 4, width=display_width, height=32, color=bg_color)
            
            # draw text
            for i in range(setting_screen_index, setting_screen_index + 4):
                
                #blackout previous text 
                if force_redraw_display:
                    tft.fill_rect(0,4 + ((i - setting_screen_index) * 32),240,32,bg_color) 
                    
                if setting_names[i] != 'confirm' and setting_names[i] != 'wifi_pass':
                    # display value:
                    tft.text(fontsmall,
                                 str(config[setting_names[i]]),
                                 ((240 - (8 * len( str(config[setting_names[i]]) ))) + (16 * len(setting_names[i]) ) ) // 2, # centered in the empty space
                                 (32 * (i - setting_screen_index)) + 18,
                                 mid_color,bg_color)
                 
                if cursor_index == i: # the currently selected text
                    tft.text(font,'>' + setting_names[i] + '',-2, (32 * (i - setting_screen_index)) + 4,white,mid_color)
                    
                elif prev_cursor_index == i or force_redraw_display: # unselected text
                    tft.text(font,setting_names[i],6, (32 * (i - setting_screen_index)) + 4,ui_color,bg_color)
   
            #dividing lines
            tft.hline(0,36,display_width,mid_color)
            tft.hline(0,68,display_width,mid_color)
            tft.hline(0,100,display_width,mid_color)

            refresh_display = False 
        
        #update prev app selector index to current one for next cycle
        prev_cursor_index = cursor_index
        force_redraw_display = False
        
# run the main loop!
main_loop()





