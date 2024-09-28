"""A tool for merging two bitmap font bins (as output by generate_utf8_font.py).

This is useful because it makes it easy to fill in missing glyphs,
making the most of our 65535 code points.
"""

# This font is the preferred font
font_main = "tools/utf8_util/guanzhi8x8.bin"
# This font is used when the preferred font is missing glyphs.
font_secondary = "tools/utf8_util/unifont8x8.bin"

output_name = "tools/utf8_util/utf8_8x8.bin"



empty_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00'

count_main = 0
count_second = 0

with open(font_main, 'rb') as main, \
open(font_secondary, 'rb') as secondary, \
open(output_name, 'wb') as output:
    for _ in range(65536):
        main_glyph = main.read(8)
        secondary_glyph = secondary.read(8)

        if main_glyph == empty_bytes:
            output.write(secondary_glyph)
            count_second += 1
        else:
            output.write(main_glyph)
            count_main += 1

print(f"""\
Wrote {count_main + count_second} glyphs.
Used {count_main} glyphs from {font_main},
used {count_second} glyphs from {font_secondary}.
""")
