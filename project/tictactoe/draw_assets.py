"""Draw the pictures the web front end uses: the board and the two pieces, in the course's colours.

Run in project/: python3 tictactoe/draw_assets.py   (writes tictactoe/templates/web/assets/, then build.py ships them in stage 5)
Standard library only, so nothing here is anyone else's picture. A teacher can replace the PNGs with their own: the
page only needs the same file names; it shows the board at 330 x 330 and each piece filling its cell.
"""
import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent / "templates" / "web" / "assets"
CELL = 110
SAND, LINE, CLAY, OLIVE = (0xF0, 0xEE, 0xE6), (0x3D, 0x3A, 0x35), (0xC6, 0x61, 0x3F), (0x5B, 0x6F, 0x45)


def png(path, width, height, pixel):
    """pixel(x, y) -> (r, g, b, a); written as an 8-bit RGBA PNG."""
    rows = b"".join(b"\0" + b"".join(bytes(pixel(x + 0.5, y + 0.5)) for x in range(width)) for y in range(height))
    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def segment(px, py, ax, ay, bx, by):
    """Distance from a point to the segment a-b: a stroke with round ends is every point closer than half its width."""
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def cover(distance, half):
    """How much of a pixel a stroke covers, so the edges come out smooth."""
    return max(0.0, min(1.0, half - distance + 0.5))


def over(base, colour, amount):
    return tuple(round(b + (c - b) * amount) for b, c in zip(base, colour))


def board(x, y):
    size = CELL * 3
    lines = [(CELL * k, 14, CELL * k, size - 14) for k in (1, 2)] + [(14, CELL * k, size - 14, CELL * k) for k in (1, 2)]
    ink = max(cover(segment(x, y, *line), 4) for line in lines)
    return over(SAND, LINE, ink) + (255,)


def cross(x, y):
    a = max(cover(segment(x, y, 30, 30, 80, 80), 8), cover(segment(x, y, 80, 30, 30, 80), 8))
    return CLAY + (round(255 * a),)


def ring(x, y):
    a = cover(abs(math.hypot(x - 55, y - 55) - 28), 7.5)
    return OLIVE + (round(255 * a),)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png(OUT / "board.png", CELL * 3, CELL * 3, board)
    png(OUT / "x.png", CELL, CELL, cross)
    png(OUT / "o.png", CELL, CELL, ring)
    for f in sorted(OUT.glob("*.png")):
        print("%s  %d bytes" % (f.relative_to(OUT.parents[3]), f.stat().st_size))


if __name__ == "__main__":
    main()
