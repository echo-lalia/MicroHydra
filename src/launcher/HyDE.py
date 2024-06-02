from lib import smartkeyboard, st7789fbuf, mhconfig, mhoverlay
import machine
from machine import Pin, SPI, RTC
from font import vga1_8x16 as font
from lib import microhydra as mh
import os, time, sys
import esp32

# increased freq makes fancy text drawing faster. This may not be necessary if fancytext function is optimized
machine.freq(240_000_000)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_WIDTH = const(240)
_DISPLAY_HEIGHT = const(135)

_HORIZONTAL_CHARACTERS = const((_DISPLAY_WIDTH // 8) - 1)

_DISPLAY_LINES = const(10)
_DISPLAY_PADDING = const(1) # padding between lines

_LEFT_PADDING = const(8)
_LEFT_RULE = const(6)
_INDENT_RULE_OFFSET = const(_LEFT_RULE - _LEFT_PADDING)

_RIGHT_TEXT_FADE = const(_DISPLAY_WIDTH - 8)

_TEXT_HEIGHT = const(16 + _DISPLAY_PADDING)
_SMALL_TEXT_HEIGHT = const(8 + _DISPLAY_PADDING)
_TEXT_HEIGHT_HALF = const(_TEXT_HEIGHT//2)
_SMALL_TEXT_HEIGHT_HALF = const(_SMALL_TEXT_HEIGHT//2)

_CURSOR_BLINK_MS = const(1000)
_CURSOR_BLINK_HALF = const(_CURSOR_BLINK_MS // 2)

_FILE_BROWSER = const("/launcher/files.py")

# arbitrary char classifications as int:
_NONE_CLASS = const(0)
_ALPHA_CLASS = const(7)
_DIGIT_CLASS = const(8)
_DOT_CLASS = const(9)
_SPACE_CLASS = const(1)
_INDENT_CLASS = const(2)
_OTHER_CLASS = const(4)

# rarely used whitespace chars are repurposed to denote converted tab/space indents
_INDENT_SYM = const(' ')
_SPACE_INDENT = const('    ')
_TAB_INDENT = const('	')


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Global Objects: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# sd needs to be mounted for any files in /sd
try:
    sd = machine.SDCard(slot=2, sck=machine.Pin(40), miso=machine.Pin(39), mosi=machine.Pin(14), cs=machine.Pin(12))
    os.mount(sd, '/sd')
except OSError:
    print("Could not mount SDCard!")

DISPLAY = st7789fbuf.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

RTC = machine.RTC()
CONFIG = mhconfig.Config()
KB = smartkeyboard.KeyBoard(config=CONFIG, use_sys_commands = False)
NVS = esp32.NVS("HyDE")

# load config option to use tabs/spaces
USE_TABS = False



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Generate color palette: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def shift_color565_hue(color, shift):
    """shift the hue of a color565 to the right and left. this is useful for generating complimentary colors."""
    r,g,b = mhconfig.separate_color565(color)

    r /= 31; g /= 63; b /= 31

    h,s,v = mhconfig.rgb_to_hsv(r,g,b)

    r,g,b = mhconfig.hsv_to_rgb(h+shift,s,v)

    r = int(r*31); g = int(g*63); b = int(b*31)

    clr = mhconfig.combine_color565(r,g,b)

    return clr

STR_COLOR = shift_color565_hue(CONFIG.palette[5], -0.4)
DARK_STR_COLOR = shift_color565_hue(CONFIG.palette[3], -0.2)

NUM_COLOR = shift_color565_hue(
    mhconfig.mix_color565(CONFIG.palette[1], CONFIG.palette[5], mix_factor=0.95, hue_mix_fac=0, sat_mix_fac=0.95),
    -0.15
    )

OP_COLOR = mhconfig.mix_color565(
    CONFIG.palette[1], CONFIG.palette[5], mix_factor=0.9, hue_mix_fac=0.7, sat_mix_fac=0.8
    )

KEYWORD_COLOR = mhconfig.mix_color565(
    CONFIG.palette[1], CONFIG.palette[5], mix_factor=1, hue_mix_fac=0.3, sat_mix_fac=0.7
    )

COMMENT_COLOR = mhconfig.mix_color565(
    CONFIG.palette[1], CONFIG.palette[5], mix_factor=0.5, hue_mix_fac=0, sat_mix_fac=0.1
    )

DARK_COMMENT_COLOR = mhconfig.mix_color565(
    CONFIG.palette[1], CONFIG.palette[5], mix_factor=0.25, hue_mix_fac=0, sat_mix_fac=0.1
    )




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function defs: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def file_options(target_file,overlay,editor):
    """Give file options menu"""
    _OPTIONS = const(("Back", "Save", "Tab...", "Run...", "Exit..."))

    choice = overlay.popup_options(_OPTIONS,title="GO...")

    if choice == "Back":
        return
    elif choice == "Save":
        editor.save_file(target_file)
    elif choice == "Run...":
        run_options(target_file,overlay,editor)
    elif choice == "Exit...":
        exit_options(target_file,overlay,editor)
    elif choice == "Tab...":
        tab_options(target_file,overlay,editor)

def tab_options(target_file,overlay,editor):
    """Give tab options menu"""
    global USE_TABS

    title = "'tab' inserts tabs" if USE_TABS else "'tab' inserts spaces"
    _TAB_OPTIONS = const(("Back", "Use tabs", "Use spaces"))

    choice = overlay.popup_options(_TAB_OPTIONS,title=title,extended_border=True)

    if choice == "Back":
        return

    elif choice == "Use tabs":
        USE_TABS = True
        NVS.set_i32("use_tabs",True)
        NVS.commit()

    elif choice == "Use spaces":
        USE_TABS = False
        NVS.set_i32("use_tabs",False)
        NVS.commit()

def run_options(target_file,overlay,editor):
    """Give run options submenu"""
    _RUN_OPTIONS = const(("Cancel", "Run here", "Restart and run"))
    choice = overlay.popup_options(_RUN_OPTIONS,extended_border=True)
    if choice == "Cancel":
        return
    elif choice == "Run here":
        run_file_here(target_file, overlay, editor)
    elif choice == "Restart and run":
        boot_into_file(target_file,overlay)

def exit_options(target_file,overlay,editor):
    """Give run options submenu"""
    _EXIT_OPTIONS = const(("Cancel", "Exit to Files", "Exit to Launcher"))

    choice = overlay.popup_options(_EXIT_OPTIONS,extended_border=True)

    if choice == "Cancel":
        return
    elif choice == "Exit to Files":
        choice = overlay.popup_options(("Save", "Discard"),title="Save changes?")
        if choice == "Save":
            editor.save_file(target_file)
        boot_into_file(_FILE_BROWSER, overlay)
    elif choice == "Exit to Launcher":
        choice = overlay.popup_options(("Save", "Discard"),title="Save changes?")
        if choice == "Save":
            editor.save_file(target_file)
        boot_into_file('', overlay)

def boot_into_file(target_file,overlay):
    """Restart and load into target file."""
    overlay.draw_textbox("Restarting...", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2)
    DISPLAY.show()

    RTC.memory(target_file)
    machine.reset()

def run_file_here(filepath, overlay, editor):
    """Try running the target file here"""
    editor.save_file(filepath)
    overlay.draw_textbox("Running...", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2)
    DISPLAY.show()
    try:
        # you have to slice off the ".py" to avoid importerror
        mod = __import__(filepath[:-3])
        # we need to unload the module to import it again later.
        mod_name = mod.__name__
        if mod_name in sys.modules:
            del sys.modules[mod_name]

    except Exception as e:
        overlay.error(f"File closed with error: {e}")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~ String formatting/classification: ~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def classify_char(char) -> int:
    """Classify char types for comparison. Returns an int representing the type."""
    if char is None:
        return _NONE_CLASS
    elif char.isalpha() or char == "_":
        return _ALPHA_CLASS
    elif char.isdigit():
        return _DIGIT_CLASS
    elif char == ".":
        return _DOT_CLASS
    elif char.isspace():
        return _SPACE_CLASS
    elif char == _INDENT_SYM:
        return _INDENT_CLASS
    return _OTHER_CLASS


def is_var(string) -> bool:
    """Check if string could be a variable name."""
    for idx, char in enumerate(string):
        if idx == 0:
        # first char can only be underscore or letter
            if not (char.isalpha() or char == "_"):
                return False
        else:
        # chars must be alphanumeric or underscores
            if not (char.isalpha() or char == "_" or char.isdigit()):
                return False
    return True


def is_numeric(string):
    """Check if string is numeric. Support for "_" and "." """
    any_numbers = False
    for char in string:
        if char.isdigit():
            any_numbers = True
        elif char not in "._":
            return False
    return any_numbers


#string formatter
def remove_line_breaks(line):
    """Trim line breaks off lines for display/editing."""

    if line.endswith('\r') or line.endswith('\n'):
        line = line[:-1]
    if line.endswith('\r') or line.endswith('\n'):
        line = line[:-1]
    return line


def replace_tabs(line):
    """replace tabs with fake tab"""
    tab_syms = ''
    while line.startswith(_TAB_INDENT):
        line = line[1:]
        tab_syms += _INDENT_SYM
    return tab_syms + line


def replace_space_indents(line):
    """replace space indents with fake tab"""
    space_syms = ''
    while line.startswith(' '):
        # we must handle cases where less than 4 spaces are used, but we expect 4.
        for _ in range(4):
            if line.startswith(' '):
                line = line[1:]
        space_syms += _INDENT_SYM
    return space_syms + line


def auto_set_tabs(lines):
    """Set tab use option based on first occurance."""

    for line in lines:
        if line.startswith(_TAB_INDENT):
            return True
        elif line.startswith(_SPACE_INDENT):
            return False
    return None


def clean_line(line):
    """Clean line for display/editing."""
    line = remove_line_breaks(line)
    line = replace_space_indents(line)
    line = replace_tabs(line)
    return line


def format_display_line(line):
    """Preform final line formatting before printing to display."""
    line = line.replace(_INDENT_SYM, ' ')
    return line


def segment_from_str(string, index):
    """Extract word segment from index, based on classify_char"""
    output_str = ""
    start_class = classify_char(string[index])
    idx = index
    while idx < len(string): # look right
        if (classify_char(string[idx]) == start_class
            # allow numbers on vars
            )or (start_class == _ALPHA_CLASS and classify_char(string[idx]) == _DIGIT_CLASS
            # allow numbers to start with a "."
            )or (start_class == _DOT_CLASS and classify_char(string[idx]) == _DIGIT_CLASS
            # allow numbers with "." at the end or middle
            )or (start_class == _DIGIT_CLASS and classify_char(string[idx]) == _DOT_CLASS):

            output_str += string[idx]
            idx += 1
        else: break
    idx = index - 1
    while idx >= 0: # look left
        if classify_char(string[idx]) == start_class:
            output_str = string[idx] + output_str
            idx -= 1
        else: break
    return output_str



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Graphics Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def draw_small_line(line,x,y,fade=0):
    """apply special styling to a small line and display it."""
    line = format_display_line(line)
    is_comment = False
    string_char = None
    for idx, char in enumerate(line):
        # find comments
        if char == "#" and string_char == None:
            is_comment = True
        # find strings
        if char in "'\"":
            if string_char == None:
                string_char = char
            elif char == string_char:
                string_char = "END"

        # decide on color
        clr_idx = 4 - fade
        if x < _LEFT_PADDING: # fade left chars
            color = CONFIG.palette[3]
            clr_idx -= 2
        elif x >= _RIGHT_TEXT_FADE:
            color = CONFIG.palette[4]
            clr_idx -= 1

        if is_comment:
            color = DARK_COMMENT_COLOR
        elif string_char:
            color = DARK_STR_COLOR
        else:
            color = CONFIG.palette[max(clr_idx, 2)]

        DISPLAY.text(char,
                    x,
                    y, color
                    )

        # reset style trackers for next cycle
        if string_char == "END": string_char = None
        x += 8


def draw_rule(x,y,small=False, highlight=False):
    """Draw one rule line"""
    DISPLAY.vline(
        x+6,y,
        _SMALL_TEXT_HEIGHT if small else _TEXT_HEIGHT,
        CONFIG.palette[1] if highlight else CONFIG.palette[0]
        )


def draw_rules(line,x,y,small=False,highlight=False):
    """Draw indentaiton rule lines for given line"""
    while line.startswith(_INDENT_SYM):
        line = line[1:]
        draw_rule(x,y,small=small,highlight=highlight)
        x += 8


def draw_fancy_line(line, x, y, highlight=False, trim=True):
    """apply special styling to a line and display it."""
    _KEYWORDS = const(('and','as','assert','break','class','continue','def','del','elif','else','except',
                       'False','Finally','for','from','global','if','import','in','is','lambda','None',
                       'nonlocal','not','or','pass','raise','return','True','try','while','with','yield'))
    _OPERATORS = const("<>,|[]{}()*^%!=-+/:;&@")

    # TODO: I worry this may be extremely unoptomized. Should maybe be tested/optimized further.

    line = format_display_line(line)
    # trim right part of line to speed up styling
    if len(line) > _HORIZONTAL_CHARACTERS and trim:
        offset = 0
        if x < _LEFT_RULE:
            offset_px = (x - _LEFT_RULE) * - 1
            offset = offset_px // 8
        start_trim = max(offset - 20,0)
        line = line[start_trim:_HORIZONTAL_CHARACTERS + offset + 1]
        x += start_trim*8

    # track if this line is commented
    is_comment = False
    # track if string found
    string_char = None
    num_char = False

    var_char = False

    current_segment = ""
    segment_counter = -1

    for idx, char in enumerate(line):

        # track current word segment
        if segment_counter <= 0: # need to fetch next segment
            # currently we only care about these, so might as well save some time
            current_segment = segment_from_str(line, idx)
            segment_counter = len(current_segment)

            # check if it could be a var
            if is_var(current_segment):
                var_char = True
            else:
                var_char = False

        # find comments
        if char == "#" and string_char == None:
            is_comment = True
        #find strings
        elif char in "'\"":
            if string_char == None:
                string_char = char
            elif char == string_char:
                string_char = "END"

        #decide on color
        if is_comment: # comment string
            if x >= _RIGHT_TEXT_FADE or x < _LEFT_PADDING:
                color = DARK_COMMENT_COLOR
            else:
                color = COMMENT_COLOR

        elif string_char: # this is in a string
            if x >= _RIGHT_TEXT_FADE or x < _LEFT_PADDING:
                color = DARK_STR_COLOR
            else:
                color = STR_COLOR

        elif current_segment in _KEYWORDS: # keywords
            color = KEYWORD_COLOR

        elif is_numeric(current_segment): # this is a number
            color = NUM_COLOR

        elif char in _OPERATORS:
            color = OP_COLOR

        elif x < _LEFT_PADDING: # fade left chars
            color = CONFIG.palette[3]

        elif x >= _RIGHT_TEXT_FADE:
            color = CONFIG.palette[4]

        else:
            color = CONFIG.palette[5]

        DISPLAY.bitmap_text(font, char,
                        x,
                        y, color
                        )

        # reset style trackers for next cycle
        if string_char == "END": string_char = None
        if num_char: num_char = False
        segment_counter -= 1

        x += 8



#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Editor Class: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#--------------------------------------------------------------------------------------------------
class Editor:
    """HyDE Editor class
    
    This class is used to manage the cursor and view positions, 
    as well as to hold and modify the lines of the open file.
    """
    #class to handle our text editor display and state
    def __init__(self, overlay):
        self.overlay = overlay
        self.lines = []
        self.display_index = [0,-3]
        self.cursor_index = [0,0]
        self.clipboard = ''

    def draw_lines(self):
        """Draw each visible editor line."""
        draw_y = 0
        line_x = _LEFT_PADDING - (self.display_index[0] * 8)

        # TODO: these if/else statements are too much. They should be simplified.

        for i in range(self.display_index[1],self.display_index[1] + 11):
            if i <= self.display_index[1] or i >= self.display_index[1] + 10:
                #top/bottom lines
                # only draw lines that are in the file:
                if i >= 0 and i < len(self.lines):
                    draw_rules(self.lines[i],line_x,draw_y,small=True,highlight=False)
                    draw_small_line(self.lines[i], line_x, draw_y, 2)
                draw_y += 8

            elif i <= self.display_index[1] + 1 or i >= self.display_index[1] + 9:
                #top/bottom lines
                if i >= 0 and i < len(self.lines):
                    draw_rules(self.lines[i],line_x,draw_y,small=True,highlight=False)
                    draw_small_line(self.lines[i], line_x, draw_y, 1)
                draw_y += 8

            elif i <= self.display_index[1] + 2 or i >= self.display_index[1] + 8:
                # compact lines
                if i >= 0 and i < len(self.lines):
                    draw_rules(self.lines[i],line_x,draw_y,small=True,highlight=False)
                    draw_small_line(self.lines[i], line_x, draw_y, 0)
                draw_y += 8

            else:
                if i == self.cursor_index[1]:
                    DISPLAY.rect(0,draw_y, 238,16,CONFIG.palette[0],fill=True)
                if i >= 0 and i < len(self.lines):
                    is_currentline = (i == self.cursor_index[1])
                    draw_rules(self.lines[i],line_x,draw_y,small=False,highlight=is_currentline)
                    draw_fancy_line(self.lines[i], line_x, draw_y, highlight=is_currentline,trim=is_currentline)

                draw_y += 16 + _DISPLAY_PADDING

    def get_current_indentation(self):
        """Return the indentation of selected line."""
        current_line, _ = self.split_line_at_cursor()

        # if current_line is indented at all:
        if current_line and current_line[0] == _INDENT_SYM:
            return segment_from_str(current_line,0)
        return ""

    def jump_backspace(self):
        """Repeat backspace until we hit a new char class"""
        start_type = classify_char(self.get_left_char())
        for _ in range(0,100): # let's not go forever here
            if classify_char(self.get_left_char()) != start_type:
                break
            self.backspace()

    def jump_left(self):
        """Repeat left until we hit a new char class"""
        start_type = classify_char(self.get_left_char())
        for _ in range(0,100): # let's not go forever here
            if classify_char(self.get_left_char()) != start_type:
                break
            self.move_left()

    def jump_right(self):
        """Repeat right until we hit a new char class"""
        start_type = classify_char(self.get_right_char())
        for _ in range(0,100): # let's not go forever here
            if classify_char(self.get_right_char()) != start_type:
                break
            self.move_right()

    def get_right_char(self):
        """get the character to the right of the cursor"""
        line = self.lines[self.cursor_index[1]]
        if self.cursor_index[0] < len(line):
            return line[self.cursor_index[0]]

    def get_left_char(self):
        """get the character to the left of the cursor"""
        line = self.lines[self.cursor_index[1]]
        if self.cursor_index[0] <= 0:
            return None
        elif self.cursor_index[0] - 1 < len(line):
            return line[self.cursor_index[0] - 1]

    def split_line_at_cursor(self):
        """Get 2 tuple of (left_line, right_line) based on cursor position."""
        line = self.lines[self.cursor_index[1]]
        return line[:self.cursor_index[0]], line[self.cursor_index[0]:]

    def insert_char(self, char):
        """insert a character at the cursor"""
        l_line, r_line = self.split_line_at_cursor()
        self.lines[self.cursor_index[1]] = l_line + char + r_line
        self.move_right()

    def insert_tab(self):
        """insert a tab at the cursor"""
        l_line, r_line = self.split_line_at_cursor()

        self.lines[self.cursor_index[1]] = l_line + _INDENT_SYM + r_line
        self.move_right()

    def insert_line(self):
        """insert a new line at the cursor"""
        l_line, r_line = self.split_line_at_cursor()

        # auto indent
        if l_line.endswith(':'):
            indent = self.get_current_indentation() + _INDENT_SYM
            r_line = indent + r_line
            indent_count = len(indent)
        else:
            indent = self.get_current_indentation()
            r_line = indent + r_line
            indent_count = len(indent)

        self.lines[self.cursor_index[1]] = l_line
        self.lines = self.lines[:self.cursor_index[1]+1] + [r_line] + self.lines[self.cursor_index[1]+1:]

        self.move_down()
        self.cursor_index[0] = indent_count
        self.display_to_cursor_x()


    def backspace(self):
        """delete a character at the cursor"""
        l_line, r_line = self.split_line_at_cursor()

        # if cursor at start of line, delete line:
        if not l_line and self.cursor_index[1] > 0:
            self.lines[self.cursor_index[1] - 1] += r_line
            self.lines = self.lines[:self.cursor_index[1]] + self.lines[self.cursor_index[1] + 1:]
            self.move_left()
            self.cursor_index[0] -= len(r_line)

        # else, delete one char:
        else:
            self.lines[self.cursor_index[1]] = l_line[:-1] + r_line
            self.move_left()

        self.display_to_cursor_x()


    def display_to_cursor_x(self):
        """Move view to cursor on the X axis"""
        if self.display_index[0] + _HORIZONTAL_CHARACTERS < self.cursor_index[0] + 4:
            self.display_index[0] = (self.cursor_index[0] - _HORIZONTAL_CHARACTERS) + 4
        if self.display_index[0] > self.cursor_index[0] - 4:
            self.display_index[0] = self.cursor_index[0] - 4
        if self.display_index[0] < 0:
            self.display_index[0] = 0

    def display_to_cursor_y(self):
        """Move view to cursor on the Y axis"""
        if self.cursor_index[1] < self.display_index[1] + 3:
            self.display_index[1] = self.cursor_index[1] - 3

        elif self.cursor_index[1] > self.display_index[1] + 7:
            self.display_index[1] = self.cursor_index[1] - 7

    def display_snap_right(self):
        """Move view all the way right"""
        self.display_index[0] += 100
        self.display_to_cursor_x()

    def display_snap_left(self):
        """Move view all the way left"""
        self.display_index[0] = 0
        self.display_to_cursor_x()

    def display_snap_up(self):
        """Move view all the way up"""
        self.display_index[1] = -3
        self.display_to_cursor_y()

    def display_snap_down(self):
        """Move view all the way down"""
        self.display_index[1] = len(self.lines)
        self.display_to_cursor_y()

    def clamp_cursor(self):
        """
        Keep cursor within editor lines, 
        where end of line connects with start of next line."""
        if self.cursor_index[0] < 0:
            self.cursor_index[0] = len(self.lines[max(0,self.cursor_index[1] - 1)])
            self.move_up()
        elif self.cursor_index[0] > len(self.lines[self.cursor_index[1]]):
            self.cursor_index[0] = 0
            self.move_down()

    def snap_cursor_x(self):
        """Keep cursor x within current line length."""
        if self.cursor_index[0] < 0:
            self.cursor_index[0] = 0
        elif self.cursor_index[0] > len(self.lines[self.cursor_index[1]]):
            self.cursor_index[0] = len(self.lines[self.cursor_index[1]])
        self.display_to_cursor_x()

    def move_end(self):
        """Jump to bottom of document"""
        self.cursor_index[1] = len(self.lines) - 1
        self.cursor_index[0] = len(self.lines[-1])
        self.display_index[1] = len(self.lines) -8
        self.display_to_cursor_x()


    def move_home(self):
        """Jump to top of document"""
        self.cursor_index[1] = 0
        self.cursor_index[0] = 0
        self.display_index[1] = -3
        self.display_to_cursor_x()


    def move_left(self):
        """Move cursor to the left"""
        self.cursor_index[0] -= 1
        self.clamp_cursor()
        self.display_to_cursor_x()


    def move_right(self):
        """Move cursor to the right"""
        self.cursor_index[0] += 1
        self.clamp_cursor()
        self.display_to_cursor_x()


    def move_up(self):
        """Move cursor up"""
        self.cursor_index[1] -= 1
        if self.cursor_index[1] < 0:
            self.cursor_index[1] = 0
            self.display_index[1] -= 1
        self.display_to_cursor_y()
        self.snap_cursor_x()


    def move_down(self):
        """Move cursor down"""
        self.cursor_index[1] += 1
        if self.cursor_index[1] >= len(self.lines):
            self.cursor_index[1] = len(self.lines) - 1
            self.display_index[1] += 1
        self.display_to_cursor_y()
        self.snap_cursor_x()

    def draw_scrollbar(self):
        """Draw the x and y scrollbars based on view position."""
        # y scrollbar
        max_screen_index = len(self.lines) - 5
        if max_screen_index > 0:
            scrollbar_height = (_DISPLAY_HEIGHT // max_screen_index) + 10
            scrollbar_position = int((_DISPLAY_HEIGHT - scrollbar_height) * ((self.display_index[1] + 3) / max_screen_index))
            DISPLAY.rect(238,0,2,_DISPLAY_HEIGHT, CONFIG.palette[0])
            DISPLAY.vline(237,scrollbar_position - 10, scrollbar_height + 20, CONFIG.palette[1])
            DISPLAY.rect(238,scrollbar_position - 10, 2, scrollbar_height + 20, CONFIG.palette[3])

        #x scrollbar
        max_screen_index = (len(self.lines[self.cursor_index[1]]) - _HORIZONTAL_CHARACTERS) + 4
        if max_screen_index > 0:
            scrollbar_width = (_DISPLAY_WIDTH // max_screen_index) + 10
            scrollbar_position = int((_DISPLAY_WIDTH - scrollbar_width) * ((self.display_index[0]) / max_screen_index) )
            DISPLAY.hline(scrollbar_position, 132, scrollbar_width, CONFIG.palette[1])
            DISPLAY.rect(0,133, _DISPLAY_WIDTH,2, CONFIG.palette[0])
            DISPLAY.rect(scrollbar_position, 133, scrollbar_width, 2, CONFIG.palette[3])

    def get_current_lines(self):
        """Get the lines currently within the "main" portion of the display"""
        output=[]
        for i in range(self.display_index[1] + 3, self.display_index[1]+8):
            if i >= 0 and i < len(self.lines):
                output.append(self.lines[i])
            else:
                output.append("")
        return output

    def draw_cursor(self):
        cursor_x = 8 * (self.cursor_index[0] - self.display_index[0]) + _LEFT_PADDING
        cursor_y = _TEXT_HEIGHT * (self.cursor_index[1] - self.display_index[1]) - 28
        if time.ticks_ms() % _CURSOR_BLINK_MS < _CURSOR_BLINK_HALF:
            DISPLAY.rect(cursor_x, cursor_y, 1, 16, CONFIG.palette[5])
        else:
            DISPLAY.rect(cursor_x, cursor_y, 1, 16, CONFIG.palette[3])

    def draw_bg(self):
        """fill the background"""
        DISPLAY.fill(CONFIG['bg_color'])
        if self.display_index[0] == 0: # left rule
            DISPLAY.vline(_LEFT_RULE, 0, _DISPLAY_HEIGHT, CONFIG.palette[0])

    def save_file(self, filepath):
        """Reverse temporary formatting and Save the file."""
        self.overlay.draw_textbox("Saving...",_DISPLAY_WIDTH//2,_DISPLAY_HEIGHT//2)
        DISPLAY.show()
        with open(filepath,"w") as file:
            for line in self.lines:
                line = line.replace(
                    _INDENT_SYM, _TAB_INDENT if USE_TABS else _SPACE_INDENT
                    )
                file.write(line + "\r\n")

    def copy_line(self):
        """Copy the current line to the clipboard"""
        self.clipboard = self.lines[self.cursor_index[1]]

    def paste(self):
        """Paste clipboard contents."""
        for char in self.clipboard:
            self.insert_char(char)

    def cut_line(self):
        """Copy line, and delete line."""
        self.clipboard = self.lines[self.cursor_index[1]]
        self.lines[self.cursor_index[1]] = ''
        self.cursor_index[0] = 0
        self.clamp_cursor()

    def del_line(self):
        """Delete current line"""
        self.lines[self.cursor_index[1]] = ''
        self.cursor_index[0] = 0
        self.backspace()




#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Main loop of the program."""

    global STR_COLOR, DARK_STR_COLOR, KEYWORD_COLOR, COMMENT_COLOR, DARK_COMMENT_COLOR, USE_TABS

    DISPLAY.fill(CONFIG['bg_color'])
    overlay = mhoverlay.UI_Overlay(CONFIG, KB, display_fbuf=DISPLAY)
    editor = Editor(overlay)

    # Find our filepath from RTC memory
    target_file = RTC.memory().decode()

    # remove syntax hilighting for plain txt files.
    if target_file.endswith('.txt'):
        STR_COLOR = CONFIG['ui_color']; DARK_STR_COLOR = CONFIG['ui_color']
        KEYWORD_COLOR = CONFIG['ui_color']
        COMMENT_COLOR = CONFIG['ui_color']; DARK_COMMENT_COLOR = CONFIG['ui_color']


    try:
        with open(target_file,'r') as file:
            editor.lines = file.readlines()
    except Exception as e:
        overlay.error(f"Couldn't open '{target_file}': {e}")
        machine.reset()

    #for when file empty
    if not editor.lines:
        editor.lines = ['']

    # set 'use tabs' option based on first indent found in file.
    USE_TABS = auto_set_tabs(editor.lines)
    # if 'auto_set_tabs' returned None, use stored value instead
    if USE_TABS is None:
        try:
            USE_TABS = bool(NVS.get_i32("use_tabs"))
        except:
            USE_TABS = False
            NVS.set_i32("use_tabs",0)
            NVS.commit()


    for idx, line in enumerate(editor.lines):
        editor.lines[idx] = clean_line(line)

    editor.move_end()
    editor.draw_lines()
    DISPLAY.show()
    KB.get_new_keys()

    redraw_display = True

    while True:
        keys = KB.get_new_keys()
        if keys:
            redraw_display = True
            for key in keys:
                if "CTL" in KB.key_state:
                    # CTRL KEY SHORTCUTS

                    if key == ";":
                        for _ in range(0,4):
                            editor.move_up()
                    elif key == ".":
                        for _ in range(0,4):
                            editor.move_down()
                    elif key == "/":
                        editor.jump_right()

                    elif key == ",":
                        editor.jump_left()

                    elif key == "BSPC":
                        editor.jump_backspace()
                    elif key == "s":
                        editor.save_file(target_file)
                    elif key == "F5":
                        boot_into_file(target_file,overlay)

                    elif key == "x":
                        editor.cut_line()
                    elif key == "c":
                        editor.copy_line()
                    elif key == "v":
                        editor.paste()

                elif "OPT" in KB.key_state:
                    # OPT KEY SHORTCUTS

                    if "." == key:
                        editor.move_end()
                    elif ";" == key:
                        editor.move_home()

                elif "ALT" in KB.key_state:
                    # OPT KEY SHORTCUTS
                    if key == "/":
                        editor.display_snap_right()
                    elif key == ",":
                        editor.display_snap_left()
                    elif key == ";":
                        editor.display_snap_up()
                    elif key == ".":
                        editor.display_snap_down()

                else:
                    # REGULAR KEYS

                    if key == 'UP':
                        editor.move_up()
                    elif key == 'DOWN':
                        editor.move_down()
                    elif key == "LEFT":
                        editor.move_left()
                    elif key == "RIGHT":
                        editor.move_right()
                    elif key == "ENT":
                        editor.insert_line()
                    elif key == "F5":
                        run_file_here(target_file,overlay,editor)
                    elif key == "BSPC":
                        editor.backspace()

                    elif key == "SPC":
                        editor.insert_char(" ")

                    elif key == "TAB":
                        editor.insert_tab()

                    elif key == "GO":
                        # file actions menu
                        file_options(target_file,overlay,editor)

                    elif key == "DEL":
                        editor.del_line()

                    elif len(key) == 1:
                        editor.insert_char(key)

        # graphics!
        if redraw_display:
            redraw_display = False
            editor.draw_bg()
            editor.draw_lines()
            editor.draw_scrollbar()
        else:
            time.sleep_ms(1)

        editor.draw_cursor() # cursor blinks so it needs to be redrawn regularly
        DISPLAY.show()

main_loop()