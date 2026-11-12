#!/usr/bin/env python3
"""«The Kitchen Headphones» — мультяшний шортс 1080x1920, 30 fps за правилами скіла cartoon-3d-short.

Камера: ковзання smootherstep, кожна статична пауза повільно наїжджає, поштовхи на ударах
(знак міняється щокадру, згасання за 7 кадрів), нахили 4°, білий спалах після хука,
перехресні розчинення 7 кадрів при зміні місця. Розмитий фон на крупних планах. Без субтитрів.

    python3 navushnyky/film.py navushnyky/out/video.mp4 [--from 0 --to 59] [--stills 1,5,9]
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import sets
import toon as T

HERE = Path(__file__).resolve().parent
FPS = 30
OW, OH = 1080, 1920
S = sets.S
INK = sets.INK
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120 * S)

LINES = json.load(open(HERE / "voice" / "lines.json"))
WORDS = json.load(open(HERE / "voice" / "words.json"))
DUR = LINES[-1]["e"] + 0.45


def Ls(i, lead=0.07):
    return LINES[i]["s"] - lead


def Wt(word, after=0.0):
    for w in WORDS:
        if w["s"] >= after and word.lower() in w["w"].lower():
            return w["s"]
    raise KeyError(word)


def ss(x):  # smootherstep
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


# ---------- малювання з урахуванням зсуву кадрування ----------
class Pen:
    def __init__(self, img, ox, oy):
        self.img, self.d, self.ox, self.oy = img, ImageDraw.Draw(img, "RGBA"), ox, oy

    def p(self, x, y):
        return (x * S - self.ox, y * S - self.oy)

    def poly(self, pts, fill, ink=True, w=6):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=INK if ink else None, width=w if ink else 0)

    def ell(self, cx, cy, rx, ry, fill, ink=True, w=6):
        a, b = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        self.d.ellipse([a, b], fill=fill, outline=INK if ink else None, width=w if ink else 0)

    def rect(self, x0, y0, x1, y1, fill, ink=True, w=6, r=0):
        a, b = self.p(x0, y0), self.p(x1, y1)
        if r:
            self.d.rounded_rectangle([a, b], radius=r * S, fill=fill, outline=INK if ink else None, width=w if ink else 0)
        else:
            self.d.rectangle([a, b], fill=fill, outline=INK if ink else None, width=w if ink else 0)

    def line(self, pts, w=6, fill=INK):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=w, joint="curve")

    def arc(self, cx, cy, r, a0, a1, w=6, fill=INK):
        a, b = self.p(cx - r, cy - r), self.p(cx + r, cy + r)
        self.d.arc([a, b], a0, a1, fill=fill, width=w)

    def sprite(self, spr, x, y_feet, k):
        self.img.alpha_composite(spr, (int(x * S - spr.width / 2 - self.ox), int(y_feet * S - 965 * k - self.oy))) \
            if self._inside(spr, x, y_feet, k) else None

    def _inside(self, spr, x, y, k):
        px, py = int(x * S - spr.width / 2 - self.ox), int(y * S - 965 * k - self.oy)
        return px < self.img.width and py < self.img.height and px + spr.width > 0 and py + spr.height > 0 \
            and px > -10 ** 5


# ---------- ефекти й предмети ----------
def star(P, cx, cy, r, fill=(255, 236, 120), n=4, rot=0.0):
    pts = []
    for i in range(n * 2):
        a = rot + math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    P.poly(pts, fill, w=5)


def sparkles(P, cx, cy, t, spread=160, n=5, seed=0):
    rnd = np.random.default_rng(seed)
    for i in range(n):
        ph = (t * 1.6 + rnd.uniform(0, 1)) % 1.0
        r = 34 * math.sin(math.pi * ph)
        if r > 3:
            star(P, cx + rnd.uniform(-spread, spread), cy + rnd.uniform(-spread, spread) * 0.8, r)


def waves(P, cx, cy, t, side=1, n=3, color=INK, scale=1.0):
    for i in range(n):
        ph = (t * 1.3 + i / n) % 1.0
        r = (40 + 120 * ph) * scale
        a0, a1 = (-40, 40) if side > 0 else (140, 220)
        P.arc(cx, cy, r, a0, a1, w=int(8 * (1 - ph)) + 2, fill=color)


def burst(P, cx, cy, r, text="!"):
    star(P, cx, cy, r, fill=(255, 222, 70), n=9)
    tw = P.d.textlength(text, font=FONT)
    x, y = P.p(cx, cy)
    P.d.text((x - tw / 2, y - 75 * S), text, font=FONT, fill=INK)


def headset(P, cx, cy, s=1.0, col=(120, 78, 44)):
    P.arc(cx, cy, 46 * s, 190, 350, w=int(9 * s) + 2, fill=(40, 34, 30))
    for sx in (-1, 1):
        P.ell(cx + sx * 44 * s, cy + 6 * s, 16 * s, 20 * s, col, w=5)


def thought(P, cx, cy, t):
    for i, (dx, dy, r) in enumerate(((-210, 330, 22), (-170, 260, 34))):
        P.ell(cx + dx, cy + dy, r, r, (255, 255, 255))
    for dx, dy, r in ((-90, 40, 110), (60, -20, 130), (190, 40, 110), (60, 110, 130), (-40, 120, 100)):
        P.ell(cx + dx, cy + dy, r, r * 0.8, (255, 255, 255), ink=False)
    P.ell(cx + 50, cy + 40, 290, 170, None, w=6)
    P.ell(cx + 50, cy + 40, 286, 166, (255, 255, 255), ink=False)
    # кораблик
    bob = 8 * math.sin(t * 4)
    P.poly([(cx - 130, cy + 60 + bob), (cx + 230, cy + 60 + bob), (cx + 190, cy + 120 + bob), (cx - 100, cy + 120 + bob)], (90, 94, 110))
    P.rect(cx - 40, cy - 10 + bob, cx + 120, cy + 60 + bob, (200, 200, 210))
    P.rect(cx + 20, cy - 70 + bob, cx + 50, cy - 10 + bob, (60, 60, 70))
    P.line([(cx - 150, cy + 130), (cx + 250, cy + 130)], w=6, fill=(60, 110, 170))


def coins(P, t, x0, x1, y0, y1, n=14, seed=3):
    rnd = np.random.default_rng(seed)
    for i in range(n):
        x = rnd.uniform(x0, x1)
        sp = rnd.uniform(500, 900)
        y = y0 + ((t * sp + rnd.uniform(0, y1 - y0)) % (y1 - y0))
        w = 30 * abs(math.cos(t * 6 + i))
        P.ell(x, y, max(5, w), 30, (240, 196, 70), w=5)


def winged_money(P, cx, cy, t):
    flap = 30 * math.sin(t * 18)
    P.poly([(cx - 40, cy), (cx - 130, cy - 60 - flap), (cx - 70, cy + 10)], (255, 255, 255), w=5)
    P.poly([(cx + 40, cy), (cx + 130, cy - 60 - flap), (cx + 70, cy + 10)], (255, 255, 255), w=5)
    P.rect(cx - 70, cy - 30, cx + 70, cy + 30, (130, 190, 110), r=6)
    P.ell(cx, cy, 18, 18, (100, 160, 90), w=4)


def gavel(P, cx, cy, ang):
    a = math.radians(ang)
    hx, hy = cx + 170 * math.cos(a), cy - 170 * math.sin(a)
    P.line([(cx, cy), (hx, hy)], w=16, fill=(110, 64, 36))
    nx, ny = -math.sin(a), -math.cos(a)
    P.poly([(hx + nx * 50 - 30 * math.cos(a), hy + ny * 50 + 30 * math.sin(a)),
            (hx + nx * 50 + 30 * math.cos(a), hy + ny * 50 - 30 * math.sin(a)),
            (hx - nx * 50 + 30 * math.cos(a), hy - ny * 50 - 30 * math.sin(a)),
            (hx - nx * 50 - 30 * math.cos(a), hy - ny * 50 + 30 * math.sin(a))], (130, 80, 48))


def blink(t, seed):
    period = 1.3 + (seed % 5) * 0.25
    return ((t + seed * 0.37) % period) < 4 / FPS


def actor(P, spec, x, y, h, t, seed=0, bob=0.0, **over):
    k = h / 500.0
    sp = dict(spec)
    sp.update(over)
    if "blink" not in over:
        sp["blink"] = blink(t, seed)
    spr = T.person(round(k, 3), **sp)
    cs = contact_shadow(int(h * 0.34))
    P.img.alpha_composite(cs, (int(x * S - cs.width / 2 - P.ox), int(y * S - cs.height / 2 - P.oy))) \
        if -cs.width < x * S - P.ox < P.img.width and -cs.height < y * S - P.oy < P.img.height else None
    P.sprite(spr, x, y - bob * h * 0.03 * abs(math.sin(t * 6 + seed)), k)


@lru_cache(maxsize=64)
def contact_shadow(w):
    """М'яка тінь під ногами: щільна посередині, розмита по краях."""
    W, H = w * S, int(w * 0.3) * S
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse((W * 0.12, H * 0.2, W * 0.88, H * 0.8), fill=150)
    m = m.filter(ImageFilter.GaussianBlur(H * 0.18))
    img = Image.new("RGBA", (W, H), (20, 16, 50, 0))
    img.putalpha(m)
    return img


