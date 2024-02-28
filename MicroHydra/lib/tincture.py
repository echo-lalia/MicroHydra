import math

"""
Tincture version 1.2

changes:
    Heavily trimmed for use in MicroPython
"""

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      Basic convenience functions:      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def separate_color565(color):
    """
    Separate a 16-bit 565 encoding into red, green, and blue components.
    """
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return red, green, blue

def clamp(value,minimum,maximum,):
    #choose the largest: value, or the minimum
    output = max(value, minimum)
    #then choose the smallest, of the max and the value
    output = min(output, maximum)
    return output

def blend_tuple(input1,input2,factor=0.5):
    """take two tuples of equal size, and average them to the weight of factor.
    Mainly for blending colors."""
    output = []
    for i in range(0,len(input1)):
        val1 = input1[i]
        val2 = input2[i]
        new_val = (val1 * (1 - factor)) + (val2 * factor)
        output.append(new_val)
    return tuple(output)

def blend_angle(angle1, angle2, factor=0.5):
    """take two angles, and average them to the weight of factor.
    Mainly for blending hue angles."""
    # Ensure hue values are in the range [0, 360)
    angle1 = angle1 % 360
    angle2 = angle2 % 360

    # Calculate the angular distance between hue1 and hue2
    angular_distance = (angle2 - angle1 + 180) % 360 - 180

    # Calculate the middle hue value
    blended = (angle1 + angular_distance * factor) % 360

    return blended

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      Tinct - color class definition      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Tinct:
    """'To tinge or tint / tinged; colored; flavored' - 
    This class aims to provide a very simple and straightforward way to mix, convert, and manipulate color.
    Colors are stored as a Tuple of floats in RGB, but can be converted an manipulated in any supported colorspace."""
    
    def __init__(self,RGB565=None,RGB=None,RGBA=None,RGB255=None,HSL=None,okLab=None,okLCh=None,hex=None):
        self.rgb = (0.0,0.0,0.0)
        #check each of the input variables and preform required transformations.
        if RGB565:
            self.set_RGB565(RGB565)
        elif RGB:
            self.set_RGB(RGB)
        elif RGBA:
            r,g,b,a = RGBA
            self.set_RGB((r,g,b))
            self.alpha = a
        elif RGB255:
            self.set_RGB255(RGB255)
        elif HSL:
            self.set_HSL(HSL)
        elif okLab:
            self.set_okLab(okLab)
        elif okLCh:
            self.set_okLCh(okLCh)
        elif hex:
            self.set_hex(hex)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   Useful modifiers:   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def blend(self,other_tinct:'Tinct',fac=0.5,ease=False) -> 'Tinct':
        """Mix this Tinct with another using factor. Transform is done is okLCh space."""
        l1,c1,h1 = self.get_okLCh()
        l2,c2,h2 = other_tinct.get_okLCh()
        l3,c3 = blend_tuple((l1,c1),(l2,c2),factor=fac)
        h3 = blend_angle(h1,h2,factor=fac)
        return Tinct(okLCh=(l3,c3,h3))
    
    def add_lightness(self,amount, clamped=True) -> 'Tinct':
        """Add amount (percent) to current lightness. Values can be negative.
        If clamped is True, resulting lightness will be clamped to range of 0-100%"""
        l,a,b = self.get_okLab()
        l = l + amount
        if clamped:
            l = clamp(l,0,100)
        return Tinct(okLab=(l,a,b))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   'set_' functions:   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def set_RGB565(self,rgb565):
        """Input RGB as int in 16bit 565 encoding."""
        r,g,b = separate_color565(rgb565)
        self.rgb = (r/31,g/63,b/31)
    
    def set_okLab(self,Lab):
        l,a,b = Lab
        #convert from percentages to 0,1 / -1,1 range
        #print(l,a,b)
        l *= 0.01
        a *= 0.01
        b *= 0.01
        #print(l,a,b)

        l_ = l + (0.39634 * a) + (0.2158 * b)
        m_ = l - (0.10556 * a) - (0.06385 * b)
        s_ = l - (0.08948 * a) - (1.29149 * b)

        l = l_*l_*l_
        m = m_*m_*m_
        s = s_*s_*s_

        rgb = self.linear_sRGB_transform((
        +(4.07674 * l) - (3.30771 * m) + (0.23097 * s),
        -(1.26844 * l) + (2.60976 * m) - (0.34132 * s),
        -(0.0042 * l) - (0.70342 * m) + (1.70761 * s)))
        self.rgb = rgb

    def set_HSL(self,HSL):
        #convert HSL to RGB
        h,s,l = HSL
        #default should be percentage, so change to range 0 - 1
        s *= 0.01
        l *= 0.01
        chroma = (1 - abs((2 * l) - 1)) * s
        h_prime = h / 60
        X = chroma * (1 - abs(h_prime % 2 - 1))
        if 0 <= h_prime <= 1:
            tempRGB = (chroma,X,0)
        elif 1 <= h_prime <= 2:
            tempRGB = (X,chroma,0)
        elif 2 <= h_prime <= 3:
            tempRGB = (0,chroma,X)
        elif 3 <= h_prime <= 4:
            tempRGB = (0,X,chroma)
        elif 4 <= h_prime <= 5:
            tempRGB = (X,0,chroma)
        else:
            tempRGB = (chroma,0,X)
        m = l - (chroma / 2)
        r = tempRGB[0] + m; g = tempRGB[1] + m; b = tempRGB[2] + m
        self.rgb = (r,g,b)

    def set_RGB(self,RGB):
        """Input RGB as a 3 tuple of floats, range[0,1]"""
        self.rgb = RGB
    
    def set_RGB255(self,RGB255):
        """Input RGB as a 3 tuple of floats (or int) with range[0,255]"""
        r,g,b = RGB255
        self.rgb = (r/255,g/255,b/255)   
    
    def set_okLCh(self,LCh):
        """polar LCH to okLab"""
        l,chroma,hue = LCh

        a = chroma * math.cos(math.radians(hue))
        b = chroma * math.sin(math.radians(hue))
        self.set_okLab((l,a*100,b*100)) # oklab method expects a percentage input

    def set_hex(self,hex):
        """input an rgb hex"""
        cleaned = hex.replace('#','').strip()
        r,g,b = bytes.fromhex(cleaned)
        self.set_RGB255((r,g,b))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 'get_' functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

    def get_RGB565(self) -> int:
        """return RGB value as a 16bit integer with RGB565 encoding."""
        red, green, blue = self.get_RGB255()
        return (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3

    def get_RGB(self) -> tuple[float,float,float]:
        """return RGB value as tuple with range [0,1]"""
        #get the rgb color of this Tinct.
        r,g,b = self.rgb
        return (clamp(r,minimum=0,maximum=1),clamp(g,minimum=0,maximum=1),clamp(b,minimum=0,maximum=1))

    def get_HSL(self,as_int=False) -> tuple[float,float,float]:
        """return HSL value as tuple with range:
        H [0,360], S [0,100%], L [0,100%]"""
        r,g,b = self.rgb
        Cmax = max(r,g,b)
        Cmin = min(r,g,b)
        delta = Cmax - Cmin

        #get hue
        if delta == 0:
            hue = 0
        elif Cmax == r:
            hue = 60 * (((g - b) / delta) % 6 )
        elif Cmax == g:
            hue = 60 * (((b-r+(2*delta)) / delta) % 6)
        else: #Cmax == b
            hue = 60 * (((r-g+(4*delta)) / delta) % 6)

        # get lightness
        lightness = (Cmax + Cmin) / 2

        #get saturation
        if delta == 0:
            saturation = 0
        else:
            saturation = delta / ( 1 - (abs( 2 * lightness - 1 )))

        #convert to percentage
        saturation *= 100
        lightness *= 100

        if as_int:
            hue = int(round(hue))
            saturation = int(round(saturation))
            lightness = int(round(lightness))

        return (hue,saturation,lightness)

    def get_RGB255(self) -> tuple[int,int,int]:
        """return okLab value as tuple with range:
        R [0,255], G [0,255], B [0,255]"""
        r,g,b = self.rgb
        r = clamp(r,0,1)
        g = clamp(g,0,1)
        b = clamp(b,0,1)
        r = int(round(r * 255))
        g = int(round(g * 255))
        b = int(round(b * 255))
        return (r,g,b)
    
    def get_okLab(self) -> tuple[float,float,float]: 
        """return okLab value as tuple with range:
        L [0,100%], a [-100%,100%], b [-100%,100%]"""
        r,g,b = self.inverse_linear_sRGB_transform(self.rgb)
        l = (0.41222 * r) + (0.53633 * g) + (0.05145 * b)
        m = (0.2119 * r) + (0.6807 * g) + (0.1074 * b)
        s = (0.0883 * r) + (0.28172 * g) + (0.62998 * b)

        l_ = l ** 0.33333
        m_ = m ** 0.33333
        s_ = s ** 0.33333

        return (
        ((0.21045*l_) + (0.793618*m_) - (0.00407*s_)) * 100,
        ((1.978*l_) - (2.42859*m_) + (0.45059*s_)) * 100,
        ((0.0259*l_) + (0.78277*m_) - (0.80868*s_)) * 100,
        )

    def get_okLCh(self) -> tuple[float,float,float]:
        """Converts value to L,C,h with ranges:
        L [0% : 100%], C [0 : 0.4ish], h [0 : 360]"""
        l,a,b = self.get_okLab()
        #convert values back to proper ranges
        a *= 0.01
        b *= 0.01

        chroma = math.sqrt((a ** 2) + (b ** 2)) #chroma
        hue = math.degrees(math.atan2(b,a)) # hue degrees
        return (l,chroma,hue)

    def get_hex(self) -> str:
        """Get a hexidecimal representation of the color."""
        return '#%02x%02x%02x' % self.get_RGB255()
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ dunders: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self):
        return 3 #len(self.rgb) should never change, so 3 is ok

    def __getitem__(self,index):
        rgb = self.get_RGB255()
        return rgb[index]

    def __str__(self):
        return self.get_hex()
    
    def __repr__(self):
        r,g,b = self.get_RGB255(as_float=True)
        return f'Tinct({r},{g},{b})'

    def __eq__(self, other):
        if type(other) == Tinct:
            return self.get_RGB255() == other.get_RGB255()
        else:
            return self.get_RGB255() == other

    def __int__(self):
        return  self.get_RGB565()
    
    # math
    def __add__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r += other
            g += other
            b += other
            return Tinct(RGB=(r,g,b))
        elif type(other) == Tinct:
            r,g,b = self.rgb
            r2,g2,b2 = other.rgb
            return Tinct(RGB=(r+r2,g+g2,b+b2))
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r+r2,g+g2,b+b2))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        #if we made it here, its unsupported
        return NotImplemented
        
    def __rsub__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r = other - r
            g = other - g
            b = other - b
            return Tinct(RGB=(r,g,b))
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r2-r,g2-g,b2-b))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __lt__(self,other):
        if type(other) != Tinct:
            return NotImplemented
        else:
            return sum(self.rgb) < sum(other.rgb)
        
    def __gt__(self,other):
        if type(other) != Tinct:
            return NotImplemented
        else:
            return sum(self.rgb) > sum(other.rgb)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ additional helper functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

    # linear srgb conversions are described here:
    # https://bottosson.github.io/posts/colorwrong/#what-can-we-do%3F
    def linear_sRGB_transform(self,sRGB:float) -> tuple[float,float,float]:
        output = []
        for x in sRGB:
            if x >= 0.00313:
                output.append( (1.055 * (x**(1.0/2.4))) - 0.055 )
            else:
                output.append( 12.92 * x )
        return tuple(output)
    
    def inverse_linear_sRGB_transform(self,RGB:float) -> tuple[float,float,float]:
        output = []
        for x in RGB:
            if x >= 0.04045:
                output.append( ((x + 0.055) / (1 + 0.055))**2.4 )
            else:
                output.append( x / 12.92 )
        return tuple(output)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   Testing or demo body:   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == '__main__':
    from machine import Pin, SPI
    from lib import st7789fbuf
    tft = st7789fbuf.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )
    
    # the demo below shows a gradient between two nearly opposite colors.
    # the colors should blend evenly and maintain their intensity through the middle
    # a regular rgb gradient should become gray or muddy in the middle
    
    # define colors
    color_start = Tinct(RGB255=(255,255,1))
    color_end = Tinct(RGB255=(38,0,230))
    
    # create a tincture object to mix colors
    color_list = (
        color_start.blend(color_end, 0.2),
        color_start.blend(color_end, 0.3),
        color_start.blend(color_end, 0.4),
        color_start.blend(color_end, 0.5),
        color_start.blend(color_end, 0.6),
        color_start.blend(color_end, 0.7),
        color_start.blend(color_end, 0.8),
        )
    
    
    #add starting colors to the left and right
    tft.rect(0,0,20,135, color_start.get_RGB565(), fill=True)
    tft.rect(220,0,20,135, color_end.get_RGB565(), fill=True)
    

    
    # loop through color list to draw out our palette
    color_bar_width = 220 // len(color_list)
    for idx, clr in enumerate(color_list):
        tft.rect(
            10 + (idx*color_bar_width), 0, color_bar_width, 135,
            clr.get_RGB565(), fill=True
            )
        
    tft.show()
