import gc

class mhKanji:
    def __init__(self,tft):
        self.tft = tft
        self.ascii_font = {'a': '0x6556000', 'b': '0x3553110', 'c': '0x6116000', 'd': '0x6556440', 'e': '0x6352000', 'f': '0x2227260', 'g': '0x74757000', 'h': '0x5553110',
                           'i': '0x7223020', 'j': '0x12222020', 'k': '0x5535110', 'l': '0x7222230', 'm': '0x5575000', 'n': '0x5553000', 'o': '0x2552000', 'p': '0x13553000',
                           'q': '0x46556000', 'r': '0x1135000', 's': '0x3636000', 't': '0x6227200', 'u': '0x6555000', 'v': '0x2255000', 'w': '0x5755000', 'x': '0x5225000',
                           'y': '0x34655000', 'z': '0x7247000', 'A': '0x5575520', 'B': '0x3553530', 'C': '0x6111160', 'D': '0x3555530', 'E': '0x7113170', 'F': '0x1113170',
                           'G': '0x6551160', 'H': '0x5575550', 'I': '0x7222270', 'J': '0x2544440', 'K': '0x5553550', 'L': '0x7111110', 'M': '0x5557750', 'N': '0x5555530',
                           'O': '0x2555520', 'P': '0x1135530', 'Q': '0x42555520', 'R': '0x5535530', 'S': '0x3442160', 'T': '0x2222270', 'U': '0x7555550', 'V': '0x1355550',
                           'W': '0x5775550', 'X': '0x5522550', 'Y': '0x2222550', 'Z': '0x7122470', '0': '0x2555200', '1': '0x7223200', '2': '0x7124300', '3': '0x3424300',
                           '4': '0x4756400', '5': '0x3431700', '6': '0x7571700', '7': '0x2224700', '8': '0x7575700', '9': '0x7475700', '~': '0x630', '!': '0x2022220',
                           '@': '0x2564520', '#': '0x5755750', '$': '0x2763720', '%': '0x4124100', '^': '0x520', '&': '0xb5a5520', '*': '0x52720', '(': '0x42222240',
                           ')': '0x12222210', '_': '0x70000000', '+': '0x2272200', '-': '0x70000', '=': '0x707000', '[': '0x62222260', ']': '0x32222230', '{': '0x42212240',
                           '}': '0x12242210', '|': '0x22222220', ';': '0x1202000',"'": '0x120', ':': '0x202000', '"': '0x550', ',': '0x24000000', '.': '0x2000000',
                           '/': '0x124000', '<': '0x4212400', '>': '0x1242100', '?': '0x2024520'}
        self.font = open("/font/kanji_8x8.txt","r",encoding = 'utf-8', buffering = 0)
        self.cache = {}
           
    def show_decode(self, cur, x, y, color, scale = 2, height = 8, width = 8):
        for i in range(height):
            for j in range(width):
                if (cur & 1):
                    self.tft.rect((x+j)*scale,(y+i)*scale,scale,scale,color,True)
                cur >>= 1
    
    def putc(self, char, x, y, color, scale = 2):
        if char in self.ascii_font:
            self.show_decode(int(self.ascii_font[char]), x, y, color, scale, width = 4)
        elif char in self.cache:
            self.show_decode(int(self.cache[char]), x, y, color, scale)
        else:
            found = False
            t_id = t_cur = ""
            self.font.seek(0)
            while True:
                line = self.font.readline()
                if not line:
                    break
                
                try:
                    t_id,t_cur = line.split()
                except:
                    continue
                
                if t_id == char:
                    found = True
                    break
                
            
            if len(self.cache) >= 200:
                del self.cache[list(self.cache.keys())[0]]
            
            if found:
                cur = t_cur
                self.cache[char] = cur
                self.show_decode(int(cur), x, y, color, scale)
            else:
                self.show_decode(0x7e424242427e0000, x, y, color, scale)
        
    def text(self, string, x, y, color, scale = 2, instant_show = True):
        cur_x = x
        for char in string:
            self.putc(char, cur_x, y, color, scale)
            if instant_show:
                self.tft.show()
            
            if char in self.ascii_font:
                cur_x += 4
            else:
                cur_x += 8

