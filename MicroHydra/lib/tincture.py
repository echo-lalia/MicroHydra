import math

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      Basic convenience functions:      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

def wrap(value, minimum, maximum):
    """Basically a modulo wrapper, this convenience function wraps a value around,
    in the range of min to max."""
    output = value
    
    #translate the value by the min, because modulo works here on min=0
    output -= minimum
    deltamax = maximum - minimum
    
    #then modulo to wrap in our new range of 0 - deltamax. 
    output = output % deltamax
    
    #ok, now shift back to the original range
    output += minimum
    #lastly clamp so that we dont have any weird values due to rounding errors
    return clamp(output, minimum=minimum, maximum=maximum)

def blend_value(input1,input2,factor=0.5):
    """take two numbers, and average them to the weight of factor."""
    new_val = (input1 * (1 - factor)) + (input2 * factor)
    return new_val

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

def sigmoid(val):
    return 1 / (1 + math.exp(-val))

def ease_in_out(x:float) -> float:
    """easeInOutQuad function implementation"""
    if x < 0.5:
        return 2 * x**2
    else:
        return 1 - ((-2 * x + 2)**2) / 2
    
def map_range(value:float, input_min:float, input_max:float, output_min:float=0, output_max:float=1) -> float:
    """Take value, from range (input_min,input_max), and reshape it for the range (output_min,output_max)"""
    output = value - input_min
    output = output / (input_max - input_min)
    output = output * (output_max - output_min)
    output += output_min
    return output

