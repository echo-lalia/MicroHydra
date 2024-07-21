from lib import st7789fbuf, mhconfig, keyboard
import machine, time, os
machine.freq(240_000_000)
"""
MicroHydra SHELL & Terminal
Version: 1.0

A simple Terminal that can run console-based Apps.
Have fun!

TODO:
KFC V me 50
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
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

# object for accessing microhydra config (Delete if unneeded)
config = mhconfig.Config()

# object for reading keypresses
kb = keyboard.KeyBoard()

#screen buffer
scr_buf = [""]*13

RTC = machine.RTC()

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def scr_feed(str):
    for i in range(1,12):
        scr_buf[i-1] = scr_buf[i]
    scr_buf[11] = str
    
def scr_show():
    # clear framebuffer 
    tft.fill(config['bg_color'])
    # write current text to framebuffer
    for i in range(12):
        tft.text(text=scr_buf[i], x=0, y=10*i,color=config['ui_color'])
    # write framebuffer to display
    tft.show()

def scr_clear():
    for i in range(12):
        scr_buf[i] = ""
    scr_show()

# Custom print function that writes to the buffer
def custom_print(*args, **kwargs):
    str_out = (' '.join(map(str, args)) + kwargs.get('end', '')).split('\n')
    for i in str_out:
        while len(i)>30:
            scr_feed(i[:30])
            scr_show()
            i = i[30:]
        
        scr_feed(i)
        scr_show()


# Replace the built-in print function with the custom one
print = custom_print

def custom_input(prmpt):
    print(f"{prmpt} _")
    
    current_text = []
    while True:
        keys = kb.get_new_keys()
        # if there are keys, convert them to a string, and store for display
        if keys:
            if 'SPC' in keys:
                current_text.append(' ')
            elif 'BSPC' in keys:
                current_text = current_text[:-1]
            else:
                current_text += [i for i in keys if i != 'ENT']
            
            scr_buf[11] = f"{prmpt} " + ''.join(current_text) + "_"
            scr_show()
            
            if 'ENT' in keys or 'GO' in keys:
                scr_buf[11] = scr_buf[11][:-1]
                scr_show()
                line = ''.join(current_text)
                return line

input = custom_input
#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    
    app_path = RTC.memory().decode()
    if app_path[0] == '$':
        #print(app_path[1:])
        exec(open(app_path[1:]).read(), {'__name__': '__main__'},globals())
    else:
        print(f"MicroHydra v{os.uname().release}) on {os.uname().sysname}, Terminal Ver 1.0.")
        print("Press GO Button to Exit.")
    
    print(f"root@MH:{os.getcwd()}# _")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    
    # create variable to remember text between loops
    current_text = []
    
    
    while True: # Fill this loop with your program logic! (delete old code you dont need)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # put user input logic here
        
        # get list of newly pressed keys
        keys = kb.get_new_keys()
        
        # if there are keys, convert them to a string, and store for display
        if keys:
            if 'GO' in keys:
                machine.reset()
            if 'SPC' in keys:
                current_text.append(' ')
            elif 'BSPC' in keys:
                current_text = current_text[:-1]
            else:
                current_text += [i for i in keys if i != 'ENT']
            
            scr_buf[11] = f"root@MH:{os.getcwd()}# " + ''.join(current_text) + "_"
            scr_show()
            
            if 'ENT' in keys:
                scr_buf[11] = scr_buf[11][:-1]
                try:
                    args = (''.join(current_text)).split()
                    if args[0] == 'ls':
                        print('  '.join(os.listdir() if len(args) == 1 else os.listdir(args[1])))
                            
                    elif args[0] == 'cat':
                        with open(args[1], 'r') as f:
                            print(f.read())
                    elif args[0] == 'cd' or args[0] == 'chdir':
                        os.chdir(args[1])
                    elif args[0] == 'rm':
                        for i in args[1:]:
                            os.remove(i)
                    elif args[0] == 'touch':
                        for i in args[1:]:
                            with open(i, 'w') as f:
                                f.write(i)
                    elif args[0] == 'mv':
                        os.rename(args[1],args[2])
                    elif args[0] == 'cwd':
                        print(os.getcwd())
                    elif args[0] == 'mkdir':
                        for i in args[1:]:
                            os.mkdir(i)
                    elif args[0] == 'rmdir':
                        for i in args[1:]:
                            os.rmdir(i)
                    elif args[0] == 'uname':
                        print(os.uname().machine)
                    elif args[0] == 'clear':
                        scr_clear()
                    elif args[0] == 'reboot' or args[0] == 'exit':
                        machine.reset()
                    elif args[0] in os.listdir():
                        try:
                            exec(open(args[0]).read(), {'__name__': '__main__', 'argv':args},globals())
                        except Exception as e:
                            print(e)
                            print("Trying Hard Launch...")
                            RTC.memory(args[0])
                            # reset clock speed to default.
                            machine.freq(160_000_000)
                            time.sleep_ms(10)
                            machine.reset()
                    else:
                        print("Bad Command.")
                except Exception as e:
                    print(f"{e}")
                       
                print(f"root@MH:{os.getcwd()}# _")
                current_text = []
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # anything that needs to be done to prepare for next loop
        
        # do nothing for 10 milliseconds
        time.sleep_ms(10)


# start the main loop
try:
    main_loop()
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[TERMINAL]')
        sys.print_exception(e, f)
    
    tft.text(text=f"{e}",x=0, y=0, color=config['ui_color'])
    tft.show()


