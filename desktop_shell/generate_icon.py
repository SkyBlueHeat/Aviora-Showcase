"""Generate a simple placeholder .ico file for JobTracker PRO.
Creates a 32x32 icon with an indigo background and white "J" letter.
Run: python desktop_shell/generate_icon.py
"""
import struct
import os

def create_ico(path: str):
    width = 32
    height = 32
    # ICO header
    ico = bytearray()
    # ICONDIR header (6 bytes)
    ico += struct.pack('<HHH', 0, 1, 1)  # reserved, type=1 (icon), count=1
    # ICONDIRENTRY (16 bytes)
    bmp_size = 40 + (width * height * 4) + (width * height // 8)  # header + pixels + mask
    ico += struct.pack('<BBBBHHII',
        width % 256, height % 256, 0, 0,  # width, height, palette, reserved
        1, 32,                             # color count, bits per pixel
        bmp_size,                          # size of image data
        22                                 # offset to image data (6 + 16)
    )
    # BITMAPINFOHEADER (40 bytes)
    ico += struct.pack('<IiiHHIIiiII',
        40,          # header size
        width,       # width
        height * 2,  # height (doubled for icon: XOR + AND mask)
        1,           # planes
        32,          # bits per pixel
        0,           # compression (BI_RGB)
        0,           # image size
        0, 0,        # x/y pixels per meter
        0, 0         # colors used, important colors
    )
    # Pixel data (BGRA, bottom-up)
    indigo = (99, 102, 241, 255)   # #6366F1 in BGRA
    white = (255, 255, 255, 255)
    # Simple "J" pattern on indigo background
    j_pattern = [
        "00000000",
        "00111100",
        "00010000",
        "00010000",
        "00010000",
        "01010000",
        "00110000",
        "00000000",
    ]
    # Pad to 8x8 centered in 32x32
    for y in range(height):
        for x in range(width):
            # Check if this pixel is part of the "J"
            jx = x - 12  # center the 8x8 pattern
            jy = y - 12
            if 0 <= jx < 8 and 0 <= jy < 8:
                if j_pattern[jy][jx] == '1':
                    ico += struct.pack('BBBB', *white)
                else:
                    ico += struct.pack('BBBB', *indigo)
            else:
                ico += struct.pack('BBBB', *indigo)
    # AND mask (1 bit per pixel, all zeros = fully opaque)
    for y in range(height):
        for x in range(0, width, 8):
            ico += struct.pack('B', 0)

    with open(path, 'wb') as f:
        f.write(ico)
    print(f"Created {path} ({len(ico)} bytes)")

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    create_ico(os.path.join(here, 'icon.ico'))
