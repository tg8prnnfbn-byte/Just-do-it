"""Локації для шортса про апное: нічна спальня з подвійним ліжком, кабінет лікаря, фон для пояснень."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "navushnyky"))
sys.path.insert(0, str(ROOT / "ekstrene" / "multyk2"))
import sets as N  # noqa: E402
import hsets  # noqa: E402,F401  (дерев'яна поверхня 'phone' для крупних планів)
from sets import canvas, ell, finish, glow, line, poly, rect, shade_c, window_light  # noqa: E402

BED_TOP = 1560   # де лежить ковдра (верхній край)


def bedroom2():
    W, H = 1500, 2500
    img = canvas(W, H, (66, 70, 128), (44, 44, 90))
    d = ImageDraw.Draw(img)
    rect(d, (120, 360, 560, 960), (34, 44, 96))                                    # вікно з місяцем
    ell(d, (380, 430, 480, 530), (236, 240, 255), ink=False)
    for x in range(140, 560, 70):
        poly(d, [(x, 960), (x + 35, 800 + (x % 3) * 30), (x + 70, 960)], (22, 28, 60), ink=False)
    rect(d, (120, 360, 560, 960), None)
    line(d, [(340, 360), (340, 960)], w=10, fill=(90, 96, 140))
    poly(d, [(90, 340), (180, 340), (150, 1000), (80, 1000)], (150, 90, 120))
    rect(d, (1040, 500, 1300, 760), (130, 100, 80))                                # картина
    rect(d, (1065, 525, 1275, 735), (110, 150, 140))
    rect(d, (0, 1700, W, H), (60, 48, 70), ink=False)
    line(d, [(0, 1700), (W, 1700)])
    rect(d, (230, 1000, 1270, 1500), (120, 74, 48), r=40)                          # узголів'я
    rect(d, (260, 1030, 1240, 1470), shade_c((120, 74, 48), 0.85), r=30)
    rect(d, (1290, 1450, 1480, 1500), (120, 74, 48))                               # тумбочка з лампою
    rect(d, (1300, 1500, 1470, 1800), shade_c((120, 74, 48), 0.7))
    rect(d, (1350, 1380, 1420, 1450), (200, 180, 140))
    poly(d, [(1320, 1260), (1450, 1260), (1480, 1380), (1290, 1380)], (240, 210, 150))
    for x in (330, 800):                                                            # подушки
        rect(d, (x, 1330, x + 370, 1520), (236, 236, 246), r=60)
    window_light(img, [(500, 1720), (900, 1720), (1150, 2300), (650, 2300)], 45)
    glow(img, (1180, 1150, 1600, 1600), (255, 210, 140), 70, 50)
    img = finish(img, sun=(0.85, 0.55), warm=0.10, texture=0.07, seed=31)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (200, BED_TOP, 1300, 2350), (120, 150, 200), r=50)                    # ковдра
    for x in range(260, 1300, 120):
        line(fd, [(x, BED_TOP + 20), (x + 30, 2330)], w=3, fill=(100, 128, 180, 255))
    rect(fd, (200, BED_TOP, 1300, BED_TOP + 70), (230, 232, 244), r=30)
    rect(fd, (180, 2300, 1320, 2500), (110, 70, 46))
    return img, fg


def panel():
    """М'який мальований фон для пояснень (як інфографіка в шортсах)."""
    W, H = 1400, 2400
    img = canvas(W, H, (70, 120, 170), (40, 70, 120))
    img = finish(img, sun=(0.35, 0.3), warm=0.06, texture=0.09, seed=32)
    return img, None


def doctor():
    W, H = 1500, 2500
    img = canvas(W, H, (214, 230, 226), (176, 200, 196))
    d = ImageDraw.Draw(img)
    rect(d, (880, 300, 1360, 900), (170, 210, 245))
    line(d, [(1120, 300), (1120, 900)], w=10, fill=(250, 250, 250))
    for i, x in enumerate((160, 420)):                                             # дипломи
        rect(d, (x, 420, x + 200, 640), (140, 100, 60))
        rect(d, (x + 18, 438, x + 182, 622), (246, 240, 222))
    rect(d, (0, 1600, W, H), (150, 140, 130), ink=False)
    line(d, [(0, 1600), (W, 1600)])
    window_light(img, [(500, 1620), (980, 1620), (1250, 2200), (700, 2200)], 70)
    img = finish(img, sun=(0.75, 0.2), warm=0.08, texture=0.07, seed=33)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (100, 1720, 1400, 1800), (180, 140, 100))                              # стіл
    rect(fd, (120, 1800, 1380, 2400), shade_c((180, 140, 100), 0.75))
    rect(fd, (560, 1590, 860, 1720), (236, 238, 242), r=24)                         # апарат CPAP
    rect(fd, (600, 1620, 700, 1680), (60, 140, 200), r=8)
    fd.arc([(820 * 2, 1560 * 2), (1060 * 2, 1760 * 2)], 180, 300, fill=(120, 150, 190), width=18)
    return img, fg


SETS = dict(bedroom2=bedroom2, panel=panel, doctor=doctor)
N.SETS.update(SETS)
