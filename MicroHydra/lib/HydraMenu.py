import math
from lib import microhydra as mh

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_WIDTH = const(240)
_DISPLAY_HEIGHT = const(135)

_SCROLLBAR_WIDTH = const(2)
_SCROLLBAR_X = const(_DISPLAY_WIDTH-_SCROLLBAR_WIDTH)

_FONT_HEIGHT = const(32)

_PER_PAGE = const(_DISPLAY_HEIGHT//_FONT_HEIGHT)
_Y_PADDING = const( (_DISPLAY_HEIGHT - (_PER_PAGE*_FONT_HEIGHT)) // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# global config will provide default stylings
CONFIG = None
FONT = None

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MENU ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Menu:
    def __init__(self,
                 display_fbuf,
                 config = None,
                 font = None,
                 sound = None,
                 per_page:int = _PER_PAGE,
                 y_padding:int = _Y_PADDING
                 ):
        """
        args:
        - display_fbuf (ST7789): st7789fbuf ST7789 object
        - font (module): bitmap font module
        - sound (M5Sound): M5Sound M5Sound object
        - per_page (int): menu items per page
        - y_padding (int): y padding
        """
        # init global font and config
        global FONT, CONFIG
        
        if font:
            FONT = font
        else:
            from font import vga2_16x32
            FONT = vga2_16x32
            
        if config:
            CONFIG = config
        else:
            from lib import mhconfig
            CONFIG = mhconfig.Config()
        
        self.display = display_fbuf
        self.items = []
        self.cursor_index = 0
        self.prev_cursor_index = 0
        self.setting_screen_index = 0
        self.per_page = per_page
        self.y_padding = y_padding
        self.in_submenu = False
        
        self.sound = sound
    
    def append(self, item):
        self.items.append(item)

    def display_menu(self):
        if self.cursor_index >= self.setting_screen_index + self.per_page:
            self.setting_screen_index += self.cursor_index - (self.setting_screen_index + (self.per_page - 1))

        elif self.cursor_index < self.setting_screen_index:
            self.setting_screen_index -= self.setting_screen_index - self.cursor_index
        
        self.display.fill(CONFIG['bg_color'])
        
        visible_items = self.items[self.setting_screen_index:self.setting_screen_index+self.per_page]
        
        for i in range(self.setting_screen_index, self.setting_screen_index + self.per_page):
            y = self.y_padding + (i - self.setting_screen_index) * FONT.HEIGHT
            if i <= len(self.items) - 1:
                if i == self.cursor_index:
                    self.items[i].selected = 1
                    self.items[i].y_pos = y
                    self.items[i].draw()
                else:
                    self.items[i].selected = 0
                    self.items[i].y_pos = y
                    self.items[i].draw()
            self.display.hline(0, y, _DISPLAY_WIDTH, CONFIG.palette[3])# separation lines
        self.display.hline(0, y + FONT.HEIGHT, _DISPLAY_WIDTH, CONFIG.palette[3])# separation lines

    def update_scroll_bar(self):
        max_screen_index = len(self.items) - self.per_page
        scrollbar_height = _DISPLAY_HEIGHT // max_screen_index
        scrollbar_position = math.floor((_DISPLAY_HEIGHT - scrollbar_height) * (self.cursor_index / max_screen_index))
        
        self.display.fill_rect(_SCROLLBAR_X, 0, _SCROLLBAR_WIDTH, _DISPLAY_HEIGHT, CONFIG['bg_color'])
        self.display.fill_rect(_SCROLLBAR_X, scrollbar_position, _SCROLLBAR_WIDTH, scrollbar_height, CONFIG.palette[3])

    def handle_input(self, key):
        if self.in_submenu:
            self.items[self.cursor_index].handle_input(key)
        
        elif key == 'UP' or key == ';':
            self.cursor_index = (self.cursor_index - 1) % len(self.items)
            
            #if self.ui_sound:
            #    self.beep.play(("E3","C3"), 100, CONFIG['volume'])
            self.display_menu()

        elif key == 'DOWN' or key == '.':
            self.cursor_index = (self.cursor_index + 1) % len(self.items)
            
            #if CONFIG['ui_sound']:
            #    self.beep.play(("D3","C3"), 100, CONFIG['volume'])
            self.display_menu()
        
        elif key == 'GO' or key == 'ENT':
            return (self.items[self.cursor_index].handle_input("GO"))

class bool_item:
    def __init__(self, menu, text: str = None, BOOL: bool = False, x_pos: int = 0, y_pos: int = 0, selected: bool = False, callback: callable = None):
        self.BOOL = BOOL
        self.menu = menu
        self.selected = selected
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.callback = callback        
    
    def draw(self):
        draw_left_text(self.menu, self.text, self.y_pos, self.selected)
        draw_right_text(self.menu, str(self.BOOL), self.y_pos)
        self.menu.display.hline(0, self.y_pos, _DISPLAY_WIDTH, CONFIG.palette[3])

    def handle_input(self, key):
        if (key == "GO" or key == "ENT"):
            self.BOOL = not self.BOOL
            #self.menu.beep.play((("C3","E3","D3"),"D4","C4"), 100, CONFIG['volume'])
            self.draw()
            if self.callback != None:
                self.callback(self, self.BOOL)

class RGB_item:
    def __init__(self, menu, text: str = None, items: list = [], x_pos: int = 0, y_pos: int = 0, selected: bool = False, callback: callable = None):
        self.cursor_index = 0
        self.menu = menu
        self.text = text
        self.items = items
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.selected = selected
        self.rgb_select_index = 0
        self.in_item = False
        self.callback = callback

    def draw(self):
        if self.selected:
            draw_left_text(self.menu, self.text, self.y_pos, self.selected)
        else:
            draw_left_text(self.menu, self.text, self.y_pos, self.selected)
        titel = "{},{},{}".format(self.items[0], self.items[1], self.items[2])
        draw_right_text(self.menu, str(titel), self.y_pos)
        self.menu.display.hline(0, self.y_pos, _DISPLAY_WIDTH, CONFIG.palette[3])
    
    def draw_rgb_win(self):
        win = pop_up_win(self.menu.display, self.text, CONFIG['ui_color'], CONFIG['bg_color'])
        win.draw()
        color = [63488, 2016, 31]
        rgb_text = ["R/31", "G/63", "B/31"]
        for i, item in enumerate(self.items):
            x = int(222/2 * (i * 0.5)) + int(222 / 5) #this needs to be looked at
            y = int(20 + FONT.HEIGHT + 5)
            if i == self.cursor_index:
                self.menu.display.bitmap_text(FONT, str(item), x, y + FONT.HEIGHT, 16777215)#, 0)
            else:
                self.menu.display.bitmap_text(FONT, str(item), x, y + FONT.HEIGHT, 16777215)#, CONFIG['bg_color'])
            self.menu.display.bitmap_text(FONT, str(rgb_text[i]), x, y, color[i])#, CONFIG['bg_color'])
            
            # draw pointer
        for i in range(0,16):
            self.menu.display.hline(
                x = (78 - i) + (44 * self.cursor_index),
                y = 94 + i,
                length = 2 + (i*2),
                color = mh.combine_color565(self.items[0],self.items[1],self.items[2]))
            self.menu.display.fill_rect(62 + (44 * self.cursor_index), 110, 34, 8, mh.combine_color565(self.items[0],self.items[1],self.items[2]))
        
        
    
    def handle_input(self, key):
        max_range = [31, 63, 31]
        self.menu.in_submenu = True
        if (key == 'RIGHT' or key == "/"):
            self.cursor_index += 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("D3","C3"), 100, self.menu.volume)
            if self.cursor_index >= len(self.items):
                self.cursor_index = 0
                
        elif (key == "LEFT" or key == ","):
            self.cursor_index -= 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("E3","C3"), 100, self.menu.volume)
            if self.cursor_index < 0:
                self.cursor_index = len(self.items) - 1
                
        elif (key == "UP" or key == ";"):
            self.items[self.cursor_index] += 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("C3","A3"), 80, self.menu.volume)
            if self.items[self.cursor_index] > max_range[self.cursor_index]:
                self.items[self.cursor_index] = 0
                
        elif (key == "DOWN" or key == "."):
            self.items[self.cursor_index] -= 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("C3","A3"), 80, self.menu.volume)
            if self.items[self.cursor_index] < 0:
                self.items[self.cursor_index] = max_range[self.cursor_index]
                
        elif (key == "GO" or key == "ENT") and self.in_item != False:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, self.items)
                #self.menu.beep.play(("C4","D4","E4"), 50, self.menu.volume)
            return
            
        self.in_item = True
        self.draw_rgb_win()

