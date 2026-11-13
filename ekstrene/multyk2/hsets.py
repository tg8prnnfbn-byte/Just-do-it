"""Нічні локації для мультяшної Серії 2 хорору (стиль навушників: тонкий контур, фактура, тіні)."""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "navushnyky"))
import sets as N  # noqa: E402
from sets import B, S, canvas, ell, finish, glow, line, poly, rect, shade_c, window_light  # noqa: E402

MOON = (200, 214, 255)


def pines(d, x0, x1, base, top, shade, n, seed, scale=1.0):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        h = rnd.uniform(top[0], top[1]) * scale
        w = h * 0.32
        for tier in range(5):
            ty = base - h + h * 0.78 * tier / 5
            tw = w * (0.35 + 0.65 * tier / 5)
            d.polygon([(px * S, py * S) for px, py in [(x, ty), (x - tw / 2, ty + h * 0.26), (x + tw / 2, ty + h * 0.26)]], fill=shade)
        d.rectangle(B((x - w * 0.05, base - h * 0.1, x + w * 0.05, base)), fill=shade)


def bedroom():
    W, H = 1500, 2500
    img = canvas(W, H, (52, 56, 108), (34, 34, 72))
    d = ImageDraw.Draw(img)
    rect(d, (280, 380, 860, 1100), (30, 40, 90))                                    # вікно
    ell(d, (640, 450, 760, 570), (236, 240, 255), ink=False)
    pines(d, 280, 860, 1100, (300, 520), (14, 18, 40), 9, 3)
    rect(d, (280, 380, 860, 1100), None)
    line(d, [(570, 380), (570, 1100)], w=12, fill=(70, 76, 120))
    line(d, [(280, 740), (860, 740)], w=12, fill=(70, 76, 120))
    rect(d, (250, 1090, 890, 1130), (80, 86, 130))
    poly(d, [(230, 360), (330, 360), (300, 1150), (210, 1150)], (90, 60, 110))      # фіранки
    rect(d, (0, 1500, W, H), (48, 40, 70), ink=False)
    for x in range(0, W, 110):
        line(d, [(x, 1500), (x - 160, H)], w=3, fill=(40, 34, 60))
    line(d, [(0, 1500), (W, 1500)])
    rect(d, (1080, 640, 1300, 900), (80, 70, 110))                                  # картина
    rect(d, (1110, 670, 1270, 870), (110, 120, 160))
    window_light(img, [(700, 1520), (1100, 1520), (1380, 2150), (900, 2150)], 55)
    img = finish(img, shadow=None, sun=(0.38, 0.22), warm=-0.05, texture=0.07, seed=21)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (-40, 1720, 900, 2500), (70, 80, 130), r=40)                            # ліжко з ковдрою
    rect(fd, (-40, 1640, 300, 1780), (220, 220, 236), r=50)
    for x in range(40, 900, 140):
        line(fd, [(x, 1760), (x + 40, 2480)], w=4, fill=(60, 66, 110, 255))
    rect(fd, (980, 1700, 1380, 1760), (110, 70, 50))                                 # тумбочка
    rect(fd, (1000, 1760, 1360, 2200), shade_c((110, 70, 50), 0.7))
    return img, fg


def phone_close():
    W, H = 1300, 2300
    img = canvas(W, H, (70, 44, 34), (40, 26, 22))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 70):
        line(d, [(0, y), (W, y + 40)], w=3, fill=(56, 36, 28))
    img = finish(img, sun=(0.5, 0.45), warm=0.02, texture=0.08, seed=22)
    return img, None


def hallway():
    W, H = 1400, 2500
    img = canvas(W, H, (40, 42, 80), (26, 26, 52))
    d = ImageDraw.Draw(img)
    rect(d, (520, 500, 900, 1800), (14, 14, 26))                                      # дверний отвір
    rect(d, (860, 520, 890, 1790), (255, 220, 150), ink=False)                       # щілина світла
    rect(d, (0, 1800, W, H), (36, 32, 56), ink=False)
    line(d, [(0, 1800), (W, 1800)])
    poly(d, [(860, 1800), (890, 1800), (1300, H), (700, H)], (120, 100, 80), ink=False)
    img = finish(img, sun=(0.62, 0.45), warm=0.12, texture=0.07, seed=23)
    glow(img, (760, 500, 1000, 1800), (255, 200, 130), 60, 50)
    return img, None


