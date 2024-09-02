"""
Simple script to convert the output of `generate_utf8_font.py` 
into a .py file that can be frozen in MicroPython firmware.
"""

import os


# decide on working in the current, or in the './tools/utf8_util' directory
if os.path.exists(os.path.join('tools','utf8_util','utf8_8x8.bin')):
    source_file = os.path.join('tools','utf8_util','utf8_8x8.bin')
    dest_file = os.path.join('tools','utf8_util','utf8_8x8.py')
else:
    source_file = 'utf8_8x8.bin'
    dest_file = 'utf8_8x8.py'


with open(source_file, 'rb') as source:
    with open(dest_file, 'w') as dest:
        dest.write(f"""\
_UTF8 = const({source.read()})
utf8 = memoryview(_UTF8)
""")