class do_item:
    def __init__(self, menu, text: str = None, x_pos: int = 0, y_pos: int = 0, selected: bool = False, callback: callable = None):
        self.menu = menu
        self.selected = selected
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.callback = callback

    def draw(self):
        if self.selected:
            TEXT = "< {} >".format(self.text)
            self.menu.display.bitmap_text(FONT, TEXT, int(_DISPLAY_WIDTH / 2) - get_text_center(TEXT, FONT), self.y_pos, CONFIG['ui_color'])#, CONFIG.palette[3])
        else:
            self.menu.display.bitmap_text(FONT, self.text, int(_DISPLAY_WIDTH / 2) - get_text_center(self.text, FONT), self.y_pos, CONFIG['ui_color'])#, CONFIG['bg_color'])
        
    def handle_input(self, key):
        if self.callback != None:
            self.callback(self)
            #self.menu.beep.play(("C4","D4","E4"), 50, self.menu.volume)

class int_select_item:
    def __init__(self, menu, init_int, min_int, max_int, text: str = None, x_pos: int = 0, y_pos: int = 0, selected: bool = False, callback: callable = None):
        self.menu = menu
        self.selected = selected
        self.current_value = init_int
        self.min_int = min_int
        self.max_int = max_int
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.in_item = False
        self.callback = callback
    
    def draw(self):
        draw_left_text(self.menu, self.text, self.y_pos, self.selected)
        draw_right_text(self.menu, str(self.current_value), self.y_pos)
    
    def draw_win(self):
        win = pop_up_win(self.menu.display, self.text, CONFIG['ui_color'], CONFIG['bg_color'])
        win.draw()
        for i in range(0,8):
            self.menu.display.hline(
                x = (119 - i),
                y = 60 + i,
                length = 2 + (i*2),
                color = CONFIG['ui_color'])
            self.menu.display.hline(
                x = (119 - i),
                y = 116 - i,
                length = 2 + (i*2),
                color = CONFIG['ui_color'])
        x = 112 - ((self.current_value == 10) * 8)
        if self.current_value < 0:
            x = 112 - ((self.current_value == 10) * 8) - FONT.WIDTH
        self.menu.display.bitmap_text(FONT, str(self.current_value), x, 75, CONFIG['ui_color'])#, CONFIG['bg_color'])
    
    def handle_input(self, key):
        self.menu.in_submenu = True
        if (key == "UP" or key == ";"):
            self.current_value += 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("C3","A3"), 80, self.menu.volume)
            if self.current_value > self.max_int:
                self.current_value = self.min_int
                
        elif (key == "DOWN" or key == "."):
            self.current_value -= 1
            #if self.menu.ui_sound:
            #    self.menu.beep.play(("C3","A3"), 80, self.menu.volume)
            if self.current_value < self.min_int:
                self.current_value = self.max_int
                
        elif (key == "GO" or key == "ENT") and self.in_item != False:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, self.current_value)
                #self.menu.beep.play(("C4","D4","E4"), 50, self.menu.volume)
            return
            
        self.in_item = True
        self.draw_win()

