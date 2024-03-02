import time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UI_Overlay Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UI_Overlay:
    def __init__(self, config, keyboard, display_fbuf=None, display_py=None):
        """
        UI_Overlay aims to provide easy to use methods for displaying themed UI popups, and other Overlays.
        params:
            config:Config
                - A 'lib.mhconfig.Config' object.
                
            keyboard:KeyBoard
                - A 'KeyBoard' object from lib.keyboard
                
            display_fbuf:ST7789
            display_py:ST7789
                - An 'ST7789' object from lib.st7789py or lib.st7789fbuf
                - One of them must be supplied. 
        """
        self.config = config
        self.kb = keyboard
        
        # import our display to write to!
        self.compatibility_mode = False # working with st7789fbuf
        if display_fbuf:
            self.display = display_fbuf
        elif display_py:
            from font import vga1_8x16 as font
            self.display = display_py
            self.compatibility_mode = True # for working with st7789py
            self.font = font
        else:
            raise ValueError("UI_Overlay must be initialized with either 'display_fbuf' or 'display_py'.")
    
    @staticmethod
    def split_lines(text, max_length=27):
        """Split a string into multiple lines, based on max line-length."""
        lines = []
        current_line = ''
        words = text.split()

        for word in words:
            if len(word) + len(current_line) >= max_length:
                lines.append(current_line)
                current_line = word
            elif len(current_line) == 0:
                current_line += word
            else:
                current_line += ' ' + word
            
        lines.append(current_line) # add final line
            
        return lines

    def popup(self,text):
        """
        Display a popup message with given text.
        Blocks until any button is pressed.
        """
        # split text into lines
        lines = self.split_lines(text, max_length = 27)
        try:
            if self.compatibility_mode:
                # use the st7789py driver to display popup
                box_height = (len(lines) * 16) + 8
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.fill_rect(box_x, box_y, box_width, box_height, self.config.palette[0])
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.palette[2])
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[3])
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.palette[4])
                
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(self.font, line, centered_x, box_y + 4 + (idx*16), self.config.palette[-1], self.config.palette[0])
            else:
                #use the st7789fbuf driver to display popup
                box_height = (len(lines) * 10) + 8
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.rect(box_x, box_y, box_width, box_height, self.config.palette[0], fill=True)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.palette[2], fill=False)
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[3], fill=False)
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.palette[4], fill=False)
                
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(line, centered_x, box_y + 4 + (idx*10), self.config.palette[-1])
                self.display.show()
                
            time.sleep_ms(200)
            self.kb.get_new_keys() # run once to update keys
            while True:
                if self.kb.get_new_keys():
                    return
        except TypeError as e:
            raise TypeError(f"popup() failed. Double check that 'UI_Overlay' object was initialized with correct keywords: {e}")
        
    def error(self,text):
        """
        Display a popup error message with given text.
        Blocks until any button is pressed.
        """
        # split text into lines
        lines = self.split_lines(text, max_length = 27)
        try:
            if self.compatibility_mode:
                # use the st7789py driver to display popup
                box_height = (len(lines) * 16) + 24
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.fill_rect(box_x, box_y, box_width, box_height, 0)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.rgb_colors[0])
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[0])
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.rgb_colors[0])
                
                self.display.text(self.font, "ERROR", 100, box_y + 4, self.config.rgb_colors[0])
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(self.font, line, centered_x, box_y + 20 + (idx*16), 65535, 0)
            else:
                #use the st7789fbuf driver to display popup
                box_height = (len(lines) * 10) + 20
                box_width = (len(max(lines, key=len)) * 8) + 8
                box_x = 120 - (box_width // 2)
                box_y = 67 - (box_height // 2)
                
                self.display.rect(box_x, box_y, box_width, box_height, 0, fill=True)
                self.display.rect(box_x-1, box_y-1, box_width+2, box_height+2, self.config.rgb_colors[0], fill=False)
                self.display.rect(box_x-2, box_y-2, box_width+4, box_height+4, self.config.palette[0], fill=False)
                self.display.rect(box_x-3, box_y-3, box_width+6, box_height+6, self.config.rgb_colors[0], fill=False)
                
                self.display.text("ERROR", 100, box_y + 4, self.config.rgb_colors[0])
                for idx, line in enumerate(lines):
                    centered_x = 120 - (len(line) * 4)
                    self.display.text(line, centered_x, box_y + 16 + (idx*10), 65535)
                self.display.show()
                
            time.sleep_ms(200)
            self.kb.get_new_keys() # run once to update keys
            while True:
                if self.kb.get_new_keys():
                    return
                time.sleep_ms(1)
        except TypeError as e:
            raise TypeError(f"error() failed. Double check that 'UI_Overlay' object was initialized with correct keywords: {e}")
        
        
if __name__ == "__main__":
    # just for testing
    reserved_bytearray = bytearray(240*135*2)
    from lib import st7789fbuf, keyboard
    from lib.mhconfig import Config
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
        color_order=st7789fbuf.BGR,
        reserved_bytearray=reserved_bytearray
        )
    
    kb = keyboard.KeyBoard()
    config = Config()
    overlay = UI_Overlay(config=config, keyboard=kb, display_fbuf=tft)

    # popup demo:
    tft.fill(0)
    tft.show()
    time.sleep(0.5)
    
    overlay.popup("Lorem ipsum is placeholder text commonly used in the graphic, print, and publishing industries for previewing layouts and visual mockups.")
    tft.fill(0)
    tft.show()
    time.sleep(0.5)
    
    overlay.error("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
    tft.fill(0)
    tft.show()
    
    # color palette
    bar_width = 240 // len(config.palette)
    for i in range(0,len(config.palette)):
        tft.fill_rect(bar_width*i, 0, bar_width, 135, config.palette[i])
        
    # extended colors
    bar_width = 240 // len(config.rgb_colors)
    for i in range(0,len(config.rgb_colors)):
        tft.fill_rect(bar_width*i, 0, bar_width, 20, config.rgb_colors[i])
        
    config.save() # this should do nothing
    
    tft.show()
    time.sleep(2)
    tft.fill(0)
    tft.show()
