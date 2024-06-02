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
    
    def text_entry(self, start_value='', title="Enter text:", blackout_bg=False):
        """
        Display a popup text entry box.
        Blocks until "enter" key pressed, returning written text.
        """
        tft = self.display
        # draw background
        if blackout_bg:
            tft.fill_rect(10,10,220,115,self.config.palette[1])
        self.draw_textbox(title, x=120, y=10)
            
        prev_text = None
        current_text = start_value
        max_lines = 0 # this is used to remember the largest size of text box, to clear the whole thing
        
        while True:
            if prev_text != current_text:
                prev_text = current_text
                # draw text
                # split string into list of lines to display
                lines = self.split_lines(current_text, max_length=26)
                if len(lines) > max_lines:
                    max_lines = len(lines)
                #tft.fill_rect(4,26,232,104,self.config.palette[2])
                if self.compatibility_mode:
                    # draw box
                    box_height = (max_lines*16)
                    box_y = 78 - (box_height//2)
                    
                    tft.fill_rect(4,box_y,232,box_height, self.config.palette[2])
                    
                    start_y = 78 - (len(lines)*8)
                    for idx, line in enumerate(lines):
                        tft.text(self.font, line, 8, start_y + (16*idx), self.config.palette[5], self.config.palette[2])
                    tft.rect(4, box_y, 232, box_height, self.config.palette[3])
                else:
                    # draw box
                    box_height = (max_lines*10) + 8
                    box_y = 78 - (box_height//2)

                    tft.fill_rect(4,box_y,232,box_height, self.config.palette[2])
                    
                    start_y = 78 - (len(lines)*5)
                    for idx, line in enumerate(lines):
                        tft.text(line, 8, start_y + (10*idx), self.config.palette[5])
                    tft.rect(4, box_y, 232, box_height, self.config.palette[3])
                    tft.show()
                    
            keys = self.kb.get_new_keys()
            for key in keys:
                if key == "SPC":
                    current_text += " "
                elif key == "BSPC":
                    current_text = current_text[:len(current_text)-1]
                elif key == "ENT":
                    return current_text
                elif key == "ESC":
                    return start_value
                elif key == "DEL":
                    current_text = ''
                elif len(key) == 1:
                    current_text += key
            
            
            time.sleep_ms(10)
        

    def popup_options(self, options, title=None, shadow=True, extended_border=False):
        """
        Display a popup message with given options.
        Blocks until option selected, returns selection.
        """
        tft = self.display
        if self.compatibility_mode:
            # draw box
            box_height = (len(options) * 16) + 8
            box_width = (len(max(options, key=len)) * 8) + 8
            box_x = 120 - (box_width // 2)
            box_y = 67 - (box_height // 2)
            if extended_border:
                tft.fill_rect(max(box_x - 20,0), max(box_y - 10,0), min(box_width + 40,240), min(box_height + 20,135), self.config.palette[1])
            if title:
                self.draw_textbox(title, 120, box_y - 16, shadow=shadow, extended_border=extended_border)
        else:
            # draw box
            box_height = (len(options) * 10) + 8
            box_width = (len(max(options, key=len)) * 8) + 8
            box_x = 120 - (box_width // 2)
            box_y = 67 - (box_height // 2)
            if extended_border:
                tft.fill_rect(max(box_x - 20,0), max(box_y - 10,0), min(box_width + 40,240), min(box_height + 20,135), self.config.palette[1])
            if title:
                self.draw_textbox(title, 120, box_y - 14, shadow=shadow, extended_border=extended_border)
            
        prev_cursor_index = -1
        cursor_index = 0
        keys = self.kb.get_new_keys()
        while True:
            if prev_cursor_index != cursor_index:
                prev_cursor_index = cursor_index # this logic is only really needed for compatibility mode
                if self.compatibility_mode:
                    # draw box
                    if shadow:
                        tft.fill_rect(box_x + 6, box_y + 6, box_width, box_height, self.config.palette[0])
                    tft.rect(box_x - 2, box_y - 2, box_width + 4, box_height + 4, self.config.palette[0])
                    tft.rect(box_x - 1, box_y - 1, box_width + 2, box_height + 2, self.config.palette[1])
                    tft.fill_rect(box_x, box_y, box_width, box_height, self.config.palette[2])
                    # draw options
                    for idx, option in enumerate(options):
                        if idx == cursor_index:
                            tft.fill_rect(box_x, box_y + 4 + (idx*16), box_width, 16, self.config.palette[0])
                            tft.text(self.font, option, 120 - (len(option) * 4), box_y + 4 + idx* 16, self.config.palette[5], self.config.palette[0])
                        else:
                            tft.text(self.font, option, 120 - (len(option) * 4), box_y + 4 + idx* 16, self.config.palette[4], self.config.palette[2])
                else:
                    # draw box
                    if shadow:
                        tft.rect(box_x + 6, box_y + 6, box_width, box_height, self.config.palette[0], fill=True)
                    tft.rect(box_x - 2, box_y - 2, box_width + 4, box_height + 4, self.config.palette[0], fill=False)
                    tft.rect(box_x - 1, box_y - 1, box_width + 2, box_height + 2, self.config.palette[1], fill=False)
                    tft.rect(box_x, box_y, box_width, box_height, self.config.palette[2], fill=True)
                    # draw options
                    for idx, option in enumerate(options):
                        if idx == cursor_index:
                            tft.rect(box_x, box_y + 3 + (idx*10), box_width, 10, self.config.palette[0], fill=True)
                            tft.text(option, 120 - (len(option) * 4), box_y + 4 + idx* 10, self.config.palette[5])
                        else:
                            tft.text(option, 120 - (len(option) * 4), box_y + 4 + idx* 10, self.config.palette[4])
                    tft.show()
                        
            keys = self.kb.get_new_keys()
            for key in keys:
                if key == ";":
                    cursor_index = (cursor_index - 1) % len(options)
                elif key == ".":
                    cursor_index = (cursor_index + 1) % len(options)
                elif key == "`" or key == "ESC" or key == "BSPC":
                    return None
                elif key == "ENT" or key == "GO":
                    return options[cursor_index]
                
            time.sleep_ms(10)
            
    def draw_textbox(self, text, x, y, padding=8, shadow=True, extended_border=False):
        """Draw to the display a textbox, centered at x,y"""
        if self.compatibility_mode:
            x = x - (len(text) * 4)
            y = y - 8
            box_width = (len(text) * 8) + padding
            box_height = padding + 16
            if extended_border:
                self.display.fill_rect(x - (padding // 2) - 20, y - (padding // 2) -10, box_width + 40, box_height + 20, self.config.palette[1])

            if shadow:
                self.display.fill_rect(x - (padding // 2) + 4, y - (padding // 2) + 4, box_width, box_height, self.config.palette[0])
            
            self.display.fill_rect(x - (padding // 2), y - (padding // 2), box_width, box_height, self.config.palette[2])
            self.display.rect(x - (padding // 2), y - (padding // 2), box_width, box_height, self.config.palette[0])
            self.display.text(self.font, text, x,y,self.config.palette[4], self.config.palette[2])
        else:
            x = x - (len(text) * 4)
            y = y - 4
            box_width = (len(text) * 8) + padding
            box_height = padding + 8
            if extended_border:
                self.display.fill_rect(x - (padding // 2) - 20, y - (padding // 2) -10, box_width + 40, box_height + 20, self.config.palette[1])
            if shadow:
                self.display.rect(x - (padding // 2) + 4, y - (padding // 2) + 4, box_width, box_height, self.config.palette[0], fill=True)
            self.display.rect(x - (padding // 2), y - (padding // 2), box_width, box_height, self.config.palette[2], fill=True)
            self.display.rect(x - (padding // 2), y - (padding // 2), box_width, box_height, self.config.palette[0])
            self.display.text(text, x,y,self.config.palette[4])
        
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
        if type(text) != str:
            text = str(text)
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
    from lib import st7789py, keyboard
    from lib.mhconfig import Config
    from machine import Pin, SPI

    tft = st7789py.ST7789(
        SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
        135,
        240,
        reset=Pin(33, Pin.OUT),
        cs=Pin(37, Pin.OUT),
        dc=Pin(34, Pin.OUT),
        backlight=Pin(38, Pin.OUT),
        rotation=1,
        color_order=st7789py.BGR,
        #reserved_bytearray=reserved_bytearray
        )
    
    kb = keyboard.KeyBoard()
    config = Config()
    overlay = UI_Overlay(config=config, keyboard=kb, display_py=tft)

    # popup demo:
    tft.fill(0)
    #tft.show()
    time.sleep(0.5)
    
    choices = ("popup", "error", "palette", "enter_text")
    choice = overlay.popup_options(choices, title="Choose demo:")
    if choice == "popup":
        tft.fill(0)
        #tft.show()
        overlay.popup("Lorem ipsum is placeholder text commonly used in the graphic, print, and publishing industries for previewing layouts and visual mockups.")
    elif choice == "error":
        tft.fill(0)
        #tft.show()
        overlay.error("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
    elif choice == "palette":
        tft.fill(0)
        #tft.show()
        # color palette
        bar_width = 240 // len(config.palette)
        for i in range(0,len(config.palette)):
            tft.fill_rect(bar_width*i, 0, bar_width, 135, config.palette[i])
    elif choice == "enter_text":
        tft.fill(0)
        print(overlay.text_entry(start_value="Demo!"))
        
    config.save() # this should do nothing
    
    
    tft.fill(0)
    #tft.show()
