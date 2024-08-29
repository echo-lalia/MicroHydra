#coding: utf-8

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple

class PILFont():
    def __init__(self, font_path: str, font_size: int) -> None:
        self.__font = ImageFont.FreeTypeFont(font_path, font_size)
    
    def render_text(self, text: str, offset: Tuple[int, int] = (0, 0)) -> Image:
        ''' 绘制文本图片
            > text: 待绘制文本
            > offset: 偏移量
        '''
        __left, __top, right, bottom = self.__font.getbbox(text)
        img = Image.new("1", (right, bottom), color=255)
        img_draw = ImageDraw.Draw(img)
        img_draw.text(offset, text, fill=0, font=self.__font, spacing=0)
        return img

f = PILFont("guanzhi.ttf", 8)

def i18s_encode(text: str) -> int:
    ''' 将文本编码为整数
        > text: 待编码文本
    '''
    im = f.render_text(text)
    width, height = im.size

    cur = 0
    for i in range(height):
        for j in range(width):
            mi = width * i + j
            cur += (im.getpixel((j, i)) != 255) << mi

    return cur

def i18s_decode(cur: int, width=8, height=8) -> None:
    for i in range(height):
        for j in range(width):
            print('■' if cur & 1 else ' ', end='')
            cur >>= 1
        print()

# 生成Unicode范围内的所有字符，从 U+0000 到 U+FFFF
start = 0x0000  # 开始范围
end = 0xFFFF    # 结束范围

with open(f"utf8_8x8.bin", "wb") as binary_file:
    for codepoint in range(start, end + 1):
        char = chr(codepoint)
        
        try:
            # 获取i18s_encode的值
            encoded_value = i18s_encode(char)
            
            # 将i18s_encode的值（8字节）写入文件
            try:
                t = encoded_value.to_bytes(8, byteorder='big')
            except Exception as e:
                x = 0
                t = x.to_bytes(8, byteorder='big')
                print(f"Error encoding {char} (U+{codepoint:04X}):{e}, Assuming 0...")
            binary_file.write(t)
        
        except Exception as e:
            print(f"Error processing character {char} (U+{codepoint:04X}): {e}")