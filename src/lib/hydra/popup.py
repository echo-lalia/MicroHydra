import time
from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput


_MH_DISPLAY_WIDTH = const(320)
_MH_DISPLAY_HEIGHT = const(240)

_DISPLAY_WIDTH_CENTER = const(_MH_DISPLAY_WIDTH//2)
_DISPLAY_HEIGHT_CENTER = const(_MH_DISPLAY_HEIGHT//2)

_FONT_WIDTH = const(8)

_WINDOW_PADDING = const(10)
_WINDOW_WIDTH = const(_MH_DISPLAY_WIDTH - (_WINDOW_PADDING * 2))
_WINDOW_HEIGHT = const(_MH_DISPLAY_HEIGHT - (_WINDOW_PADDING * 2))

_MAX_TEXT_WIDTH = const(_WINDOW_WIDTH // _FONT_WIDTH)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UIOverlay Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UIOverlay:
    def __init__(self):
        """
        UIOverlay aims to provide easy to use methods for displaying themed UI popups, and other Overlays.
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
        self.config = Config()
        self.kb = UserInput()

        self.display = Display()


    def text_entry(self, start_value='', title="Enter text:"):
        """
        Display a popup text entry box.
        Blocks until "enter" key pressed, returning written text.
        """
        return TextEntry(start_text=start_value, title=title, ui_overlay=self).main()
        

    def popup_options(self, options, title=None, shadow=True, extended_border=False):
        """
        Display a popup message with given options.
        Blocks until option selected, returns selection.
        """
        tft = self.display
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
                if key == "UP":
                    cursor_index = (cursor_index - 1) % len(options)
                elif key == "DOWN":
                    cursor_index = (cursor_index + 1) % len(options)
                elif key == "ESC" or key == "BSPC":
                    return None
                elif key == "ENT" or key == "G0":
                    return options[cursor_index]
                
            time.sleep_ms(10)


    def draw_textbox(self, text, x, y, padding=8, shadow=True, extended_border=False):
        """Draw to the display a textbox, centered at x,y"""
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
        PopupText(text, self).main()

        
    def error(self,text):
        """
        Display a popup error message with given text.
        Blocks until any button is pressed.
        """
        PopupError(text, self).main()
            
            
            
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Popup Objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class PopupObject:
    """Root popup class"""
    def __init__(self, ui_overlay:UIOverlay):
        self.config = ui_overlay.config
        self.kb = ui_overlay.kb
        self.display = ui_overlay.display


    @staticmethod
    def split_lines(text:str, max_length:int=_MAX_TEXT_WIDTH) -> list[str]:
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
    
    
    def draw_text_box(self, text, clr_idx=8, bg_clr=1, title=None, min_width=0, min_height=0):
        """
        Draw a text box, with optional title and minimum sizes.
        Returns a tuple of box width/height (for tracking minimum width/height)
        """
        lines = self.split_lines(text)
        
        if title: # add title before text
            lines = [title, ''] + lines
        
        box_height = max((len(lines) * 10) + 8, min_height)
        box_width = max((len(max(lines, key=len)) * 8) + 8, min_width)
        box_x = _DISPLAY_WIDTH_CENTER - (box_width // 2)
        box_y = _DISPLAY_HEIGHT_CENTER - (box_height // 2)
        
        # draw box
        for i in range(4):
            self.display.rect(
                box_x - i, box_y - i,
                box_width + i*2, box_height + i*2,
                self.config.palette[i + (bg_clr if i == 0 else 1)],
                fill = (i == 0),
                )
        
        for idx, line in enumerate(lines):
            centered_x = _DISPLAY_WIDTH_CENTER - (len(line) * 4)
            self.display.text(line, centered_x, box_y + 4 + (idx*10), self.config.palette[clr_idx])
        
        return box_width, box_height


class PopupText(PopupObject):
    """Pop up message box."""
    def __init__(self, text, ui_overlay:UIOverlay):
        self.text = text
        super().__init__(ui_overlay)


    def main(self):
        """Main program in PopupObject"""
        self.draw_text_box(self.text, clr_idx=8)
        self.display.show()
            
        time.sleep_ms(200) # stops it from being accidentally closed
        self.kb.get_new_keys() # run once to update keys
        while True:
            if self.kb.get_new_keys(): # any key closes text box
                return


class PopupError(PopupObject):
    """Pop up message box."""
    def __init__(self, text, ui_overlay:UIOverlay):
        self.text = str(text)
        super().__init__(ui_overlay)


    def main(self):
        """Main program in PopupObject"""
        self.draw_text_box(self.text, clr_idx=11, bg_clr=0, title="ERROR:")
        self.display.show()
            
        time.sleep_ms(200) # stops it from being accidentally closed
        self.kb.get_new_keys() # run once to update keys
        while True:
            if self.kb.get_new_keys(): # any key closes text box
                return


class TextEntry(PopupObject):
    """Pop up message box."""
    def __init__(self, start_text, title, ui_overlay:UIOverlay):
        self.start_text = start_text
        self.text = start_text
        self.title = title
        self.max_width = 0
        self.max_height = 0
        super().__init__(ui_overlay)


    def draw(self):
        w, h = self.draw_text_box(
            # simple blinking cursor:
            text=self.text + ("|"if time.ticks_ms() % 1000 < 500 else ":"),
            title=self.title,
            min_width=self.max_width,
            min_height=self.max_height,
            )
        if w > self.max_width:
            self.max_width = w
        if h > self.max_height:
            self.max_height = h
        self.display.show()


    def main(self):
        """
        Display a popup text entry box.
        Blocks until "enter" key pressed, returning written text.
        """
        self.draw()
        
        draw_time = time.ticks_ms()
        
        while True:
            keys = self.kb.get_new_keys()
            
            for key in keys:
                if key == "SPC":
                    self.text += " "
                elif key == "BSPC":
                    self.text = self.text[:-1]
                elif key == "ENT":
                    return self.text
                elif key == "ESC":
                    return self.start_text
                elif key == "DEL":
                    self.text = ''
                elif len(key) == 1:
                    self.text += key
    
            time_now = time.ticks_ms()
            if keys or time.ticks_diff(time_now, draw_time) > 500:
                self.draw()
                draw_time = time_now
            else:
                time.sleep_ms(10)



if __name__ == "__main__":
    # just for testing
    from lib import display, keyboard
    from lib.hydra.config import Config

    tft = Display()

    overlay = UIOverlay()
    
    overlay.popup("WHAT? (this is a test!)")
    
    print(overlay.text_entry("Hello, world!", title="test:"))
    print("DONE")

#     # popup demo:
#     tft.fill(0)
#     #tft.show()
#     time.sleep(0.5)
# 
#     choices = ("popup", "error", "palette", "enter_text")
#     choice = overlay.popup_options(choices, title="Choose demo:")
#     if choice == "popup":
#         tft.fill(0)
#         #tft.show()
#         overlay.popup("Lorem ipsum is placeholder text commonly used in the graphic, print, and publishing industries for previewing layouts and visual mockups.")
#     elif choice == "error":
#         tft.fill(0)
#         #tft.show()
#         overlay.error("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
#     elif choice == "palette":
#         tft.fill(0)
#         #tft.show()
#         # color palette
#         bar_width = 240 // len(config.palette)
#         for i in range(0,len(config.palette)):
#             tft.fill_rect(bar_width*i, 0, bar_width, 135, config.palette[i])
#     elif choice == "enter_text":
#         tft.fill(0)
#         print(overlay.text_entry(start_value="Demo!"))
#         
#     config.save() # this should do nothing
#     
#     
#     tft.fill(0)
    #tft.show()