def binary_search(sorted_list, target):
    """This helper function is used to quickly find the index of 2 numbers in a sorted list, 
    which are closest in value to the target value (one above and one below) """
    low = 0
    high = len(sorted_list) - 1

    # Handle cases where the target is outside the range of the list
    if target <= sorted_list[0]:
        return None, 0
    elif target >= sorted_list[-1]:
        return len(sorted_list) - 1, None

    while low <= high:
        mid = (low + high) // 2

        if sorted_list[mid] == target:
            # for consistency we should return mid twice, but if we do that, we'll waste time comparing them later.
            #so just return one, it should be a little faster. 
            return mid, None

        if sorted_list[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    # At this point, high is the index of the largest element < target,
    # and low is the index of the smallest element > target.
    return high, low



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      Tinct - color class definition      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Tinct:
    """'To tinge or tint / tinged; colored; flavored' - 
    This class aims to provide a very simple and straightforward way to mix, convert, and manipulate color.
    Colors are stored as a Tuple of floats in RGB, but can be converted an manipulated in any supported colorspace."""
    
    def __init__(self,RGB565=None,RGB=None,RGBA=None,RGB255=None,HSL=None,okLab=None,okLCh=None,hex=None,position=None,alpha=1):
        self.rgb = (0.0,0.0,0.0)
        # I have chosen to store the value as an rgb value.
        # This is being done purely for convenience. Another colorspace might make more sense,
        # but this way it requires a minimum understanding of colorspaces to utilize the stored value.
        # However, the self.rgb value should always be raw; we need to be able to convert between
        # other colorspaces as well, even if those spaces are larger than RGB. 


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

        self.alpha = alpha

        #Tinct stores it's own position for use in Tincture
        self.position = position


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   Useful modifiers:   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def blend(self,other_tinct:'Tinct',factor=0.5,ease=False) -> 'Tinct':
        """Mix this Tinct with another using factor. Transform is done is okLCh space. 
        if ease == True, apply an easing function to the factor (otherwise linear blend)"""
        if ease:
            fac = ease_in_out(factor)
        else:
            fac = factor
        l1,c1,h1 = self.get_okLCh()
        l2,c2,h2 = other_tinct.get_okLCh()
        l3,c3 = blend_tuple((l1,c1),(l2,c2),factor=fac)
        h3 = blend_angle(h1,h2,factor=fac)
        return Tinct(okLCh=(l3,c3,h3))


    def gradient(self, other_tinct:'Tinct',ease=False) -> 'Gradient':
        """Return a Gradient object that starts at this Tinct, and ends at other_tinct."""      
        return Gradient(RGB_start=self.get_RGB(), RGB_end=other_tinct.get_RGB(), ease=ease)
    
    def darker(self) -> 'Tinct':
        """Simply get a darker version of the color. Use add_lightness for a specific amount."""
        return self % 0
    
    def lighter(self) -> 'Tinct':
        """Simply get a lighter version of the color. Use add_lightness for a specific amount."""
        return self % 100
    
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

    def set_RGBA(self,RGBA):
        """Input RGBA as a 4 tuple of floats, range[0,1]"""
        r,g,b,a = RGBA
        self.rgb = (r,g,b)
        self.alpha = a
    
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

    def set_alpha(self,a):
        """update alpha value"""
        self.alpha = a

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
    
    def get_RGBA(self) -> tuple[float,float,float,float]:
        """return RGBA value as a 4 tuple of floats, range [0,1]"""
        r,g,b = self.rgb
        return (clamp(r,0,1),clamp(g,0,1),clamp(b,0,1),clamp(self.alpha,0,1))
        
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

    def get_RGB255(self, as_float=False) -> tuple[int,int,int]:
        """return okLab value as tuple with range:
        R [0,255], G [0,255], B [0,255]"""
        r,g,b = self.rgb
        r = clamp(r,0,1)
        g = clamp(g,0,1)
        b = clamp(b,0,1)
        if as_float:
            r = (r * 255)
            g = (g * 255)
            b = (b * 255)
        else:
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

    def get_alpha(self) -> float:
        """Get this Tincts alpha, as a float range 0-1"""
        return clamp(self.alpha,0,1)
    
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
        rgb = self.get_RGB255()
        result = ''
        for val in rgb:
            valstr = str(val)
            while len(valstr) < 3:
                valstr = '0' + valstr
            result += valstr
        return  int(result)
    
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
        
    def __sub__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r -= other
            g -= other
            b -= other
            return Tinct(RGB=(r,g,b))
        elif type(other) == Tinct:
            r,g,b = self.rgb
            r2,g2,b2 = other.rgb
            return Tinct(RGB=(r-r2,g-g2,b-b2))
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r-r2,g-g2,b-b2))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __mul__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r *= other
            g *= other
            b *= other
            return Tinct(RGB=(r,g,b))
        elif type(other) == Tinct:
            r,g,b = self.rgb
            r2,g2,b2 = other.rgb
            return Tinct(RGB=(r*r2,g*g2,b*b2))
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r*r2,g*g2,b*b2))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __truediv__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r /= other
            g /= other
            b /= other
            return Tinct(RGB=(r,g,b))
        elif type(other) == Tinct:
            # /0 operations are lazily avoided to allow for simple photo-editor-like behavior on Tinct/Tinct
            r,g,b = self.rgb
            r2,g2,b2 = other.rgb
            if r2 == 0:
                rr=r/0.00001
            else:
                rr = r / r2
            if g2 == 0:
                gg=g/0.00001
            else:
                gg = g / g2
            if b2 == 0:
                bb = b/0.00001
            else:
                bb = b / b2
            return Tinct(RGB=(rr,gg,bb))
        
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r/r2,g/g2,b/b2))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')

            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __mod__(self,other):
        #mod on tinct blends colors together
        if type(other) in {int,float,bool}:
            #if only one number is provided, just change lightness
            l,a,b = self.get_okLab()
            return self.blend(Tinct(okLab=(other,a,b)))
        elif type(other) == Tinct:
            # Tinct%Tinct shorthands a simple blend of colors
            return self.blend(other)
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    return self.blend(Tinct(RGB=(other)))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __radd__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r += other
            g += other
            b += other
            return Tinct(RGB=(r,g,b))
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

    def __rmul__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r *= other
            g *= other
            b *= other
            return Tinct(RGB=(r,g,b))
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r*r2,g*g2,b*b2))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')
            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented
        
    def __rtruediv__(self,other):
        if type(other) in {int,float,bool}:
            r,g,b = self.rgb
            r = other / r
            g = other / g
            b = other / b
            return Tinct(RGB=(r,g,b))
        
        elif type(other) in {list,tuple}:
            if len(other) == 3:
                if type(other[0]) in {int,float,bool} and type(other[1]) in {int,float,bool} and type(other[2]) in {int,float,bool}:
                    r,g,b = self.rgb
                    r2,g2,b2 = other
                    return Tinct(RGB=(r2/r,g2/g,b2/b))
                else:
                    raise TypeError(f'Operations between Tinct and {type(other)} expect numerical values')

            else:
                raise TypeError(f'Operations between Tinct and {type(other)} expect that len({type(other)} == 3)')
        else:
            return NotImplemented

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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    Tincture - color class definition     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Tincture:
    """To impart a tint or color to; To imbue or infuse with something.
    Params:
     - positions
     - blend_mode: 'linear' 'ease' or 'auto' to choose based on positions of content"""
    def __init__(self,*args,colors=None,positions=None, blend_mode='auto'):
        # args is the input colors. if input_colors is given, it overrides args. 
        # positions is 0-1, representing position of each Tinct.

        self.blend_mode=blend_mode

        input_colors = list(args)
        if len(input_colors) == 1:
            if type(input_colors[0]) in {list, tuple}:
                input_colors = input_colors[0]
        if colors:
            if type(colors) == Tinct:
                input_colors = [colors]
            else:
                input_colors = colors
        my_elements = []
        for item in input_colors:
            if type(item) == Tinct:
                my_elements.append(item)
            elif type(item) == Tincture:
                my_elements += item.elements
            elif type(item) == str:
                my_elements.append(Tinct(hex=item))
            elif type(item) in {list,tuple}:
                if len(item) == 3:
                    r,g,b = item
                    my_elements.append(Tinct(RGB=(r,g,b)))
                elif len(item) == 4:
                    r,g,b,a = item
                    my_elements.append(Tinct(RGBA=(r,g,b,a)))
                else:
                    raise TypeError(f'Tincture got a {type(item)} with len {len(item)} in input, but it should be a 3 tuple to interpret as RGB, or a 4 tuple for RGBA')
            else:
                raise TypeError(f'Tincture got a {type(item)} in input. Expected value of Tinct, Tincture, a 3-tuple representing RGB, or a 4-tuple representing RGBA')
            
        self.elements = my_elements
        if positions:
            self.update_positions(positions)
        else:
            self.set_default_positions()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    tincture utils    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def update_positions(self,positions:list[float]):
        """Set positions for stored Tincts to the provided list of positions.
        Stored Tincts will also be sorted by position."""
        if len(positions) != len(self.elements):
            raise ValueError(f'Tincture contains {len(self.elements)} Tincts, but was given {len(positions)} positions.')
        for idx, pos in enumerate(positions):
            self.elements[idx].position = pos
        #sort ourselves
        self.sort_elements()

    def sort_elements(self):
        """Sort elements stored in this tincture. This is required for the retrieval functions to work properly."""
        self.elements = sorted(self.elements,key=lambda x: x.position)

    def set_default_positions(self):
        """Set the position values for stored Tincts to the default, which is a linear mapping of 0-1 based on position in list."""
        num_positions = len(self.elements)
        if num_positions == 1:
            #one position should just be 0, I suppose
            self.elements[0].position = 0.0
        elif num_positions > 0:
            for idx, tinct in enumerate(self.elements):
                fac = idx / (num_positions - 1)
                tinct.position = fac

    def reshape_positions(self):
        """Scale this Tincts position values so that they fit range 0-1."""
        positions = []
        for tinct in self.elements:
            positions.append(tinct.position)
        minimum = min(positions)
        maximum = max(positions)
        new_positions = []
        for pos in positions:
            new_positions.append(map_range(pos,minimum,maximum))
        self.update_positions(new_positions)

    def copy(self) -> 'Tincture':
        """return a copy of this Tincture"""
        return Tincture(colors=self.elements.copy(), blend_mode=self.blend_mode)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    modifying    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add_tinct(self, tinct:Tinct = None, inplace:bool = False, **kwargs):
        """Quickly add Tinct to the Tincture. 
        Params:
         - tinct: pass a Tinct, to add that Tinct to this Tincture
         - inplace: False (default) will return a copy with your specified changes, True will return None and update this Tincture directly
         - **kwargs: instead of passing tinct, you can pass keyword args, which are simply passed on to a new Tinct object
        
        If the Tinct has no position, then it will be added to the end, and the other elements will be automatically reshaped."""
        my_tinct = None
        reshaping = False
        if tinct:
            if type(tinct) == Tinct:
                my_tinct = tinct
            else:
                raise TypeError(f"parameter 'tinct' expects a Tinct object, but got {type(tinct)}")
        if kwargs:
            my_tinct = Tinct(**kwargs)
        if my_tinct == None:
            raise TypeError("add_tinct needs to be given a Tinct to add (got None)")
        
        if my_tinct.position == None:
            reshaping = True
            #figure out where to put new element, based on previous elements location. This will be >1 to start, but fixed later.
            location = 1 + (1 / max(len(self.elements), 1))
            my_tinct.position = location
        

        if inplace:
            self.elements.append(my_tinct)
            if reshaping:
                self.reshape_positions()
            else:
                self.sort_elements()
            return None
        else:        
            new_elements = self.elements.copy()
            new_elements.append(my_tinct)
            #make a copy to do operations on
            new_tincture = self.copy()
            new_tincture.elements = new_elements
            if reshaping:
                new_tincture.reshape_positions()
            else:
                new_tincture.sort_elements()
            return new_tincture


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    retrieval    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def sample(self, location):
        """Pick a color from the Tincture based on the specified position."""
        positions = []
        for tinct in self.elements:
            positions.append(tinct.position)

        # for starters, if the tincture has len 0, we can just return None
        if len(self.elements) == 0:
            return None
        #if len is 1, theres only one color to return, so do it
        elif len(self.elements) == 1:
            return self.elements[0]
        
        #if we passed both checks above, we have at least 2 elements, and we should select from them. 
        #use binary search to find where our location value falls compared to positions of the Tincts
        idx_low, idx_high = binary_search(positions, location)
        #if either values are empty, it means our location is outside of the range of self.elements[].position
        if idx_low == None:
            return self.elements[idx_high]
        elif idx_high == None:
            return self.elements[idx_low]
        #if neither check above passed, then we have two Tincts to sample from. 
        
        #lets figure out what positions our Tincts sit at
        pos_low = self.elements[idx_low].position
        pos_high = self.elements[idx_high].position
        #to use the built in blend function, we need to scale the position and location values from whatever they are now, to a range of 0-1

        #represents relative location between pos_low as 0, and pos_high as 1
        location_factor = map_range(location, pos_low, pos_high, 0, 1)

        #check our blend mode! 
        ease = (self.blend_mode == 'ease')
        if self.blend_mode == 'auto':
            #auto should use linear if we have len 3 or less.
            # but if we have more, then outer edges should be linear, others should be ease
            if len(self.elements) > 3 and (idx_low > 0 and idx_high < (len(self.elements) - 1)):
                ease = True

        #now lets simply sample from our range using the blend function, and our location factor
        return self.elements[idx_low].blend(self.elements[idx_high], location_factor, ease=ease)
    
    def get_list(self, num_colors, kind:None|str = None) -> list:
        """return a list of colors.
        params: 
         - num_colors: the length of the returned list
         - kind: 'RGB','RGBA','RGB255','HSL','okLab','okLCh','hex', or None.   
           - None will just return a list of Tincts. 
           - Setting a valid type will convert the Tinct's to color representations.
         """
        output = []
        if num_colors == 0:
            return []
        elif num_colors == len(self.elements):
            output = self.elements.copy()
        else:
            for i in range(0,num_colors):
                fac = i / (num_colors - 1)
                output.append(self.sample(fac))
        
        if type(kind) == str:
            if kind.lower() == "rgb":
                tmp_output = []
                for tinct in output:
                    tmp_output.append(tinct.get_RGB())
                output = tmp_output
            elif kind.lower() == "rgba":
                tmp_output = []
                for tinct in output:
                    tmp_output.append(tinct.get_RGBA())
                output = tmp_output
            elif kind.lower() == "rgb565":
                tmp_output = []
                for tinct in output:
                    tmp_output.append(tinct.get_RGB565())
                output = tmp_output
            
        return output

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ dunders: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self):
        return len(self.elements)



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   Testing or demo body:   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == '__main__':
    from lib import st7789fbuf
    from machine import Pin, SPI
    
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
    tincture = Tincture([color_start,color_end])
    
    # get a list of blended colors from the tincture
    color_list = tincture.get_list(10)
    
    
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