class write_item:
    def __init__(self, menu, text: str = None, show_text: str = None, hide: bool = False, x_pos: int = 0, y_pos: int = 0, selected: bool = False, callback: callable = None):
        self.menu = menu
        self.text = text
        self.show_text = show_text
        self.hide = hide
        self.selected = selected
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.in_item = False
        self.callback = callback

    def draw(self):
        draw_left_text(self.menu, self.text, self.y_pos, self.selected)    
        if self.hide:
            draw_right_text(self.menu, str("****"), self.y_pos)
        else:
            draw_right_text(self.menu, str(self.show_text), self.y_pos)     

    def draw_win(self):
        win = pop_up_win(self.menu.display, self.text, CONFIG['ui_color'], CONFIG['bg_color'])
        win.draw()
        draw_text_on_win(self.menu, self.show_text, 75)
    
    def handle_input(self, key):
        self.menu.in_submenu = True
        if (key == "GO" or key == "ENT") and self.in_item != False:
            self.menu.in_submenu = False
            self.in_item = False
            self.menu.display_menu()
            if self.callback != None:
                self.callback(self, self.show_text)
                #self.menu.beep.play(("C4","D4","E4"), 50, self.menu.volume)
            return
        
        elif key == "SPC":
            self.show_text += " "
        elif len(key) == 1:
            self.show_text += str(key)
        elif key == "BSPC":
            self.show_text = self.show_text[:-1]
        self.in_item = True
        self.draw_win()


