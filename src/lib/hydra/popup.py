import time
from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput


_MH_DISPLAY_WIDTH = const(320)
_MH_DISPLAY_HEIGHT = const(240)

_DISPLAY_WIDTH_CENTER = const(_MH_DISPLAY_WIDTH//2)
_DISPLAY_HEIGHT_CENTER = const(_MH_DISPLAY_HEIGHT//2)

_FONT_WIDTH = const(8)
_FONT_HEIGHT = const(8)

_WINDOW_PADDING = const(10)
_WINDOW_WIDTH = const(_MH_DISPLAY_WIDTH - (_WINDOW_PADDING * 2))
_WINDOW_HEIGHT = const(_MH_DISPLAY_HEIGHT - (_WINDOW_PADDING * 2))

_MAX_TEXT_WIDTH = const(_WINDOW_WIDTH // _FONT_WIDTH)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UIOverlay Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UIOverlay:
    def __init__(self):
        """
        UIOverlay aims to provide easy to use methods for displaying themed UI popups, and other Overlays.
        """
        self.config = Config()
        self.kb = UserInput.instance if hasattr(UserInput, 'instance') else UserInput()

        # avoid reinitializing display!
        try:
            self.display = Display.instance
        except AttributeError as e:
            raise AttributeError("Display has no instance. (Please initialize Display before UIOverlay)") from e


    def text_entry(self, start_value='', title="Enter text:"):
        """
        Display a popup text entry box.
        Blocks until "enter" key pressed, returning written text.
        """
        return TextEntry(start_text=start_value, title=title, ui_overlay=self).main()


    def popup_options(self, options:list[list], title=None):
        return PopupOptions(options, title=title, ui_overlay=self).main()


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
    
    
    def draw_text_box(
        self,
        text,
        clr_idx=8,
        bg_clr=1,
        title=None,
        min_width=0,
        min_height=0
        ):
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


_OPTION_BOX_HEIGHT = const(12)
_OPTION_Y_PADDING = const((_OPTION_BOX_HEIGHT - _FONT_HEIGHT) // 2)
_OPTION_X_PADDING = const(2)
_OPTION_X_PADDING_TOTAL = const(_OPTION_X_PADDING * 2)
_OPTION_Y_PADDING_TOTAL = const(_OPTION_BOX_HEIGHT - _FONT_HEIGHT)
class PopupOptions(PopupObject):
    """
    Pop up options menu, can be 1D or 2D
    options parameter should be a list of lists, where each list is a separate column
    """
    def __init__(self, options:list[list], title:str|None, ui_overlay:UIOverlay):

        # parse 1-dimensional options into 2d for consistency
        if options and not isinstance(options[0], (list, tuple)):
            options = [options]
        self.options = options
        
        # calculate bg width and height
        self.total_width, self.total_height, self.col_xs = self._find_width_height(options)
        
        self.title = title
        self.cursor_x = 0
        self.cursor_y = 0
        
        super().__init__(ui_overlay)


    @staticmethod
    def _find_width_height(options):
        """Scan given options to find total bg width and height"""

        max_num_options = len(max(options, key=len))
        col_xs = []
        total_width = 0
        for column in options:
            col_text_width = len(max(column, key=len)) * _FONT_WIDTH + (_OPTION_X_PADDING_TOTAL * 2)
            col_xs.append(total_width + (col_text_width // 2))
            total_width += col_text_width
            
        total_height = max_num_options * (_OPTION_BOX_HEIGHT + _OPTION_Y_PADDING_TOTAL)

        return total_width, total_height + _OPTION_Y_PADDING_TOTAL, col_xs
        


    def draw_option_box(self, text, x, y, selected=False):
        box_width = (len(text) * 8) + _OPTION_X_PADDING_TOTAL
        x -= box_width // 2
        y -= _OPTION_BOX_HEIGHT // 2
        
        self.display.rect(
            x, y, box_width, _OPTION_BOX_HEIGHT,
            self.config.palette[6 if selected else 4],
            fill=True)
        self.display.rect(
            x, y, box_width, _OPTION_BOX_HEIGHT,
            self.config.palette[7 if selected else 5]
            )
        self.display.text(
            text, x + _OPTION_X_PADDING, y + _OPTION_Y_PADDING + 1,
            self.config.palette[10 if selected else 6])
    
    
    def draw(self):
        num_columns = len(self.options)
        display_width = self.display.width
        display_height = self.display.height
        
        col_half_width = self.total_width // (num_columns * 2)
        
        
        bg_y = (display_height - self.total_height) // 2
        
         # draw title:
        if self.title is not None:
            title_width = len(self.title) * _FONT_WIDTH
            title_box_width = max(title_width + _OPTION_X_PADDING_TOTAL, self.total_width)
            
            title_x = display_width // 2 - title_width // 2
            title_box_x = display_width // 2 - title_box_width // 2
            title_box_y = bg_y - _OPTION_BOX_HEIGHT - _OPTION_Y_PADDING
            
            self.display.rect(
                title_box_x, title_box_y,
                title_box_width, _OPTION_BOX_HEIGHT + _OPTION_Y_PADDING,
                self.config.palette[3], fill=True)
            self.display.text(
                self.title,
                title_x, title_box_y + _OPTION_Y_PADDING + 1,
                self.config.palette[5],
                )
            self.display.text(
                self.title,
                title_x, title_box_y + _OPTION_Y_PADDING,
                self.config.palette[6],
                )
        else:
            title_box_width = 0

        
        bg_width = max(self.total_width, title_box_width)
        width_delta_offset = (title_box_width - self.total_width) // 2 if title_box_width > self.total_width else 0
        bg_x = (display_width - bg_width) // 2
        
        # draw bg:
        self.display.rect(
            bg_x,
            bg_y,
            bg_width, self.total_height,
            self.config.palette[3],
            fill=True
            )
        
        # draw each column:
        for col_idx, column in enumerate(self.options):
            column_len = len(column)
            column_x = self.col_xs[col_idx]
            option_half_height = self.total_height // (column_len * 2)
            
            for option_idx, option in enumerate(column):
                option_y = (self.total_height * option_idx) // column_len + option_half_height
                self.draw_option_box(
                    option,
                    column_x + bg_x + width_delta_offset,
                    option_y + bg_y,
                    selected=True if col_idx == self.cursor_x and option_idx == self.cursor_y else False,
                    )

        self.display.show()
    
    def _move_cursor_x(self, move):
        """Move cursor left/right, adjusting for varying column lengths"""
        old_col_len = len(self.options[self.cursor_x])
        old_y = self.cursor_y
        self.cursor_x = (self.cursor_x + move) % len(self.options)
        new_col_len = len(self.options[self.cursor_x])
        
        self.cursor_y = min(
            int(round((old_y / old_col_len) * new_col_len)),
            new_col_len - 1
            )
        
    
    def main(self):
        """
        Display a popup options menu.
        Blocks until "enter" key pressed, returning option str.
        """
        self.draw()
        
        draw_time = time.ticks_ms()
        
        while True:
            keys = self.kb.get_new_keys()
            
            for key in keys:
                if key == "RIGHT":
                    self._move_cursor_x(1)
                elif key == "LEFT":
                    self._move_cursor_x(-1)

                elif key == "UP":
                    self.cursor_y = (self.cursor_y - 1) % len(self.options[self.cursor_x])
                elif key == "DOWN":
                    self.cursor_y = (self.cursor_y + 1) % len(self.options[self.cursor_x])

                elif key == "ESC" or key == "BSPC":
                    return None

                elif key == "ENT" or key == "G0":
                    return self.options[self.cursor_x][self.cursor_y]
            
            if keys:
                self.draw()
            else:
                time.sleep_ms(10)
    
    

if __name__ == "__main__":
    # just for testing
    from lib import display
    from lib.hydra.config import Config

    tft = Display()

    overlay = UIOverlay()
    
    tft.fill(Config().palette[2])
    
    print(overlay.popup_options(['1','2','3','4','5']))
    print(overlay.popup_options((
        ["do","re","mi","fa","so"],
        ["la","ti","do"],
        ["this", "is","a","test"],
        ), title="popup options!"))
#     print(overlay.text_entry("Hello, world!", title="test:"))
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