# ---------- план кадрів ----------
def kitchen_baldwin(P, t, **o):
    actor(P, T.BALDWIN, 760, 2050, 1150, t, seed=1, **o)


SHOTS = []


def shot(name, set_name, a, b, cams, draw_mid=None, draw_front=None, dof=None, creep=0.0016, kicks=(), xfade=False):
    if dof is None:                                    # розмитий фон на середніх/крупних планах, загальні — різкі
        dof = 0 if set_name in ("town", "fext", "desk", "fint") else 5
    SHOTS.append(dict(name=name, set=set_name, a=a, b=b, cams=cams, mid=draw_mid, front=draw_front, dof=dof,
                      creep=creep, kicks=list(kicks), xfade=xfade))


def build_shots():
    SHOTS.clear()
    # 1. Хук: Болдвін за кухонним столом у навушниках
    shot("hook", "kitchen", 0.0, Ls(1),
         [(0, 760, 1250, 1500, 0)],
         draw_mid=lambda P, t, lt: kitchen_baldwin(P, t, expr="grin", headphones=True, arms=("hold", "hold")),
         draw_front=lambda P, t, lt: (waves(P, 940, 1270, t, 1), waves(P, 580, 1270, t, -1), sparkles(P, 760, 1000, t, 300)),
         dof=6)
    # 2. Юта, храм
    shot("town", "town", Ls(1), Ls(2), [(0, 750, 1250, 1900, 0), (1.25, 750, 1700, 1650, 0)])
    # 3. Не чує проповідь
    def church3(P, t, lt):
        actor(P, T.PREACHER, 700, 1520, 330, t, seed=4, arms=("up", "point"), expr="smile")
        waves(P, 760, 1300, t, 1, scale=0.4)

    def church3f(P, t, lt):
        actor(P, T.BALDWIN, 930, 2700, 1350, t, seed=2, expr="squint", arms=("down", "ear"))

    shot("pew", "church", Ls(2), Ls(3), [(0, 820, 1650, 1500, 0), (2.4, 860, 1720, 1300, 0)],
         draw_mid=church3, draw_front=church3f, dof=10)
    # 4. Будує навушники на кухні
    t_build = Wt("builds", LINES[3]["s"])

    def build_mid(P, t, lt):
        done = t >= t_build + 0.3
        kitchen_baldwin(P, t, expr="grin" if done else "squint", headphones=done,
                        arms=("up", "up") if done else ("write", "write"))

    def build_front(P, t, lt):
        if t < t_build + 0.3:
            for i in range(3):
                if (t * 8 + i) % 2 < 1:
                    star(P, 700 + i * 60, 1560 - 20 * i, 26, fill=(255, 240, 160), n=6, rot=t * 5)
        else:
            sparkles(P, 760, 1050, t, 260, n=7, seed=4)

    shot("build", "kitchen", Ls(3), Ls(4), [(0, 750, 1350, 2100, 0), (1.0, 760, 1300, 1550, 0)],
         draw_mid=build_mid, draw_front=build_front)
    # 5. Гордий: флоту це потрібно
    shot("proud", "kitchen", Ls(4), Ls(5), [(0, 820, 1150, 1700, 4)],
         draw_mid=lambda P, t, lt: kitchen_baldwin(P, t, expr="proud", headphones=True, arms=("hip", "point")),
         draw_front=lambda P, t, lt: thought(P, 1080, 560, t), kicks=[Wt("Navy", LINES[4]["s"])])
    # 6. Лист: фіолетове чорнило, рожевий і блакитний папір
    t_ink, t_paper = Ls(6), Ls(7)

    def letter(P, t, lt):
        prog = min(1.0, lt / 2.6)
        n = 9
        for i in range(n):
            frac = min(1.0, max(0.0, prog * n - i))
            if frac <= 0:
                break
            y = 930 + i * 80
            x0 = 620 + i * -6
            P.line([(x0 + 40 * j * frac, y + 10 * math.sin(j * 1.7)) for j in range(int(12 * frac) + 1)] or [(x0, y)],
                   w=9, fill=(120, 50, 170))
        px, py = 620 + 470 * ((prog * n) % 1.0), 930 + 80 * min(n - 1, int(prog * n))
        P.line([(px, py), (px + 160, py - 260)], w=22, fill=(30, 30, 34))
        P.line([(px + 160, py - 260), (px + 240, py - 390)], w=32, fill=(36, 23, 38))
        if t >= t_ink:
            sparkles(P, 280, 1800, t, 90, n=3, seed=9)

    shot("letter", "desk", Ls(5), Ls(8),
         [(0, 830, 1250, 1400, 0), (t_ink - Ls(5), 830, 1250, 1400, 0), (t_ink - Ls(5) + 0.7, 520, 1500, 1350, 0),
          (t_paper - Ls(5), 520, 1500, 1350, 0), (t_paper - Ls(5) + 0.7, 680, 1200, 1900, 0)],
         draw_front=letter, dof=0)
    # 7. Флот ледь не викидає лист
    def navy7(P, t, lt):
        laugh = t >= Ls(9)
        actor(P, T.OFFICER, 1050, 2080, 1200, t, seed=5, expr="squint" if not laugh else "laugh", arms=("down", "throw"))
        P.rect(1180, 1140, 1300, 1290, (250, 170, 200), w=5)
        if laugh:
            actor(P, T.OFFICER2, 420, 2080, 1150, t, seed=6, expr="laugh", arms=("hip", "point"), bob=1)

    shot("navy", "navy", Ls(8), Ls(10), [(0, 900, 1400, 1800, 0), (Ls(9) - Ls(8), 900, 1400, 1800, 0),
                                         (Ls(9) - Ls(8) + 0.6, 760, 1350, 1900, -4)],
         draw_mid=navy7, kicks=[Ls(9) + 0.05])
    # 8. Тест: кухонні навушники кращі за флотські
    t_beat = Wt("beats", LINES[11]["s"])

    def radio8(P, t, lt):
        wow = t >= t_beat
        actor(P, T.OFFICER2, 640, 2080, 1200, t, seed=7, headphones=True, expr="shock" if wow else "squint",
              arms=("up", "up") if wow else ("down", "ear"))

    def radio8f(P, t, lt):
        for i in range(4):
            x = 300 + i * 90
            P.line([(x, 900 + 30 * math.sin(t * 20 + i)), (x + 45, 860), (x + 90, 900 + 30 * math.sin(t * 20 + i + 1))],
                   w=7, fill=(120, 255, 200))
        if t >= t_beat:
            s = min(1.0, (t - t_beat) * 6)
            burst(P, 1030, 900, 190 * s)

    shot("test", "radio", Ls(10), Ls(12), [(0, 700, 1350, 1700, 0), (t_beat - Ls(10), 700, 1300, 1450, 0)],
         draw_mid=radio8, draw_front=radio8f, kicks=[t_beat], dof=6)
    # 9. Замовлення: сувій розгортається до підлоги
    def scroll9(P, t, lt):
        actor(P, T.OFFICER, 700, 1700, 1050, t, seed=8, expr="grin", arms=("hold", "hold"))
        L = 300 + 400 * ss(lt / 1.2) + (500 * ss((t - Ls(13)) / 0.8) if t >= Ls(13) else 0)
        P.rect(560, 1180, 840, 1180 + L, (248, 240, 214), w=5)
        for y in range(1230, int(1180 + L) - 20, 60):
            P.line([(590, y), (810, y)], w=4, fill=(170, 160, 150))
        P.ell(700, 1180 + L, 150, 26, (232, 222, 196), w=5)

    shot("order", "navy", Ls(12), Ls(14), [(0, 760, 1250, 1500, 0), (Ls(13) - Ls(12), 760, 1350, 1500, 0),
                                           (Ls(13) - Ls(12) + 0.7, 740, 2050, 1700, 0)],
         draw_front=scroll9, kicks=[Ls(13) + 0.1])
    # 10. Скільки зробить одна людина? Десять за раз
    t_ten = Ls(15) + 0.05

    def ten_front(P, t, lt):
        n = 0 if t < t_ten else min(10, int((t - t_ten) * 16) + 1)
        for i in range(n):
            headset(P, 250 + i * 110, 1520, 0.9)

    shot("ten", "kitchen", Ls(14), Ls(16), [(0, 760, 1350, 1700, 0), (t_ten - Ls(14), 760, 1450, 1500, 0)],
         draw_mid=lambda P, t, lt: kitchen_baldwin(P, t, expr="worry", sweat=True, arms=("out", "out")),
         draw_front=ten_front, kicks=[t_ten])
    # 11. Немає фабрики, лише стіл і купа дроту (вечірнє синє світло пояснення)
    t_wire = Ls(17)

    def nothing_front(P, t, lt):
        if t >= t_wire:
            sets.wire_pile(_WirePen(P), 760, 1600)
            sparkles(P, 760, 1550, t, 120, n=3, seed=11)

    shot("nothing", "kitchen_eve", Ls(16), Ls(18), [(0, 750, 1450, 2300, 0), (t_wire - Ls(16), 760, 1450, 1700, 0)],
         draw_mid=lambda P, t, lt: kitchen_baldwin(P, t, expr="sad", arms=("out", "out")), xfade=True)
    SHOTS[-1]["front"] = nothing_front
    # 12. Як готувати весілля з однією сковорідкою
    def wed_front(P, t, lt):
        actor(P, T.CHEF, 750, 2450, 1250, t, seed=9, expr="worry", sweat=True, arms=("out", "hold"))
        P.ell(820, 1940, 50, 22, (40, 40, 48), w=5)
        P.line([(870, 1940), (960, 1930)], w=12, fill=(40, 40, 48))

    shot("wedding", "wedding", Ls(18), Ls(19), [(0, 750, 1350, 2000, 0), (1.6, 750, 1450, 1800, 0)],
         draw_front=wed_front, dof=8, xfade=True)
    # 13. Фабрика ззовні
    shot("fext", "fext", Ls(19), Ls(20), [(0, 750, 1300, 2300, 0), (1.5, 750, 1600, 1900, 0)], xfade=True)
    # 14. Цех: 150 людей, 150 навушників на день, цілодобово
    def fint_mid(P, t, lt):
        for i in range(8):
            actor(P, T.WORKERS[i % 4], 200 + i * 300, 1620, 700, t, seed=20 + i, arms=("write", "write"),
                  expr="smile", bob=1)

    def fint_front(P, t, lt):
        for i in range(30):
            x = (i * 110 + t * 260) % 2700 - 50
            headset(P, x, 1555, 0.7)
        sets.clock(_WirePen(P), 1300, 820, 160, t * 1.0, speed=14)

    shot("fint", "fint", Ls(20), Ls(21), [(0, 700, 1250, 1500, 0), (Ls(21) - Ls(20), 1900, 1250, 1500, 0)],
         draw_mid=fint_mid, draw_front=fint_front, creep=0.0006)
    # 15. Багатіє
    shot("rich", "gold", Ls(21), Ls(22), [(0, 700, 1300, 1700, 0)],
         draw_mid=lambda P, t, lt: actor(P, T.BALDWIN_RICH, 700, 2050, 1250, t, seed=3, expr="proud", arms=("hip", "out")),
         draw_front=lambda P, t, lt: coins(P, t, 150, 1250, 200, 2000), kicks=[Ls(21)])
    # 16. Погані інвестиції → суд
    t_court = Wt("jury", LINES[22]["s"]) - 0.07
    t_conv = Wt("convicts", LINES[22]["s"])

    def chart_mid(P, t, lt):
        pts = [(230 + i * 95, 420 + 60 * math.sin(i) + i * 55) for i in range(11)]
        k = min(len(pts), 2 + int(lt * 4))
        P.line(pts[:k], w=14, fill=(210, 50, 50))
        actor(P, T.BALDWIN_RICH, 760, 2100, 1150, t, seed=3, expr="worry", sweat=True, arms=("out", "ear"))
        for i in range(3):
            ph = (lt * 0.6 + i / 3) % 1.0
            winged_money(P, 1050 + i * 120 + 150 * ph, 1700 - 1500 * ph, t + i)

    shot("invest", "chart", Ls(22), t_court, [(0, 700, 1300, 1900, 0), (1.5, 700, 1250, 1700, 0)],
         draw_mid=chart_mid)

    def court_mid(P, t, lt, phones=False, verdict=None):
        slam = verdict if verdict is not None else t_conv
        up = t < slam - 0.15
        ang = 70 if up else (70 - 80 * ss((t - (slam - 0.15)) / 0.15) if t < slam else -10)
        actor(P, T.JUDGE, 800, 1400, 900, t, seed=12, expr="neutral" if up else "shock", arms=("down", "throw"))
        gavel(P, 993, 1400 - 665 * 0.9, ang)
        P.rect(430, 1060, 1170, 1450, (100, 56, 30))           # суддівський стіл перед суддею
        P.rect(430, 1000, 1170, 1060, (130, 80, 48))

    def court_front(P, t, lt, phones=False):
        actor(P, T.BALDWIN, 1300, 2450, 1100, t, seed=13, expr="sad" if not phones else "shock",
              headphones=phones, arms=("down", "down"))

    shot("court", "court", t_court, Ls(23), [(0, 900, 1400, 1900, 0), (t_conv - t_court, 900, 1300, 1700, 0)],
         draw_mid=court_mid, draw_front=court_front, kicks=[t_conv])
    # 17. Розв'язка: щоб чути проповідь…
    def church17f(P, t, lt):
        actor(P, T.BALDWIN, 930, 2700, 1350, t, seed=2, expr="grin", headphones=True, arms=("hold", "hold"))
        waves(P, 1210, 1430, t, 1), waves(P, 650, 1430, t, -1)

    shot("sermon", "church", Ls(23), Ls(24), [(0, 860, 1650, 1450, 0)],
         draw_mid=church3, draw_front=church17f, dof=10)
    # 18. …а почув вирок
    t_ver = Wt("verdict", LINES[24]["s"])
    shot("verdict", "court", Ls(24), DUR, [(0, 1100, 1600, 1500, 0), (t_ver - Ls(24) - 0.2, 1150, 1650, 1250, 3)],
         draw_mid=lambda P, t, lt: court_mid(P, t, lt, verdict=t_ver),
         draw_front=lambda P, t, lt: court_front(P, t, lt, phones=True), kicks=[t_ver])


