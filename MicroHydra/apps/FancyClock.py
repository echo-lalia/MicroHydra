from lib import st7789py, keyboard
from lib import microhydra as mh
from launcher.icons import battery
import time
from font import vga2_16x32 as font
from font import vga1_8x16 as font2
from machine import SPI, Pin, PWM, reset, ADC
import machine
import random

max_bright = const(65535)
min_bright = const(22000)
bright_peak = const(65535)
bright_step = const(500)

#a simple clock program for the cardputer


tft = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=None, #because we will control that manually
    rotation=1,
    color_order=st7789py.BGR
    )





blight = PWM(Pin(38, Pin.OUT))
blight.freq(1000)
blight.duty_u16(bright_peak)


tft.fill_rect(-40,0,280, 135, 0)

months_names = {
    1:'Jan',
    2:'Feb',
    3:'Mar',
    4:'Apr',
    5:'May',
    6:'Jun',
    7:'Jul',
    8:'Aug',
    9:'Sep',
    10:'Oct',
    11:'Nov',
    12:'Dec'
    }


def hsv_to_rgb(HSV):
    ''' Converts an integer HSV tuple (value range from 0 to 255) to an RGB tuple '''
    
    # Unpack the HSV tuple for readability
    H, S, V = HSV

    # Check if the color is Grayscale
    if S == 0:
        R = V
        G = V
        B = V
        return (R, G, B)

    # Make hue 0-5
    region = H // 43;

    # Find remainder part, make it from 0-255
    remainder = (H - (region * 43)) * 6; 

    # Calculate temp vars, doing integer multiplication
    P = (V * (255 - S)) >> 8;
    Q = (V * (255 - ((S * remainder) >> 8))) >> 8;
    T = (V * (255 - ((S * (255 - remainder)) >> 8))) >> 8;


    # Assign temp vars based on color cone region
    if region == 0:
        R = V
        G = T
        B = P
    elif region == 1:
        R = Q; 
        G = V; 
        B = P;
    elif region == 2:
        R = P; 
        G = V; 
        B = T;
    elif region == 3:
        R = P; 
        G = Q; 
        B = V;
    elif region == 4:
        R = T; 
        G = P; 
        B = V;
    else: 
        R = V; 
        G = P; 
        B = Q;

    return (R, G, B)


def get_random_colors():
    #main hue
    hue1 = random.randint(0,255)
    #bg hue
    hue2 = hue1 + random.randint(-80,80)
    
    sat1 = random.randint(0,255)
    sat2 = random.randint(50,255)

    
    val1 = random.randint(245,255)
    val2 = random.randint(10,20)
    
    
    
    #convert to color565
    ui_color = st7789py.color565(hsv_to_rgb((hue1,sat1,val1)))
    bg_color = st7789py.color565(hsv_to_rgb((hue2,sat2,val2)))
    lighter_color = st7789py.color565(hsv_to_rgb((hue2,max(sat2 - 5, 0),val2 + 8)))
    darker_color = st7789py.color565(hsv_to_rgb((hue2,min(sat2 + 60, 255),max(val2 - 4,0))))
    
    #get middle hue
    mid_color = mh.mix_color565(bg_color, ui_color)
    
    return ui_color, bg_color, mid_color, lighter_color, darker_color
    
    
    
def read_battery_level(adc):
    """
    read approx battery level on the adc and return as int range 0 (low) to 3 (high)
    """
    raw_value = adc.read_uv() # vbat has a voltage divider of 1/2

    if raw_value < 525000: # 1.05v
        return 0
    if raw_value < 1050000: # 2.1v
        return 1
    if raw_value < 1575000: # 3.15v
        return 2
    return 3 # 4.2v or higher



kb = keyboard.KeyBoard()

moving_right = True #horizontal movement
moving_up = False #vertical movement

x_pos = 50
y_pos = 50

#random color
ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
red_color = mh.color565_shiftred(mid_color)

old_minute = 0

prev_pressed_keys = kb.get_pressed_keys()
current_bright = bright_peak

#init the ADC for the battery
batt = ADC(10)
batt.atten(ADC.ATTN_11DB)

batt_level = read_battery_level(batt)



#we can slightly speed up the loop by only doing some calculations every x number of frames
loop_timer = 0

#init vals for loop timer stuff:
_, month, day, hour_24, minute, _,_,_ = time.localtime()
hour_12 = hour_24 % 12
if hour_12 == 0:
    hour_12 = 12
ampm = 'AM'
if hour_24 >= 12:
    ampm = 'PM'
time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
date_string = f"{months_names[month]},{day}"
time_width = len(time_string) * 16
date_width = len(date_string) * 8
batfill_total_width = (time_width + 16) - (date_width + 4)


