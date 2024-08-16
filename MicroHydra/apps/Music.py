from lib import st7789fbuf, mhconfig, mhoverlay, smartkeyboard, beeper
from font import vga2_16x32 as font
import os, machine, time, math, framebuf, random
from machine import SDCard, Pin
machine.freq(240000000)

"""
EasyWav 
Version: 1

Description:
Gets wav files from a directory on the sd card called 'music'. It then lists this files to be selected and played.

Arrow keys to navigate/change songs, enter to play/pause.
"""

# Constants
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_CHAR_HEIGHT = const(32)
_ITEMS_PER_SCREEN = const(_DISPLAY_HEIGHT // _CHAR_HEIGHT)
_CHARS_PER_SCREEN = const(_DISPLAY_WIDTH // 16)
_SCROLL_TIME = const(5000)  # ms per one text scroll
_SCROLLBAR_WIDTH = const(3)
_SCROLLBAR_START_X = const(_DISPLAY_WIDTH - _SCROLLBAR_WIDTH)

# Define pin constants
_SCK_PIN = const(41)
_WS_PIN = const(43)
_SD_PIN = const(42)

# Initialize hardware
tft = st7789fbuf.ST7789(
    machine.SPI(
        1,baudrate=40000000,sck=machine.Pin(36),mosi=machine.Pin(35),miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
)

config = mhconfig.Config()
kb = smartkeyboard.KeyBoard(config=config)
overlay = mhoverlay.UI_Overlay(config, kb, display_fbuf=tft)
beep = beeper.Beeper()

sd = None
i2s = None

def mount_sd():
    global sd
    try:
        if sd is None:
            sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
        os.mount(sd, '/sd')
        print("SD card mounted successfully")
    except OSError as e:
        print("Could not mount SDCard:", str(e))
        overlay.error("SD Card Mount Error")

def read_wav_header(file):
    file.seek(0)
    riff = file.read(12)
    fmt = file.read(24)
    data_hdr = file.read(8)
    
    sample_rate = int.from_bytes(fmt[12:16], 'little')
    return sample_rate * 2

def setup_i2s(sample_rate):
    global i2s
    i2s = machine.I2S(0,
                      sck=machine.Pin(_SCK_PIN),
                      ws=machine.Pin(_WS_PIN),
                      sd=machine.Pin(_SD_PIN),
                      mode=machine.I2S.TX,
                      bits=16,
                      format=machine.I2S.MONO,
                      rate=sample_rate,
                      ibuf=1024)

def ease_in_out_sine(x):
    return -(math.cos(math.pi * x) - 1) / 2

def ping_pong_ease(value, maximum):
    odd_pong = ((value // maximum) % 2 == 1)
    fac = ease_in_out_sine((value % maximum) / maximum)
    return 1 - fac if odd_pong else fac

def find_cover_image(song_name):
    # Remove the file extension
    base_name = song_name.rsplit('.', 1)[0]
    
    # Split the base name into parts
    parts = base_name.split(' - ')
    
    # Construct the cover image filename (Artist - Album.ppm)
    if len(parts) >= 2:
        cover_filename = f"{parts[0]} - {parts[1]}.ppm"
    else:
        # If the filename doesn't follow the expected format, use the whole base name
        cover_filename = f"{base_name}.ppm"
    
    # Construct the full path
    cover_path = f"/sd/music/covers/{cover_filename}"
    
    # Check if the file exists
    try:
        os.stat(cover_path)
        return cover_path
    except OSError:
        # If the file doesn't exist, return None
        return None

# Modify the load_and_display_image function
def load_and_display_image(song_name):
    image_path = find_cover_image(song_name)
    if not image_path:
        print("No cover image found")
        return
    
    try:
        with open(image_path, "rb") as f:
            # Skip the header
            f.readline()  # P6
            f.readline()  # Comment
            width, height = [int(v) for v in f.readline().split()]
            f.readline()  # Max color value
            
            # Read the image data
            data = f.read(width * height * 3)
            
            # Convert RGB888 to RGB565
            buffer = bytearray(width * height * 2)
            for i in range(0, len(data), 3):
                r, g, b = data[i:i+3]
                rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                buffer[i//3*2] = rgb >> 8
                buffer[i//3*2+1] = rgb & 0xFF
            
            # Create a framebuffer and blit it to the display
            fbuf = framebuf.FrameBuffer(buffer, width, height, framebuf.RGB565)
            tft.blit_buffer(buffer, 0, 0, width, height)
    except Exception as e:
        print(f"Error loading image: {str(e)}")
        
def display_play_screen(selected_file):
    # Clear the screen
    tft.fill(config["bg_color"])
    
    # Load and display the background image
    load_and_display_image(selected_file)
    
    # Display song info
    parts = selected_file.rsplit('.', 1)[0].split(' - ')
    if len(parts) == 3:
        artist, album, song = parts
        overlay.draw_textbox(f"Artist: {artist}", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//4)
        overlay.draw_textbox(f"Album: {album}", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2)
        overlay.draw_textbox(f"Song: {song}", _DISPLAY_WIDTH//2, 3*_DISPLAY_HEIGHT//4)
    else:
        overlay.draw_textbox(f"Playing: {selected_file}", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2)
    
    tft.show()

import random

class EasyWavMenu:
    def __init__(self, tft, config):
        self.tft = tft
        self.config = config
        self.main_items = ['Library', 'Shuffle', 'Settings']
        self.settings_items = ['Volume', 'Theme', 'Back']
        self.cursor_index = 0
        self.view_index = 0
        self.current_view = 'main'  # 'main', 'library', 'shuffle', or 'settings'
        self.wav_list_view = None
        self.items = self.main_items

    def draw(self):
        self.tft.fill(self.config["bg_color"])
        if self.current_view == 'main':
            self._draw_main_menu()
        elif self.current_view == 'library':
            self.wav_list_view.draw()
        elif self.current_view == 'settings':
            self._draw_settings_menu()
        self.tft.show()

    def _draw_main_menu(self):
        for idx, item in enumerate(self.main_items):
            color = self.config.palette[5] if idx == self.cursor_index else self.config.palette[4]
            self.tft.bitmap_text(font, item, 10, idx * _CHAR_HEIGHT, color)

    def _draw_settings_menu(self):
        for idx, item in enumerate(self.settings_items):
            color = self.config.palette[5] if idx == self.cursor_index else self.config.palette[4]
            self.tft.bitmap_text(font, item, 10, idx * _CHAR_HEIGHT, color)

    def up(self):
        if self.current_view in ['main', 'settings']:
            self.cursor_index = (self.cursor_index - 1) % len(self.items)
        elif self.current_view == 'library':
            self.wav_list_view.up()
            self.cursor_index = self.wav_list_view.cursor_index
            self.items = self.wav_list_view.items

    def down(self):
        if self.current_view in ['main', 'settings']:
            self.cursor_index = (self.cursor_index + 1) % len(self.items)
        elif self.current_view == 'library':
            self.wav_list_view.down()
            self.cursor_index = self.wav_list_view.cursor_index
            self.items = self.wav_list_view.items

    def select(self):
        if self.current_view == 'main':
            selected_item = self.main_items[self.cursor_index]
            if selected_item == 'Library':
                self.open_library()
            elif selected_item == 'Shuffle':
                return self.shuffle_play()
            elif selected_item == 'Settings':
                self.open_settings()
        elif self.current_view == 'library':
            return "play"
        elif self.current_view == 'settings':
            selected_item = self.settings_items[self.cursor_index]
            if selected_item == 'Back':
                self.back()
            else:
                print(f"Setting {selected_item} selected")
                # Implement setting change logic here

    def back(self):
        if self.current_view in ['library', 'settings', 'shuffle']:
            self.current_view = 'main'
            self.cursor_index = 0
            self.items = self.main_items
            return True
        return False

    def open_library(self):
        print("Opening Library")
        if not self.wav_list_view:
            self.wav_list_view = WavListView(self.tft, self.config)
        self.wav_list_view.load_wav_files()
        self.current_view = 'library'
        self.cursor_index = self.wav_list_view.cursor_index
        self.items = self.wav_list_view.items

    def shuffle_play(self):
        print("Starting Shuffle Play")
        if not self.wav_list_view:
            self.wav_list_view = WavListView(self.tft, self.config)
            self.wav_list_view.load_wav_files()
        if self.wav_list_view.items:
            self.current_view = 'shuffle'
            random_song = random.choice(self.wav_list_view.items)
            print(f"Selected random song: {random_song}")
            return "play_shuffle", random_song
        else:
            print("No songs available for shuffle play")
            return None

    def open_settings(self):
        print("Opening Settings")
        self.current_view = 'settings'
        self.cursor_index = 0
        self.items = self.settings_items

    def handle_input(self, key):
        if self.current_view in ['main', 'settings']:
            if key == ";":
                self.up()
                return "up"
            elif key == ".":
                self.down()
                return "down"
            elif key in ("ENT", "SPC"):
                return self.select()
        elif self.current_view == 'library':
            if key == ";":
                self.wav_list_view.up()
                self.cursor_index = self.wav_list_view.cursor_index
                self.items = self.wav_list_view.items
                return "up"
            elif key == ".":
                self.wav_list_view.down()
                self.cursor_index = self.wav_list_view.cursor_index
                self.items = self.wav_list_view.items
                return "down"
            elif key in ("ENT", "SPC"):
                return self.select()
        
        if key in ("`", "DEL", "ESC", "BKSP"):
            if self.back():
                return "back"
            else:
                return "exit"
        
        return None

class WavListView:
    def __init__(self, tft, config):
        self.tft = tft
        self.config = config
        self.items = []
        self.view_index = 0
        self.cursor_index = 0

    def load_wav_files(self):
        try:
            self.items = [f for f in os.listdir("/sd/music") if f.lower().endswith('.wav')]
            print("WAV files found:", self.items)
        except OSError as e:
            print("Error loading WAV files:", str(e))
            self.items = []

    def draw(self):
        if not self.items:
            self.tft.bitmap_text(font, "No WAV files found", 10, 10, self.config.palette[4])
        else:
            for idx in range(0, _ITEMS_PER_SCREEN):
                item_index = idx + self.view_index
                if item_index < len(self.items):
                    color = self.config.palette[5] if item_index == self.cursor_index else self.config.palette[4]
                    text = self.items[item_index]
                    
                    # Apply ping-pong scrolling for long text
                    if len(text) > _CHARS_PER_SCREEN:
                        scroll_distance = (len(text) - _CHARS_PER_SCREEN) * -16
                        x = int(ping_pong_ease(time.ticks_ms(), _SCROLL_TIME) * scroll_distance)
                    else:
                        x = 10  # Default x position for short text
                    
                    self.tft.bitmap_text(font, text, x, idx * _CHAR_HEIGHT, color)

    def up(self):
        if self.items:
            self.cursor_index = (self.cursor_index - 1) % len(self.items)
            self.view_to_cursor()

    def down(self):
        if self.items:
            self.cursor_index = (self.cursor_index + 1) % len(self.items)
            self.view_to_cursor()

    def view_to_cursor(self):
        if self.cursor_index < self.view_index:
            self.view_index = self.cursor_index
        if self.cursor_index >= self.view_index + _ITEMS_PER_SCREEN:
            self.view_index = self.cursor_index - _ITEMS_PER_SCREEN + 1
            
    def back(self):
        return True

def ping_pong_ease(value, maximum):
    odd_pong = ((value // maximum) % 2 == 1)
    fac = ease_in_out_sine((value % maximum) / maximum)
    return 1 - fac if odd_pong else fac

def ease_in_out_sine(x):
    return -(math.cos(math.pi * x) - 1) / 2

def play_sound(notes, time_ms=30):
    if config['ui_sound']:
        beep.play(notes, time_ms, config['volume'])

def main_loop():
    mount_sd()
    view = EasyWavMenu(tft, config)
    
    while True:
        view.draw()
        
        new_keys = kb.get_new_keys()
        for key in new_keys:
            action = view.handle_input(key)
            
            if action == "up":
                play_sound(("G3","B3"), 30)
            elif action == "down":
                play_sound(("D3","B3"), 30)
            elif action == "select":
                play_sound(("G3","B3","D3"), 30)
            elif action == "play" or (isinstance(action, tuple) and action[0] == "play_shuffle"):
                if view.current_view in ['library', 'shuffle'] and view.items:
                    if isinstance(action, tuple) and action[0] == "play_shuffle":
                        selected_file = action[1]
                    else:
                        selected_file = view.items[view.cursor_index]
                    try:
                        with open(f"/sd/music/{selected_file}", 'rb') as file:
                            sample_rate = read_wav_header(file)
                            setup_i2s(sample_rate)
                            
                            # Display the play screen
                            display_play_screen(selected_file)
                            
                            play_sound(("G3","B3","D3"), 30)
                            
                            while True:
                                data = file.read(1024)
                                if not data:
                                    break
                                i2s.write(data)
                                
                                if kb.get_new_keys():  # Check for key press to stop playback
                                    break
                            
                            i2s.deinit()
                    except Exception as e:
                        print(f"Error playing file: {str(e)}")
                        overlay.error(f"Playback Error: {str(e)[:20]}")
            elif action == "back":
                play_sound(("D3","B3","G3"), 30)
            elif action == "exit":
                return  # Exit the app
        
        time.sleep_ms(10)

try:
    main_loop()
except Exception as e:
    print("Error:", str(e))
    overlay.error(str(e))
finally:
    if sd:
        os.umount('/sd')
        print("SD card unmounted")