def forest():
    W, H = 1600, 2600
    img = canvas(W, H, (30, 40, 90), (16, 20, 46))
    d = ImageDraw.Draw(img)
    ell(d, (1050, 260, 1250, 460), (236, 240, 255), ink=False)
    glow(img, (900, 120, 1400, 600), MOON, 60, 60)
    d = ImageDraw.Draw(img)
    for layer, (shade, n, base, sc) in enumerate([((44, 54, 100), 26, 1500, 0.7), ((28, 34, 70), 18, 1800, 1.0)]):
        pines(d, -80, W + 80, base, (600, 900), shade, n, 30 + layer, sc)
        d.rectangle(B((0, base, W, H)), fill=shade)
        fog = Image.new("L", img.size, 0)
        ImageDraw.Draw(fog).rectangle(B((0, base - 260, W, base + 60)), fill=70)
        img.paste(Image.new("RGB", img.size, (90, 100, 150)), (0, 0), fog.filter(ImageFilter.GaussianBlur(70 * S)))
        d = ImageDraw.Draw(img)
    img = finish(img, sun=(0.7, 0.1), warm=-0.06, texture=0.06, seed=24)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rnd = random.Random(9)
    for _ in range(7):                                                               # чорні сосни спереду
        x = rnd.choice([rnd.uniform(-100, 350), rnd.uniform(1250, 1700)])
        pines(fd, x, x + 1, 2600, (1500, 1900), (8, 8, 18, 255), 1, rnd.randint(0, 99))
    return img, fg


def road():
    W, H = 1500, 2700
    img = canvas(W, H, (34, 44, 96), (22, 26, 56))
    d = ImageDraw.Draw(img)
    cx = 760                                                                          # щогла станції на пагорбі
    for s in (-1, 1):
        line(d, [(cx + s * 6, 520), (cx + s * 60, 1150)], w=5, fill=(16, 18, 30))
    for k in range(10):
        y1, y2 = 520 + 63 * k, 520 + 63 * (k + 1)
        w1, w2 = 6 + 5.4 * k, 6 + 5.4 * (k + 1)
        line(d, [(cx - w1, y1), (cx + w2, y2)], w=3, fill=(16, 18, 30))
        line(d, [(cx + w1, y1), (cx - w2, y2)], w=3, fill=(16, 18, 30))
    ell(d, (cx - 10, 490, cx + 10, 510), (230, 50, 40), ink=False)
    pines(d, -80, 620, 1500, (500, 800), (24, 30, 62), 12, 41)
    pines(d, 900, 1580, 1500, (500, 800), (24, 30, 62), 12, 42)
    poly(d, [(700, 1200), (820, 1200), (1500, 2700), (0, 2700)], (50, 52, 70), ink=False)        # дорога
    poly(d, [(0, 1500), (700, 1200), (0, 2700)], (22, 28, 50), ink=False)
    poly(d, [(1500, 1500), (820, 1200), (1500, 2700)], (22, 28, 50), ink=False)
    for k in range(9):
        f = (k / 9) ** 1.7
        y = 1220 + 1480 * f
        poly(d, [(758 - 4 - 30 * f, y), (762 + 4 + 30 * f, y), (762 + 4 + 34 * f, y + 30 + 120 * f), (758 - 4 - 34 * f, y + 30 + 120 * f)],
             (220, 210, 150), ink=False)
    img = finish(img, sun=(0.5, 0.3), warm=-0.04, texture=0.06, seed=25)
    return img, None


def station_room():
    W, H = 1500, 2500
    img = canvas(W, H, (110, 118, 140), (80, 84, 100))
    d = ImageDraw.Draw(img)
    rect(d, (900, 300, 1350, 900), (190, 200, 215))                                   # вікно, сірий світанок
    line(d, [(1125, 300), (1125, 900)], w=10, fill=(90, 90, 100))
    rnd = random.Random(5)
    for row, y in enumerate((700, 1100, 1500)):                                       # полиці з касетами
        rect(d, (80, y, 860, y + 30), (110, 80, 56))
        x = 100
        while x < 820:
            w = rnd.uniform(40, 60)
            rect(d, (x, y - 170, x + w, y), rnd.choice([(30, 30, 34), (44, 44, 50), (60, 56, 52)]), r=4)
            rect(d, (x + 6, y - 150, x + w - 6, y - 110), (200, 194, 170), ink=False)
            x += w + 10
    rect(d, (0, 1800, W, H), (70, 70, 80), ink=False)
    line(d, [(0, 1800), (W, 1800)])
    window_light(img, [(700, 1820), (1160, 1820), (1420, 2400), (880, 2400)], 60)
    img = finish(img, shadow=None, sun=(0.75, 0.2), warm=0.0, texture=0.08, seed=26)
    return img, None


SETS = dict(bedroom=bedroom, phone=phone_close, hallway=hallway, forest=forest, road=road, station=station_room)
N.SETS.update(SETS)
