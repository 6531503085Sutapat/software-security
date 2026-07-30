#!/usr/bin/env python3
"""Generate the site's raster brand assets from the KOSEN-KMITL palette.

    python3 tools/make_icons.py            # writes into ../static/

Why a generator and not three committed binaries: the assets are pure geometry
in two brand colours, and a reviewer cannot diff a PNG. This way the palette
lives in one place next to the CSS that uses the same hex values, and
regenerating after a brand tweak is one command instead of an image editor.

Pure stdlib on purpose — this repo's image has no Pillow, and adding a build-time
image dependency to ship three flat-colour rectangles would be a poor trade. PNG
is a simple enough container to emit directly: signature, IHDR, one zlib'd IDAT
of filter-0 scanlines, IEND.

favicon.svg is hand-written and is the primary icon; the PNGs exist for the
clients that still refuse SVG (Safari's touch icon, and the social crawlers,
which reject SVG for og:image outright).
"""
from __future__ import annotations

import os
import struct
import zlib

# The same values as static/style.css :root — keep them in step.
INK = (0x18, 0x15, 0x12)
KOSEN_BLUE = (0x01, 0x7B, 0xC4)
KMITL_ORANGE = (0xE3, 0x52, 0x05)
PAPER = (0xF5, 0xF2, 0xEC)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "static"))


class Canvas:
    """An RGB pixel buffer with the two primitives these assets need."""

    def __init__(self, w: int, h: int, bg=INK):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def rect(self, x, y, w, h, colour, radius=0):
        r2 = radius * radius
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                if radius:
                    # Only the four corner boxes can fall outside the round rect.
                    dx = dy = None
                    if xx < x + radius:
                        dx = x + radius - 1 - xx
                    elif xx >= x + w - radius:
                        dx = xx - (x + w - radius)
                    if yy < y + radius:
                        dy = y + radius - 1 - yy
                    elif yy >= y + h - radius:
                        dy = yy - (y + h - radius)
                    if dx is not None and dy is not None and dx * dx + dy * dy > r2:
                        continue
                i = (yy * self.w + xx) * 3
                self.px[i:i + 3] = bytes(colour)

    def png(self) -> bytes:
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)                      # filter: None
            raw += self.px[y * stride:(y + 1) * stride]

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


def mark(size: int) -> Canvas:
    """The tab icon: the wordmark's blue/orange pairing reduced to two blocks.

    At 16px nothing legible survives, so this is deliberately a colour signature
    rather than shrunken letters — which is what the tab actually needs.
    """
    c = Canvas(size, size)
    u = size / 64.0
    c.rect(0, 0, size, size, INK, radius=int(12 * u))
    c.rect(int(9 * u), int(15 * u), int(17 * u), int(34 * u), KOSEN_BLUE)
    c.rect(int(31 * u), int(15 * u), int(24 * u), int(34 * u), KMITL_ORANGE)
    c.rect(int(31 * u), int(28 * u), int(24 * u), int(8 * u), INK)
    return c


def og_card(w=1200, h=630) -> Canvas:
    """The link-preview card.

    No text: the platforms that render this also render og:title beside it, and
    hand-rasterising a typeface here would look worse than the type on the site.
    So it carries the brand colours and the three-course structure instead.
    """
    c = Canvas(w, h)
    c.rect(0, 0, w, 88, KMITL_ORANGE)                     # top rule

    bar_w, bar_h, gap = 208, 244, 44
    group_w = 3 * bar_w + 2 * gap
    x0 = (w - group_w) // 2                               # centred, not left-hung
    bar_y = 196
    for n, colour in enumerate((KOSEN_BLUE, KMITL_ORANGE, PAPER)):
        c.rect(x0 + n * (bar_w + gap), bar_y, bar_w, bar_h, colour, radius=10)

    # A baseline the width of the group: reads as a shelf the three courses
    # stand on, and stops the lower half looking abandoned.
    c.rect(x0, bar_y + bar_h + 56, group_w, 12, PAPER, radius=6)
    c.rect(x0, bar_y + bar_h + 56, bar_w, 12, KMITL_ORANGE, radius=6)
    return c


def main() -> None:
    for name, canvas in (("favicon.png", mark(32)),
                         ("apple-touch-icon.png", mark(180)),
                         ("og-card.png", og_card())):
        path = os.path.join(OUT, name)
        with open(path, "wb") as fh:
            fh.write(canvas.png())
        print(f"{path}  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