class pop_up_win:
    def __init__(self, display, text: str = None, ui_color: int = 53243, bg_color: int = 4421):
        self.display = display
        self.text = text
    
    def draw(self):
        self.display.fill_rect(10, 10, 220, 115, CONFIG['bg_color'])
        self.display.rect(9, 9, 222, 117, CONFIG['ui_color'])
        self.display.hline(10, 126, 222, 0)
        self.display.hline(11, 127, 222, 0)
        self.display.hline(12, 128, 222, 0)
        self.display.hline(13, 129, 222, 0)
        self.display.vline(231, 10, 117, 0)
        self.display.vline(232, 11, 117, 0)
        self.display.vline(233, 12, 117, 0)
        self.display.vline(234, 13, 117, 0)
        if self.text:
            center_x = int(222/2) - get_text_center(self.text, FONT)
            self.display.bitmap_text(FONT, str(self.text + ":"), center_x, 20, CONFIG['ui_color'])

def get_text_center(text:str, font):
    center = int((len(text) * font.WIDTH) // 2)
    return (center)

def draw_left_text(menu, text:str, y_pos:int, selected):
    if selected:
        menu.display.bitmap_text(FONT, '>', 0, y_pos, CONFIG['ui_color'])
        menu.display.bitmap_text(FONT, text, 15, y_pos, CONFIG['ui_color'])
    else:
        menu.display.bitmap_text(FONT, ' ', 0, y_pos, CONFIG['ui_color'])
        menu.display.bitmap_text(FONT, text, 15, y_pos, CONFIG['ui_color'])

def draw_right_text(menu, text:str, y_pos:int):
    menu.display.fill_rect(160, y_pos, 80, 8, CONFIG['bg_color'])# clear word
    x = menu.display.width - 40 - (len(text)*4)
    color = mh.mix_color565(CONFIG['ui_color'], CONFIG['bg_color'])
    if len(text) * 4 > 80:
         x = (int(menu.display.width / 2) + 40)
    menu.display.text(str(text), x, y_pos, color)#, CONFIG['bg_color'])

def draw_text_on_win(menu, text:str, y_pos:int):
    if len(text) > int(222 / FONT.WIDTH):
        menu.display.bitmap_text(FONT, text[0:int(222 / FONT.WIDTH)], int(menu.display.width / 2) - get_text_center(text[0:int(222 / FONT.WIDTH)], FONT), 85-FONT.HEIGHT, CONFIG['ui_color'])#, CONFIG['bg_color'])
        menu.display.bitmap_text(FONT, text[int(222 / FONT.WIDTH):len(text)], int(menu.display.width / 2) - get_text_center(text[int(222 / FONT.WIDTH):len(text)], FONT), 85, CONFIG['ui_color'])#, CONFIG['bg_color'])
    else:
        menu.display.bitmap_text(FONT, text, int(menu.display.width / 2) - get_text_center(text, FONT), 75, CONFIG['ui_color'])
