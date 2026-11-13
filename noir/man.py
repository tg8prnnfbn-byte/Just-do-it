"""Наш нуарний герой: довге темне пальто, чорний светр під горло, кашкет, круглі темні окуляри, вуса.
П'ять ракурсів (спереду, 3/4 спереду, профіль, 3/4 ззаду, ззаду) × фази ходи. Висота 1.85 м."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw

import tex

INK = (14, 12, 16)
COAT = (52, 50, 58)
COAT_D = (36, 34, 42)
COAT_L = (74, 70, 80)
PANTS = (30, 30, 36)
SKIN = (222, 176, 140)
SKIN_D = (186, 140, 110)
CAP = (40, 38, 46)
W, H = 640, 1850        # 1 px = 1 мм


def _legs(d, cx, phase, spread=1.0, profile=False):
    st = math.sin(phase * 2 * math.pi)
    for side, s in ((-1, st), (1, -st)):
        if profile:
            hip = (cx, 1080)
            foot = (cx + s * 210, 1800)
            knee = (cx + s * 110, 1450 - abs(s) * 20)
        else:
            hip = (cx + side * 55 * spread, 1080)
            foot = (cx + side * 70 * spread, 1800 - max(0, s) * 50)
            knee = ((hip[0] + foot[0]) / 2, 1450)
        d.line([hip, knee, foot], fill=PANTS, width=78, joint="curve")
        sx = foot[0] + (s * 40 if profile else 0)
        d.ellipse((sx - 62, foot[1] - 22, sx + 62, foot[1] + 30), fill=(18, 16, 18), outline=INK, width=4)


def _coat_front(d, cx, phase, narrow=1.0, shift=0.0):
    sw = math.sin(phase * 2 * math.pi) * 30
    hw_top, hw_bot = 165 * narrow, 215 * narrow
    pts = [(cx - hw_top, 430), (cx + hw_top, 430), (cx + hw_bot + sw, 1340), (cx - hw_bot + sw, 1340)]
    d.polygon(pts, fill=COAT, outline=INK, width=6)
    d.polygon([(cx + hw_top * 0.3, 430), (cx + hw_top, 430), (cx + hw_bot + sw, 1340), (cx + hw_bot * 0.35 + sw, 1340)], fill=COAT_D)
    d.polygon([(cx - hw_top * 0.9, 440), (cx - hw_top * 0.55, 440), (cx - hw_bot * 0.6 + sw, 1330), (cx - hw_bot * 0.85 + sw, 1330)], fill=COAT_L)
    d.polygon(pts, outline=INK, width=6)
    # лацкани й светр під горло
    lc = cx + shift
    d.polygon([(lc - 70, 430), (lc + 70, 430), (lc + 40, 720), (lc - 40, 720)], fill=(12, 12, 16))
    d.polygon([(lc - 80, 430), (lc - 10, 760), (lc - 120, 600)], fill=COAT_L, outline=INK, width=4)
    d.polygon([(lc + 80, 430), (lc + 10, 760), (lc + 120, 600)], fill=COAT_D, outline=INK, width=4)
    for y in (820, 960, 1100):
        d.ellipse((lc - 12, y - 12, lc + 12, y + 12), fill=(20, 20, 24))
    # руки в кишенях: рукави вздовж боків
    for s in (-1, 1):
        x0 = cx + s * hw_top * 0.98
        d.line([(x0, 470), (x0 + s * 26, 800), (cx + s * hw_top * 0.75, 1000)], fill=COAT_D, width=70, joint="curve")
        d.line([(x0 + s * 30, 470), (x0 + s * 48, 800)], fill=INK, width=5)


def _head(d, cx, view="front"):
    # шия-светр
    d.rectangle((cx - 50, 360, cx + 50, 450), fill=(16, 16, 20), outline=INK, width=4)
    if view == "back":
        d.ellipse((cx - 95, 140, cx + 95, 390), fill=(30, 24, 22), outline=INK, width=6)   # потилиця: волосся
        d.chord((cx - 70, 300, cx + 70, 400), 0, 180, fill=SKIN_D)                          # шия
        for s_ in (-1, 1):
            d.ellipse((cx + s_ * 95 - 16, 240, cx + s_ * 95 + 12, 300), fill=SKIN_D, outline=INK, width=3)   # вуха
    elif view == "side":
        d.ellipse((cx - 90, 140, cx + 90, 390), fill=SKIN, outline=INK, width=6)
        d.polygon([(cx - 88, 250), (cx - 128, 300), (cx - 86, 312)], fill=SKIN, outline=INK, width=5)   # ніс
        d.chord((cx - 20, 150, cx + 100, 390), 270, 90, fill=(30, 24, 22))
        d.ellipse((cx - 92, 230, cx - 22, 280), fill=(10, 10, 14), outline=INK, width=4)                 # окуляр
        d.line((cx - 22, 250, cx + 40, 246), fill=INK, width=8)
        d.polygon([(cx - 92, 322), (cx - 40, 316), (cx - 50, 340), (cx - 96, 336)], fill=(24, 18, 16))  # вуса
    else:
        off = 0 if view == "front" else (-28 if view == "front34" else 0)
        d.ellipse((cx - 95, 140, cx + 95, 390), fill=SKIN, outline=INK, width=6)
        d.ellipse((cx + 20, 180, cx + 95, 380), fill=SKIN_D)
        d.ellipse((cx - 95, 140, cx + 95, 390), outline=INK, width=6)
        for s in (-1, 1):                                                                                 # круглі окуляри
            ex = cx + off + s * 45
            d.ellipse((ex - 40, 230, ex + 40, 300), fill=(10, 10, 14), outline=INK, width=5)
            d.ellipse((ex - 24, 240, ex - 8, 256), fill=(120, 120, 140))
        d.line((cx + off - 6, 258, cx + off + 6, 258), fill=INK, width=6)
        d.polygon([(cx + off - 60, 330), (cx + off, 314), (cx + off + 60, 330), (cx + off + 40, 346), (cx + off, 334),
                   (cx + off - 40, 346)], fill=(24, 18, 16))                                              # вуса
        d.line((cx + off - 20, 362, cx + off + 20, 362), fill=(120, 60, 60), width=6)
    # кашкет
    if view == "side":
        d.chord((cx - 100, 110, cx + 110, 280), 180, 360, fill=CAP, outline=INK, width=6)
        d.polygon([(cx - 100, 196), (cx - 170, 214), (cx - 96, 222)], fill=(24, 22, 28), outline=INK, width=4)
    else:
        d.chord((cx - 112, 100, cx + 112, 290), 180, 360, fill=CAP, outline=INK, width=6)
        if view != "back":
            d.chord((cx - 100, 170, cx + 100, 250), 0, 180, fill=(24, 22, 28), outline=INK, width=4)
        d.line((cx - 100, 196, cx + 100, 196), fill=INK, width=4)


@lru_cache(maxsize=64)
def sprite(view: str, phase8: int):
    """view: front | front34 | side | back34 | back; phase8: 0..7 — фаза кроку (−1 = стоїть)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W // 2
    ph = 0.0 if phase8 < 0 else phase8 / 8
    bob = 0 if phase8 < 0 else int(18 * abs(math.sin(ph * 2 * math.pi)))
    profile = view == "side"
    _legs(d, cx, ph if phase8 >= 0 else 0.0, spread=0.85 if "34" in view else 1.0, profile=profile)
    if profile:
        sw = math.sin(ph * 2 * math.pi) * 40
        d.polygon([(cx - 95, 430), (cx + 110, 430), (cx + 170 + sw, 1340), (cx - 150 + sw, 1340)], fill=COAT, outline=INK, width=6)
        d.polygon([(cx + 20, 430), (cx + 110, 430), (cx + 170 + sw, 1340), (cx + 40 + sw, 1340)], fill=COAT_D)
        d.polygon([(cx - 95, 430), (cx + 110, 430), (cx + 170 + sw, 1340), (cx - 150 + sw, 1340)], outline=INK, width=6)
        d.line([(cx, 470), (cx - 20, 800), (cx + 10, 1000)], fill=COAT_D, width=74, joint="curve")
        d.line([(cx + 34, 470), (cx + 14, 800)], fill=INK, width=5)
        d.polygon([(cx - 95, 430), (cx - 40, 430), (cx - 70, 620)], fill=COAT_L, outline=INK, width=4)
    elif view in ("back", "back34"):
        _coat_front(d, cx, ph, narrow=0.92 if view == "back34" else 1.0)
        d.rectangle((cx - 175, 430, cx + 175, 760), fill=COAT)       # ззаду без лацканів
        d.rectangle((cx - 34, 760, cx + 34, 1130), fill=COAT)
        d.line((cx, 760, cx, 1340), fill=INK, width=5)               # шов і хлястик
        d.rectangle((cx - 120, 760, cx + 120, 800), fill=COAT_D, outline=INK, width=4)
        d.polygon([(cx - 165, 430), (cx + 165, 430), (cx + 205, 1340), (cx - 205, 1340)], outline=INK, width=6)
    else:
        _coat_front(d, cx, ph, narrow=0.9 if view == "front34" else 1.0, shift=-26 if view == "front34" else 0)
    _head(d, cx, "back" if view.startswith("back") else ("side" if profile else view))
    img = tex.paint_noise(img, 0.05, 3)
    if bob:
        img = img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, bob), resample=Image.BILINEAR)
    return img
