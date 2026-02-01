# coding: utf-8
from __future__ import print_function, unicode_literals

import os

try:
    if os.environ.get("PRTY_SYS_ALL") or os.environ.get("PRTY_SYS_QRCG"):
        raise ImportError()
    from .stolen.qrcodegen import QrCode

    qrgen = QrCode.encode_binary
    VENDORED = True
except ImportError:
    VENDORED = False
    from qrcodegen import QrCode

if os.environ.get("PRTY_MODSPEC"):
    from inspect import getsourcefile

    print("PRTY_MODSPEC: qrcode:", getsourcefile(QrCode))

if not VENDORED:

    def _qrgen(data  )  :
        ret = None
        V = QrCode.Ecc
        for e in [V.HIGH, V.QUARTILE, V.MEDIUM, V.LOW]:
            qr = QrCode.encode_binary(data, e)
            qr.size = qr._size
            qr.modules = qr._modules
            if not ret or ret.size > qr.size:
                ret = qr
        return ret

    qrgen = _qrgen


def qr2txt(qr , zoom  = 1, pad  = 4)  :
    tab = qr.modules
    sz = qr.size
    if sz % 2 and zoom == 1:
        tab.append([False] * sz)

    tab = [[False] * sz] * pad + tab + [[False] * sz] * pad
    tab = [[False] * pad + x + [False] * pad for x in tab]

    rows  = []
    if zoom == 1:
        for y in range(0, len(tab), 2):
            row = ""
            for x in range(len(tab[y])):
                v = 2 if tab[y][x] else 0
                v += 1 if tab[y + 1][x] else 0
                row += " ▄▀█"[v]
            rows.append(row)
    else:
        for tr in tab:
            row = ""
            for zb in tr:
                row += " █"[int(zb)] * 2
            rows.append(row)

    return "\n".join(rows)


def qr2png(
    qr ,
    zoom ,
    pad ,
    bg   ,
    fg   ,
    ap ,
)  :
    from PIL import Image

    tab = qr.modules
    sz = qr.size
    psz = sz + pad * 2
    if bg:
        img = Image.new("RGB", (psz, psz), bg)
    else:
        img = Image.new("RGBA", (psz, psz), (0, 0, 0, 0))
        fg = (fg[0], fg[1], fg[2], 255)
    for y in range(sz):
        for x in range(sz):
            if tab[y][x]:
                img.putpixel((x + pad, y + pad), fg)
    if zoom != 1:
        img = img.resize((sz * zoom, sz * zoom), Image.Resampling.NEAREST)
    img.save(ap)


def qr2svg(qr , border )  :
    parts  = []
    for y in range(qr.size):
        sy = border + y
        for x in range(qr.size):
            if qr.modules[y][x]:
                parts.append("M%d,%dh1v1h-1z" % (border + x, sy))
    t = """\
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {0} {0}" stroke="none">
<rect width="100%" height="100%" fill="#F7F7F7"/>
<path d="{1}" fill="#111111"/>
</svg>
"""
    return t.format(qr.size + border * 2, " ".join(parts))