while True:
    
    #loop timer stuff; only update every x number of frames
    if loop_timer > 100:
        loop_timer = 0
        
        _, month, day, hour_24, minute, _,_,_ = time.localtime()
    
        hour_12 = hour_24 % 12
        if hour_12 == 0:
            hour_12 = 12
        
        ampm = 'AM'
        if hour_24 >= 12:
            ampm = 'PM'
        
        time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
        date_string = f"{months_names[month]},{day}"
        time_width = len(time_string) * 16
        date_width = len(date_string) * 8
        
        batfill_total_width = (time_width + 16) - (date_width + 4)
        
    else:
        loop_timer += 1
        
        
        
    #add main graphics first
    tft.text(
        font,
        time_string,
        x_pos,
        y_pos,
        ui_color, bg_color)
    tft.text(
        font2,
        ampm,
        time_width + x_pos,16 + y_pos,
        mid_color, bg_color)
    
    #date
    tft.fill_rect(x_pos,y_pos + 32, 4, 16, bg_color)
    tft.text(
        font2,
        date_string,
        x_pos + 4,
        y_pos + 32,
        mid_color, bg_color)
        
        
        
    # extract useful positions for fill section
    battfill_x = x_pos + date_width + 4
    battfill_y = y_pos + 32
    batt_x = x_pos + time_width - 8
    

    
    # battery

    if batt_level == 3:
        tft.bitmap_icons(battery, battery.FULL, (bg_color,mid_color),batt_x, y_pos + 34)
    elif batt_level == 2:
        tft.bitmap_icons(battery, battery.HIGH, (bg_color,mid_color),batt_x, y_pos + 34)
    elif batt_level == 1:
        tft.bitmap_icons(battery, battery.LOW, (bg_color,mid_color),batt_x, y_pos + 34)
    elif batt_level == 0:
        tft.bitmap_icons(battery, battery.EMPTY, (bg_color,red_color),batt_x, y_pos + 34)
        
        
        
    #the spot beside the date and battery
    #we have to fill AROUND the battery to prevent a flashy/glitchy display
    tft.fill_rect(battfill_x, battfill_y, batfill_total_width , 2, bg_color) #line above
    tft.fill_rect(battfill_x, battfill_y + 12, batfill_total_width , 4, bg_color) #line below
    tft.fill_rect(batt_x + 20, battfill_y + 2, 4 , 10, bg_color) #box right
    tft.fill_rect(battfill_x, battfill_y + 2, batfill_total_width - 24, 10, bg_color) #box left
    
    
    
    #cover up the little spot above the am/pm
    tft.fill_rect(x_pos + time_width, y_pos, 16, 16, bg_color)
    
    
    
    #add a line to the right to pad the am/pm a little
    tft.fill_rect(x_pos + time_width + 16, y_pos, 2, 49, bg_color)
    #and a line to the left to frame the time better
    tft.fill_rect(x_pos-2, y_pos, 2, 49, bg_color)
    
    
    
    #highlight/shadow
    tft.hline(x_pos-2, y_pos-1, time_width + 20, lighter_color)
    tft.hline(x_pos-2, y_pos+48, time_width + 20, darker_color)

    
    if moving_right:
        x_pos += 1
    else:
        x_pos -= 1
        
    if moving_up:
        y_pos -= 1
    else:
        y_pos +=1
    
    
    #y_collision
    if y_pos <= 1:
        y_pos = 1
        moving_up = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = mh.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
    elif y_pos >= 87:
        y_pos = 87
        moving_up = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = mh.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
        
    #x_collision
    if x_pos <= 0:
        x_pos = 0
        moving_right = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = mh.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
    elif x_pos >= 224 - time_width:
        x_pos = 224 - time_width
        moving_right = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = mh.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
    
    
    
    
    #refresh bg on 5 mins
    if minute != old_minute and minute % 5 == 0:
        old_minute = minute
        tft.fill(0)
        
    #keystrokes and backlight
    pressed_keys = kb.get_pressed_keys()
    if pressed_keys != prev_pressed_keys: # some button has been pressed
        if "GO" in pressed_keys:
            tft.fill(0)
            tft.sleep_mode(True)
            blight.duty_u16(0)
            reset()
        current_bright = bright_peak
    elif current_bright != min_bright:
        current_bright -= bright_step
        if current_bright < min_bright:
            current_bright = min_bright
        blight.duty_u16(min(max_bright,current_bright))
        
        
    prev_pressed_keys = pressed_keys
    
    if "SPC" in pressed_keys:
        current_bright = bright_peak
        time.sleep_ms(1)
    else:
        time.sleep_ms(70)






