"""Світла сучасна вітальня: великі вікна, бежевий диван, рослини, вхідні двері праворуч."""
from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "navushnyky"))
import sets as N  # noqa: E402
from sets import canvas, ell, finish, glow, line, poly, rect, shade_c, window_light  # noqa: E402

FLOOR_Y = 1900
DOOR = (2050, 760, 2450, 1900)      # проріз вхідних дверей


def leaf(d, cx, cy, w, h, ang, col):
    import math
    a = math.radians(ang)
    pts = []
    for i in range(16):
        u = i / 15
        r = math.sin(math.pi * u) * w
        px, py = u * h, r
        pts.append((px, py))
    pts += [(u * h, -math.sin(math.pi * u) * w) for u in [i / 15 for i in range(15, -1, -1)]]
    rot = [(cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
    poly(d, rot, col, w=3)


def plant(d, x, y, scale=1.0, seed=1):
    rnd = random.Random(seed)
    rect(d, (x - 90 * scale, y - 200 * scale, x + 90 * scale, y), (200, 120, 80), r=20)
    for i in range(9):
        ang = rnd.uniform(-160, -20)
        leaf(d, x, y - 190 * scale, 60 * scale, rnd.uniform(260, 420) * scale, ang,
             rnd.choice([(70, 150, 80), (60, 130, 70), (90, 170, 90)]))


def living():
    W, H = 2600, 2600
    img = canvas(W, H, (246, 232, 210), (226, 206, 180))
    d = ImageDraw.Draw(img)
    # великі вікна з видом на зелень і небо
    for x0 in (120, 760):
        rect(d, (x0, 260, x0 + 560, 1420), (170, 214, 248))
        rect(d, (x0, 1050, x0 + 560, 1420), (130, 190, 120), ink=False)
        for k in range(4):
            ell(d, (x0 + 40 + k * 130, 900, x0 + 200 + k * 130, 1120), (100, 170, 100), ink=False)
        rect(d, (x0, 260, x0 + 560, 1420), None)
        line(d, [(x0 + 280, 260), (x0 + 280, 1420)], w=14, fill=(250, 250, 250))
        line(d, [(x0, 840), (x0 + 560, 840)], w=14, fill=(250, 250, 250))
    rect(d, (80, 1420, 1360, 1460), (250, 250, 250))
    # вхідні двері (проріз з коридором; полотно малюється в кадрі)
    x0, y0, x1, y1 = DOOR
    rect(d, (x0 - 30, y0 - 30, x1 + 30, y1), (250, 246, 238))
    rect(d, (x0, y0, x1, y1), (150, 130, 110))
    rect(d, (x0 + 40, y0 + 40, x1 - 40, y1), (180, 160, 140), ink=False)
    # підлога
    rect(d, (0, FLOOR_Y, W, H), (196, 150, 104), ink=False)
    for y in range(FLOOR_Y + 40, H, 90):
        line(d, [(0, y), (W, y)], w=3, fill=(176, 130, 88))
    line(d, [(0, FLOOR_Y), (W, FLOOR_Y)])
    ell(d, (380, 1980, 1900, 2420), (226, 120, 100))                                   # килим
    ell(d, (460, 2020, 1820, 2380), (240, 150, 120), ink=False)
    window_light(img, [(300, 1920), (1300, 1920), (1700, 2500), (600, 2500)], 70)
    d = ImageDraw.Draw(img)
    # бежевий диван
    sofa = (226, 204, 170)
    rect(d, (1180, 1300, 2000, 1640), sofa, r=60)
    rect(d, (1120, 1560, 2060, 1820), shade_c(sofa, 0.92), r=50)
    for x in (1100, 1960):
        rect(d, (x, 1440, x + 120, 1820), shade_c(sofa, 0.85), r=50)
    for x in (1240, 1600):
        rect(d, (x, 1380, x + 330, 1600), (236, 216, 184), r=50)
    rect(d, (1300, 1560, 1360, 1640), (240, 170, 80), r=20)                           # подушка-акцент
    for x in (1150, 2010):
        rect(d, (x, 1820, x + 30, 1900), (120, 80, 50))
    plant(d, 150, 1960, 1.4, seed=2)
    plant(d, 2550, 1960, 1.1, seed=3)
    rect(d, (500, 2080, 1000, 2140), (150, 100, 64), r=12)                              # журнальний столик
    for x in (530, 950):
        rect(d, (x, 2140, x + 26, 2260), (120, 80, 50))
    glow(img, (100, 300, 1500, 2100), (255, 246, 210), 70, 90)
    img = finish(img, sun=(0.22, 0.25), warm=0.08, texture=0.06, seed=51)
    return img, None


def door_leaf(P, open_):
    """Полотно дверей обертається на завісах ліворуч: open_ 0..1."""
    x0, y0, x1, y1 = DOOR
    w = (x1 - x0) * (1 - 0.85 * open_)
    P.rect(x1 - w, y0, x1, y1, (236, 230, 222) if open_ < 0.5 else (214, 206, 196), w=4)
    P.ell(x1 - w + 40, (y0 + y1) / 2, 16, 16, (200, 170, 80), w=3)


SETS = dict(living=living)
N.SETS.update(SETS)
