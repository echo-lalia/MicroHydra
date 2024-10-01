"""Convert a font into a utf8 bin, compatible with MicroHydra."""

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import math


in_file = "tools/utf8_util/unifont-16.0.01.otf"
out_file = "tools/utf8_util/unifont8x8.bin"

threshold = 200
text_draw_size = 32

# Display test images:
testing_chars = {'ಠ', 'ツ', '✿'}

# how to handle rescaling:
rescale = True
sharpen = True
brightness = 2.0
contrast = 2.0
sharpen = 500




TEST_IMG = None
class TestImg:
    """Stores several test images for comparison."""

    img = None
    height = 32
    def __init__(self, img: Image.Image):
        """Make a new test image."""
        TestImg.img = img.resize((int(self.height/img.width*img.width), self.height), resample=Image.Resampling.NEAREST)

    @classmethod
    def append(cls, img: Image.Image):
        """Append a new image onto the test image."""
        img = img.resize((int(cls.height/img.width*img.width), cls.height), resample=Image.Resampling.NEAREST)
        new_img = Image.new(mode='L', size=(cls.img.width + img.width, cls.height))
        new_img.paste(cls.img, (0,0))
        new_img.paste(img, (cls.img.width, 0))
        cls.img = new_img


class PILFont:
    """Outputs font glyphs as images."""

    def __init__(self, font_path: str, font_size: int) -> None:
        """Load given font with given size."""
        self.__font = ImageFont.FreeTypeFont(font_path, font_size)

    def render_text(self, text: str, offset: tuple[int, int] = (0, 0)) -> Image.Image:
        """绘制文本图片.

        > text: 待绘制文本
        > offset: 偏移量
        """
        global TEST_IMG  # noqa: PLW0603

        __left, __top, right, bottom = self.__font.getbbox(text)
        img = Image.new("1", (right, bottom), color=255)
        img_draw = ImageDraw.Draw(img)
        img_draw.text(offset, text, fill=0, font=self.__font, spacing=0)

        if text in testing_chars:
            TEST_IMG = TestImg(img)

        return img


f = PILFont(in_file, text_draw_size)


# Rescale helpers:
def mix(val2, val1, fac:float = 0.5) -> float:
    """Mix two values to the weight of fac."""
    return (val1 * fac) + (val2 * (1.0 - fac))

def rescale_by_factor(bbox, im) -> tuple[int, int, int, int]:
    """Crop all edges by some fraction of the bbox."""
    left, top, right, bottom = bbox
    return (
        int(mix(0, left, 0.8)),
        int(mix(0, top, 0.5)),
        math.ceil(mix(im.width, right, 0.5)),
        math.ceil(mix(im.height, bottom, 0.5)),
    )

def rescale_by_threshold(bbox, im) -> tuple[int, int, int, int]:
    """Crop exactly to bbox, except for when it's obvious that this is incorrect."""
    left, top, right, bottom = bbox
    if left > im.width*3//2:
        left = 0
    if top > im.height*3//2:
        top = 0
    if right < im.width//3:
        right = im.width
    if bottom < im.height//3:
        bottom = im.height
    return left, top, right, bottom


def rescale_glyph(im: Image.Image, text: str) -> Image.Image|None:
    """Rescale the given glyph image.

    Uses values from the top of the script.
    """
    bbox = ImageOps.invert(im).getbbox(alpha_only=False)
    # We need gray values for the rescale
    im = im.convert('L')

    # guard against blank images:
    if bbox is None:
        return None

    left, top, right, bottom = bbox

    code = ord(text)
    # glyph is large, just add a bit of spacing and crop tight
    if right-left > im.width//3 and bottom-top > im.height//3:
        right += 1
    # glyph is a symbol, crop tight unless threshold reached
    elif 0x2010 <= code <= 0x2bff:
        left, top, right, bottom = rescale_by_threshold(bbox, im)
    # other glyphs are cropped by some factor of the original size
    else:
        left, top, right, bottom = rescale_by_factor(bbox, im)

    if text in testing_chars:
        print(f"Showing glyph for {text}:")
        print(f"  source size {im.width, im.height}, bbox {bbox} -> {left, top, right, bottom}\n")
        TEST_IMG.append(im.crop(bbox))

    im = im.crop((left, top, right, bottom))
    return im.resize((8, 8), resample=Image.Resampling.LANCZOS)


def i18s_encode(text: str) -> int:
    """将文本编码为整数.

    > text: 待编码文本
    """
    im = f.render_text(text)
    width, height = im.size

    if rescale:
        im = rescale_glyph(im, text)
        if im is None:
            return 0
        if text in testing_chars:
            TEST_IMG.append(im)

    # rarely, glyphs can be too large to encode
    elif (width > 8 or height > 8) \
    and (width and height):
        width = min(width, 8)
        height = min(height, 8)
        im = im.resize((width, height))

    # These filters dont work on 1-bit images
    if im.mode == 'L':
        if sharpen:
            im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=sharpen))
        if brightness:
            im = ImageEnhance.Brightness(im).enhance(brightness)
        if contrast:
            im = ImageEnhance.Contrast(im).enhance(contrast)
        if text in testing_chars:
            TEST_IMG.append(im)
        im = im.convert('1')

    if text in testing_chars:
        TEST_IMG.append(im)
        TEST_IMG.img.show()

    # Convert px data to integer
    cur = 0
    for i in range(im.height):
        for j in range(im.width):
            mi = im.width * i + j
            cur += (im.getpixel((j, i)) < threshold) << mi
    return cur


def _i18s_decode(cur: int, width=8, height=8) -> None:
    for _ in range(height):
        for _ in range(width):
            print('■' if cur & 1 else ' ', end='')
            cur >>= 1
        print()


# 生成Unicode范围内的所有字符, 从 U+0000 到 U+FFFF
start = 0x0000  # 开始范围
end = 0xFFFF    # 结束范围

with open(out_file, "wb") as binary_file:
    for codepoint in range(start, end + 1):
        char = chr(codepoint)

        # 获取i18s_encode的值
        encoded_value = i18s_encode(char)

        # 将i18s_encode的值(8字节)写入文件
        t = encoded_value.to_bytes(8, byteorder='big')

        binary_file.write(t)
