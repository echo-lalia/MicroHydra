from lib import st7789py
import time
from font import vga2_16x32 as font
from font import vga1_8x16 as font2
from machine import SPI, Pin, PWM
import random

#a simple clock program for the cardputer



tft = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT), #because we will controll that manually
    rotation=1,
    color_order=st7789py.BGR
    )








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










#main body:
    
    
#backlight.duty_u16(50000)

moving_right = True #horizontal movement
moving_up = False #vertical movement

x_pos = 0
y_pos = 0

#random color
r, g, b = hsv_to_rgb((random.randint(0,255), random.randint(0,255), 255))

while True:
    
    _,_,_, hour_24, minute, _,_,_ = time.localtime()
    
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    
    ampm = 'AM'
    if hour_24 >= 12:
        ampm = 'PM'
    
    time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
    time_width = len(time_string) * 16
    
    
    
    tft.text(
        font,
        time_string,
        x_pos,
        y_pos,
        st7789py.color565(r,g,b))
    tft.text(
        font2,
        f'{ampm}',
        time_width + x_pos,16 + y_pos,
        st7789py.color565(r//2,g//2,b//2))
    
    if moving_right:
        x_pos += 1
    else:
        x_pos -= 1
        
    if moving_up:
        y_pos -= 1
    else:
        y_pos +=1
    
    
    #y_collision
    if y_pos <= 0:
        y_pos = 0
        moving_up = False
        r,g,b = hsv_to_rgb((random.randint(0,255), random.randint(0,255), 255))
        
    elif y_pos >= 103:
        y_pos = 103
        moving_up = True
        r,g,b = hsv_to_rgb((random.randint(0,255), random.randint(0,255), 255))
        
    #x_collision
    if x_pos <= 0:
        x_pos = 0
        moving_right = True
        r,g,b = hsv_to_rgb((random.randint(0,255), random.randint(0,255), 255))
    elif x_pos >= 224 - time_width:
        x_pos = 224 - time_width
        moving_right = False
        r,g,b = hsv_to_rgb((random.randint(0,255), random.randint(0,255), 255))
    
    time.sleep(0.05)
