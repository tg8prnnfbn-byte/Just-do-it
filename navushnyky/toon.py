"""Мультяшні персонажі за правилами скіла cartoon-3d-short (у 2D, PIL).

Бобова голова h/w ~0.93, ~3.5 висоти голови, сливовий контур #241726, ноги-палички,
руки-палички з крапками-долонями, без рум'янцю й відблисків в очах, очі на 0.26 ширини голови.
Дизайн-полотно 600x1000, підошви на y=965.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

PLUM = (36, 23, 38)
INK = (11, 10, 12)


def shade(c, k=0.72, tint=(40, 40, 90)):
    """Тінь: темніше і в синьо-фіолетовий бік (ніколи не в коричневий)."""
    return tuple(int(v * k + t * (1 - k) * 0.6) for v, t in zip(c, tint))


def bean(cx, cy, w, h, n=48):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        s, c = math.sin(a), math.cos(a)
        x = w / 2 * c * (1 - 0.13 * max(0.0, s))          # вужче підборіддя
        y = h / 2 * s * (1.06 if s < 0 else 1.0)          # гостріша маківка
        pts.append((cx + x, cy + y))
    return pts


ARMS = {  # (лікоть, долоня) для правої руки, відносно центру; ліву дзеркалимо
    "down": ((105, 545), (112, 640)),
    "up": ((150, 370), (165, 270)),
    "ear": ((165, 410), (128, 300)),
    "hold": ((118, 560), (58, 540)),
    "out": ((165, 495), (232, 420)),
    "point": ((165, 455), (262, 410)),
    "write": ((120, 560), (70, 610)),
    "hip": ((150, 540), (95, 600)),
    "throw": ((140, 380), (215, 300)),
}

EXPR = ("smile", "grin", "shock", "squint", "sad", "laugh", "worry", "neutral", "proud")


@lru_cache(maxsize=256)
def person(k: float, skin=(242, 204, 170), hair=(74, 48, 32), hair_style="short", shirt=(92, 130, 190),
           pants=(60, 62, 82), hat=None, mustache=False, expr="smile", blink=False,
           arms=("down", "down"), headphones=False, apron=None, tie=None, sweat=False, hold=None, buttons=False):
    W, H = int(600 * k), int(1000 * k)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * k, y * k)

    def L(w):
        return max(1, int(w * k))

    cx = 300
    # ноги
    for s_ in (-1, 1):
        d.line([P(cx + s_ * 40, 680), P(cx + s_ * 48, 950)], fill=PLUM, width=L(12))
        d.ellipse([P(cx + s_ * 48 - 28 + s_ * 10, 937), P(cx + s_ * 48 + 28 + s_ * 10, 965)], fill=PLUM)
    # тулуб-капсула (як у зразку: одразу під головою, без шиї)
    d.rounded_rectangle([P(cx - 104, 395), P(cx + 104, 700)], radius=L(104), fill=shirt, outline=PLUM, width=L(6))
    d.rounded_rectangle([P(cx - 104, 395), P(cx + 104, 700)], radius=L(104), outline=PLUM, width=L(6))
    if apron:
        d.rounded_rectangle([P(cx - 66, 500), P(cx + 66, 690)], radius=L(24), fill=apron, outline=PLUM, width=L(4))
    if tie:
        d.polygon([P(cx - 12, 430), P(cx + 12, 430), P(cx + 18, 545), P(cx, 572), P(cx - 18, 545)], fill=tie, outline=PLUM)
    if buttons:
        for y in (470, 530, 590, 650):
            d.ellipse([P(cx + 8 - 9, y - 9), P(cx + 8 + 9, y + 9)], fill=PLUM)
    # руки
    for s, pose in ((-1, arms[0]), (1, arms[1])):
        (ex, ey), (hx, hy) = ARMS[pose]
        sh = P(cx + s * 96, 480)
        d.line([sh, P(cx + s * ex, ey), P(cx + s * hx, hy)], fill=PLUM, width=L(10), joint="curve")
        d.ellipse([P(cx + s * hx - 12, hy - 12), P(cx + s * hx + 12, hy + 12)], fill=PLUM)
    if hold:
        hold(d, P, L)
    # голова
    hc, hw, hh = 290, 252, 234
    head = bean(cx, hc, hw, hh)
    d.polygon([(x * k, y * k) for x, y in head], fill=skin)
    d.line([(x * k, y * k) for x, y in head] + [(head[0][0] * k, head[0][1] * k)], fill=PLUM, width=L(6), joint="curve")
    d.line([(x * k, y * k) for x, y in head[6:20]], fill=PLUM, width=L(8), joint="curve")   # товща нижня сторона
    # волосся
    if hair_style == "short":
        d.chord([P(cx - 128, hc - 128), P(cx + 128, hc + 30)], 180, 360, fill=hair)
        d.polygon([P(cx - 122, hc - 40), P(cx - 60, hc - 70), P(cx + 40, hc - 60), P(cx + 124, hc - 40),
                   P(cx + 120, hc - 80), P(cx - 120, hc - 80)], fill=hair)
    elif hair_style == "side":
        d.chord([P(cx - 130, hc - 130), P(cx + 130, hc + 20)], 180, 360, fill=hair)
        d.polygon([P(cx - 126, hc - 50), P(cx + 10, hc - 85), P(cx + 126, hc - 40), P(cx + 120, hc - 95)], fill=hair)
    elif hair_style == "bald":
        for s in (-1, 1):
            d.ellipse([P(cx + s * 118 - 18, hc - 30), P(cx + s * 118 + 18, hc + 30)], fill=hair)
    elif hair_style == "bun":
        d.chord([P(cx - 130, hc - 132), P(cx + 130, hc + 40)], 180, 360, fill=hair)
        d.ellipse([P(cx - 45, hc - 175), P(cx + 45, hc - 95)], fill=hair, outline=PLUM, width=L(6))
    # капелюхи
    if hat == "navy":
        d.rounded_rectangle([P(cx - 120, hc - 150), P(cx + 120, hc - 85)], radius=L(20), fill=(28, 36, 72), outline=PLUM, width=L(5))
        d.rectangle([P(cx - 118, hc - 100), P(cx + 118, hc - 86)], fill=(214, 172, 60))
        d.chord([P(cx - 30, hc - 112), P(cx + 150, hc - 60)], 0, 180, fill=(14, 14, 18))
    elif hat == "top":
        d.rectangle([P(cx - 72, hc - 270), P(cx + 72, hc - 110)], fill=(24, 22, 28), outline=PLUM, width=L(5))
        d.rectangle([P(cx - 72, hc - 150), P(cx + 72, hc - 125)], fill=(150, 40, 50))
        d.ellipse([P(cx - 135, hc - 128), P(cx + 135, hc - 92)], fill=(24, 22, 28), outline=PLUM, width=L(5))
    elif hat == "chef":
        for ox in (-55, 0, 55):
            d.ellipse([P(cx + ox - 60, hc - 250), P(cx + ox + 60, hc - 140)], fill=(250, 250, 248), outline=PLUM, width=L(6))
        d.rectangle([P(cx - 90, hc - 160), P(cx + 90, hc - 95)], fill=(250, 250, 248), outline=PLUM, width=L(6))
    # навушники
    if headphones:
        d.arc([P(cx - 140, hc - 175), P(cx + 140, hc + 60)], 190, 350, fill=(40, 34, 30), width=L(16))
        for s in (-1, 1):
            d.ellipse([P(cx + s * 128 - 32, hc - 40), P(cx + s * 128 + 32, hc + 40)], fill=(120, 78, 44), outline=PLUM, width=L(5))
            d.ellipse([P(cx + s * 128 - 14, hc - 16), P(cx + s * 128 + 14, hc + 16)], fill=(70, 44, 26))
        d.line([P(cx + 130, hc + 40), P(cx + 150, hc + 140), P(cx + 120, hc + 240)], fill=(40, 34, 30), width=L(5))
    # обличчя
    ex, ey = 33, hc + 2
    if blink or expr in ("squint", "laugh"):
        for s in (-1, 1):
            if expr == "laugh":
                d.arc([P(cx + s * ex - 14, ey - 6), P(cx + s * ex + 14, ey + 16)], 200, 340, fill=INK, width=L(6))
            else:
                d.line([P(cx + s * ex - 13, ey + 4), P(cx + s * ex + 13, ey + 4)], fill=INK, width=L(6))
    else:
        big = 1.35 if expr == "shock" else 1.0
        for s in (-1, 1):
            d.ellipse([P(cx + s * ex - 9 * big, ey - 13 * big), P(cx + s * ex + 9 * big, ey + 13 * big)], fill=INK)
    brows = {"worry": (12, -8), "sad": (10, -6), "shock": (-6, 0), "proud": (-4, 4), "squint": (6, 4)}.get(expr)
    if brows:
        inner, outer = brows
        for s in (-1, 1):
            d.line([P(cx + s * 14, ey - 30 - inner), P(cx + s * 50, ey - 30 - outer)], fill=PLUM, width=L(6))
    my = hc + 62
    if expr in ("smile", "proud"):
        d.arc([P(cx - 34, my - 26), P(cx + 34, my + 12)], 20, 160, fill=PLUM, width=L(7))
    elif expr in ("grin", "laugh"):
        d.chord([P(cx - 42, my - 30), P(cx + 42, my + 30)], 0, 180, fill=(150, 40, 50), outline=PLUM, width=L(6))
        d.rectangle([P(cx - 30, my), P(cx + 30, my + 7)], fill=(250, 250, 245))
    elif expr == "shock":
        d.ellipse([P(cx - 16, my - 14), P(cx + 16, my + 26)], fill=(110, 30, 40), outline=PLUM, width=L(5))
    elif expr in ("sad", "worry"):
        d.arc([P(cx - 30, my - 4), P(cx + 30, my + 30)], 200, 340, fill=PLUM, width=L(7))
    else:
        d.line([P(cx - 22, my), P(cx + 22, my)], fill=PLUM, width=L(6))
    if mustache:
        d.polygon([P(cx - 46, my - 14), P(cx, my - 26), P(cx + 46, my - 14), P(cx + 30, my - 4), P(cx, my - 12),
                   P(cx - 30, my - 4)], fill=hair)
    if sweat:
        d.polygon([P(cx + 118, hc - 70), P(cx + 132, hc - 34), P(cx + 104, hc - 34)], fill=(140, 200, 245))
        d.ellipse([P(cx + 102, hc - 50), P(cx + 134, hc - 18)], fill=(140, 200, 245), outline=PLUM, width=L(4))
    return lit(img, k)


def lit(img, k):
    """Об'ємна світлотінь: світло зліва-згори, тінь праворуч у синьо-фіолетовий бік.
    Обличчя лише злегка (у зразку обличчя світлі)."""
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(-1, 1, h)[:, None]
    g = np.clip(0.5 + 0.55 * (xs * 0.9 + ys * 0.25), 0, 1)           # 0 = світло, 1 = тінь
    g = g * g * (3 - 2 * g)
    head = (np.arange(h)[:, None] < 420 * k)
    strength = np.where(head, 0.35, 1.0)
    shadow = np.array([70, 70, 140], np.float32)
    rgb = a[..., :3]
    lit_ = rgb * (1.06 - 0.06 * g[..., None]) + np.array([12, 8, 0]) * (1 - g[..., None])
    shd = rgb * 0.62 + shadow * 0.38 * (rgb / 255.0 + 0.2)
    mix = (g * strength)[..., None] * 0.75
    a[..., :3] = lit_ * (1 - mix) + shd * mix
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


# ---------- персонажі історії ----------
BALDWIN = dict(skin=(240, 200, 165), hair=(96, 64, 40), hair_style="side", shirt=(232, 226, 205),
               pants=(70, 60, 54), mustache=True, tie=(140, 50, 50))
BALDWIN_RICH = dict(BALDWIN, shirt=(52, 44, 70), tie=(214, 172, 60), hat="top")
OFFICER = dict(skin=(236, 196, 160), hair=(40, 34, 30), hair_style="short", shirt=(40, 58, 128),
               pants=(28, 34, 70), hat="navy", buttons=True)
OFFICER2 = dict(OFFICER, skin=(212, 160, 120), hair=(30, 24, 22), mustache=True)
JUDGE = dict(skin=(238, 206, 176), hair=(214, 214, 214), hair_style="bald", shirt=(40, 36, 50), pants=(22, 20, 26))
PREACHER = dict(skin=(236, 200, 168), hair=(190, 190, 190), hair_style="bald", shirt=(30, 30, 36), pants=(30, 30, 36))
WORKERS = [
    dict(skin=(240, 202, 168), hair=(80, 50, 30), hair_style="bun", shirt=(200, 90, 80), apron=(232, 222, 196)),
    dict(skin=(214, 168, 128), hair=(30, 26, 24), hair_style="short", shirt=(90, 140, 120), apron=(232, 222, 196)),
    dict(skin=(244, 210, 180), hair=(210, 160, 80), hair_style="bun", shirt=(120, 110, 190), apron=(232, 222, 196)),
    dict(skin=(226, 186, 150), hair=(60, 40, 30), hair_style="side", shirt=(210, 160, 70), apron=(232, 222, 196)),
]
CHEF = dict(BALDWIN, shirt=(250, 250, 248), hat="chef", tie=None)