class _WirePen:
    """Адаптер для функцій sets.* (вони малюють через ImageDraw у світових координатах)."""

    def __init__(self, P):
        self.P = P

    def line(self, xy, fill=INK, width=6, joint=None):
        pts = [(x / S, y / S) for x, y in xy]
        self.P.line(pts, w=width, fill=fill)

    def ellipse(self, box, fill=None, outline=None, width=0):
        x0, y0, x1, y1 = [v / S for v in box]
        self.P.ell((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, fill, ink=outline is not None, w=width)


# sets.wire_pile/clock викликають line()/ell() з модуля sets, що беруть ImageDraw: підмінимо їх для _WirePen
_orig_line, _orig_ell = sets.line, sets.ell


def _line(d, pts, w=6, fill=INK):
    if isinstance(d, _WirePen):
        d.P.line(pts, w=w, fill=fill)
    else:
        _orig_line(d, pts, w, fill)


def _ell(d, box, fill, ink=True, w=6):
    if isinstance(d, _WirePen):
        x0, y0, x1, y1 = box
        d.P.ell((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, fill, ink=ink, w=w)
    else:
        _orig_ell(d, box, fill, ink, w)


sets.line, sets.ell = _line, _ell


# ---------- камера й кадр ----------
@lru_cache(maxsize=16)
def load_set(name, dof):
    bg, fg = sets.SETS[name]()
    if dof:
        bg = bg.filter(ImageFilter.GaussianBlur(dof * S))
    return bg, fg


def cam_at(sh, lt):
    keys = sh["cams"]
    if lt <= keys[0][0]:
        k = keys[0]
    elif lt >= keys[-1][0]:
        k = keys[-1]
    else:
        for k0, k1 in zip(keys, keys[1:]):
            if k0[0] <= lt <= k1[0]:
                dur = k1[0] - k0[0]
                g = ss((lt - k0[0]) / dur) if dur > 0 else 1
                k = tuple(a + (b - a) * g for a, b in zip(k0, k1))
                break
    _, cx, cy, vh, roll = k
    vh *= (1 - sh["creep"]) ** (lt * FPS)          # повільний наїзд
    sx = sy = 0.0
    for kt in sh["kicks"]:
        f = (sh["a"] + lt - kt) * FPS
        if 0 <= f < 7:
            amp = 18 * (1 - f / 7)
            sgn = 1 if int(f) % 2 == 0 else -1
            sx, sy = sgn * amp, -sgn * amp * 0.6
    return cx + sx, cy + sy, vh, roll


def render_shot(sh, t):
    lt = t - sh["a"]
    bg, fg = load_set(sh["set"], sh["dof"])
    cx, cy, vh, roll = cam_at(sh, lt)
    vw = vh * OW / OH
    pad = 1.12 if roll else 1.0
    sw, shh = bg.width / S, bg.height / S                 # камера не виходить за межі локації
    vh = min(vh, shh / pad, sw / pad * OH / OW)
    vw = vh * OW / OH
    cx = min(max(cx, vw * pad / 2), sw - vw * pad / 2)
    cy = min(max(cy, vh * pad / 2), shh - vh * pad / 2)
    bw, bh = vw * pad, vh * pad
    ox, oy = int((cx - bw / 2) * S), int((cy - bh / 2) * S)
    box = (ox, oy, ox + int(bw * S), oy + int(bh * S))
    frame = bg.crop(box).convert("RGBA")
    P = Pen(frame, ox, oy)
    if sh["mid"]:
        sh["mid"](P, t, lt)
    if fg is not None:
        frame.alpha_composite(fg.crop(box))
    if sh["front"]:
        sh["front"](P, t, lt)
    if roll:
        frame = frame.rotate(roll, resample=Image.BICUBIC, center=(frame.width / 2, frame.height / 2))
        mx, my = (frame.width - vw * S) / 2, (frame.height - vh * S) / 2
        frame = frame.crop((int(mx), int(my), int(mx + vw * S), int(my + vh * S)))
    return frame.convert("RGB").resize((OW, OH), Image.LANCZOS)


_YY, _XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
_VIG = np.clip(1.05 - 0.20 * (((_XX - OW / 2) / (OW / 2)) ** 2 + ((_YY - OH / 2) / (OH / 2)) ** 2) ** 1.4, 0.68, 1)


def grade(img):
    """Кольорокорекція під зразок: S-крива контрасту, теплі світла / сині тіні, легке світіння, віньєтка."""
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    s_curve = lum + 0.22 * (lum - lum ** 2) * (lum - 0.5) * 4          # контраст у середніх тонах
    a = a * (s_curve / np.maximum(lum, 1e-4))[..., None]
    sh = np.clip(1 - lum * 2, 0, 1)[..., None]
    hi = np.clip(lum * 2 - 1, 0, 1)[..., None]
    a += sh * np.array([-0.02, -0.005, 0.05]) + hi * np.array([0.04, 0.02, -0.03])
    gray = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    a = gray + (a - gray) * 1.15                                        # насиченість
    small = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((OW // 8, OH // 8), Image.BILINEAR)
    b = np.asarray(small.filter(ImageFilter.GaussianBlur(6)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
    a += np.clip(b - 0.72, 0, 1) * 0.6                                  # світіння яскравих місць
    a *= _VIG[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def frame_at(t):
    idx = max(i for i, s in enumerate(SHOTS) if s["a"] <= t + 1e-6)
    sh = SHOTS[idx]
    img = render_shot(sh, t)
    if sh["xfade"] and idx > 0 and t - sh["a"] < 7 / FPS:
        k = (t - sh["a"]) / (7 / FPS)
        img = Image.blend(render_shot(SHOTS[idx - 1], t), img, ss(k))
    tf = (t - SHOTS[1]["a"]) * FPS                    # білий спалах після хука
    if 0 <= tf < 4:
        img = Image.blend(img, Image.new("RGB", img.size, (255, 255, 255)), 1 - tf / 4)
    return grade(img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--stills", default="")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    build_shots()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.stills:
        for s in a.stills.split(","):
            frame_at(float(s)).save(out.parent / f"still_{float(s):05.2f}.png")
        return
    n = int(DUR * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                             f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "18", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame_at(i / FPS).tobytes())
        if i % 150 == 0:
            print(f"  {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    json.dump([{"name": s["name"], "a": s["a"], "b": s["b"]} for s in SHOTS], open(out.parent / "shots.json", "w"), indent=1)
    print("Готово:", out, f"{DUR:.2f} с")


if __name__ == "__main__":
    main()
