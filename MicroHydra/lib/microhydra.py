import math


'''

This is a collection of utility functions for MicroHydra.

This module was created to prevent 'launcher.py' from becoming too large,
and to provide easy access to any other scripts or apps who want to use these same utilities.

'''



def separate_color565(color):
    """
    Separate a 16-bit 565 encoding into red, green, and blue components.
    """
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return red, green, blue


def combine_color565(red, green, blue):
    """
    Combine red, green, and blue components into a 16-bit 565 encoding.
    """
    # Ensure color values are within the valid range
    red = max(0, min(red, 31))
    green = max(0, min(green, 63))
    blue = max(0, min(blue, 31))

    # Pack the color values into a 16-bit integer
    return (red << 11) | (green << 5) | blue



def avg_color565(color1, color2):
    """
    Combine two colors in color565 format, 50/50.
    """
    r1,g1,b1 = separate_color565(color1)
    r2,g2,b2 = separate_color565(color2)
    
    r = r1 + r2
    r = r // 2
    g = g1 + g2
    g = g // 2
    b = b1 + b2
    b = b // 2
    
    return combine_color565(r,g,b)


def mix(val2, val1, fac=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * fac) + (val2 * (1.0 - fac))
    return output


def mix_angle_float(angle1, angle2, factor=0.5):
    """take two angles as floats (range 0.0 to 1.0) and average them to the weight of factor.
    Mainly for blending hue angles."""
    # Ensure hue values are in the range [0, 1)
    angle1 = angle1 % 1
    angle2 = angle2 % 1

    # Calculate the angular distance between hue1 and hue2
    angular_distance = (angle2 - angle1 + 0.5) % 1 - 0.5

    # Calculate the middle hue value
    blended = (angle1 + angular_distance * factor) % 360

    return blended

def remap(value, in_min, in_max, clamp=True):
    if clamp == True:
        if value < in_min:
            return 0.0
        elif value > in_max:
            return 1.0
    # Scale the value to be in the range 0.0 to 1.0
    return (value - in_min) / (in_max - in_min)


def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod



def rgb_to_hsv(r, g, b):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v



def hsv_to_rgb(h, s, v):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    if s == 0.0:
        return v, v, v
    i = math.floor(h*6.0)
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    # Cannot get here
    

def mix_color565(color1, color2, mix_factor=0.5):
    """
    High quality mixing of two rgb565 colors, by converting through HSV color space.
    This function is probably too slow for running constantly in a loop, but should be good for occasional usage.
    """
    #separate to components
    r1,g1,b1 = separate_color565(color1)
    r2,g2,b2 = separate_color565(color2)
    #convert to float 0.0 to 1.0
    r1 /= 31; r2 /= 31
    g1 /= 63; g2 /= 63
    b1 /= 31; b2 /= 31
    #convert to hsv 0.0 to 1.0
    h1,s1,v1 = rgb_to_hsv(r1,g1,b1)
    h2,s2,v2 = rgb_to_hsv(r2,g2,b2)
    
    #mix the hue angle
    hue = mix_angle_float(h1,h2,factor=mix_factor)
    #average the rest
    sat = (s1 + s2) / 2
    val = (v1 + v2) / 2
    
    #convert back to rgb floats
    red,green,blue = hsv_to_rgb(hue,sat,val)
    #convert back to 565 range
    red = math.floor(red * 31)
    green = math.floor(green * 63)
    blue = math.floor(blue * 31)
    
    return combine_color565(red,green,blue)



def darker_color565(color,mix_factor=0.5):
    """
    Get the darker version of a 565 color.
    """
    #separate to components
    r,g,b = separate_color565(color)
    #convert to float 0.0 to 1.0
    r /= 31; g /= 63; b /= 31
    #convert to hsv 0.0 to 1.0
    h,s,v = rgb_to_hsv(r,g,b)
    
    #higher sat value is percieved as darker
    s *= 1 + mix_factor
    v *= 1 - mix_factor
    
    #convert back to rgb floats
    r,g,b = hsv_to_rgb(h,s,v)
    #convert back to 565 range
    r = math.floor(r * 31)
    g = math.floor(g * 63)
    b = math.floor(b * 31)
    
    return combine_color565(r,g,b)


def lighter_color565(color,mix_factor=0.5):
    """
    Get the lighter version of a 565 color.
    """
    #separate to components
    r,g,b = separate_color565(color)
    #convert to float 0.0 to 1.0
    r /= 31; g /= 63; b /= 31
    #convert to hsv 0.0 to 1.0
    h,s,v = rgb_to_hsv(r,g,b)
    
    #higher sat value is percieved as darker
    s *= 1 - mix_factor
    v *= 1 + mix_factor
    
    #convert back to rgb floats
    r,g,b = hsv_to_rgb(h,s,v)
    #convert back to 565 range
    r = math.floor(r * 31)
    g = math.floor(g * 63)
    b = math.floor(b * 31)
    
    return combine_color565(r,g,b)


def color565_shiftred(color, mix_factor=0.5):
    """
    Simple convenience function which shifts a color toward red.
    This was made for displaying 'negative' ui elements, while sticking to the central color theme.
    """
    red = const(63488)
    return mix_color565(color, red, mix_factor)
    

def color565_shiftgreen(color, mix_factor=0.5):
    """
    Simple convenience function which shifts a color toward green.
    This was made for displaying 'positive' ui elements, while sticking to the central color theme.
    """
    green = const(2016)
    return mix_color565(color, green, mix_factor)
    
    
    
if __name__ == "__main__":
    # just for testing
    
    print('output:', mix_color565(4421, 53243, 0.5))
