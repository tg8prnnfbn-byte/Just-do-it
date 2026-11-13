#!/usr/bin/env python3
"""Освітній мультик «Snoring, then silence» про апное сну (рушій навушників, 1080x1920, 30 fps).

    python3 apnoe/film_a.py apnoe/out/video_silent.mp4 [--stills 1,5]
"""
from __future__ import annotations

import math
import os
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("VOICE_DIR", str(HERE / "voice"))
sys.path.insert(0, str(HERE.parent / "navushnyky"))
sys.path.insert(0, str(HERE.parent / "ekstrene" / "multyk2"))
sys.path.insert(0, str(HERE))

from PIL import Image, ImageFont  # noqa: E402

import film as F  # noqa: E402
import asets  # noqa: E402
import toon as T  # noqa: E402
from film_h import phone as phone_h  # noqa: E402
import sleeper as SL  # noqa: E402

Ls, Wt, ss, shot, actor, burst, star, sparkles = F.Ls, F.Wt, F.ss, F.shot, F.actor, F.burst, F.star, F.sparkles
S = F.S
INK = F.INK
DIGI = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"

HER = dict(skin=(240, 204, 172), hair=(120, 60, 40), hair_style="bun", shirt=(200, 110, 130), pants=(60, 50, 80))
HIM = dict(skin=(226, 186, 150), hair=(60, 44, 34), hair_style="short", shirt=(110, 140, 190), pants=(50, 54, 80), mustache=True)
DOC = dict(skin=(214, 168, 128), hair=(30, 26, 24), hair_style="short", shirt=(246, 246, 250), pants=(60, 70, 100))


def font(path, size):
    return ImageFont.truetype(path, max(8, int(size * S)))


# ---------- персонажі в ліжку ----------
@lru_cache(maxsize=64)
def head_sprite(k, angle, expr, blink, mask=False):
    spr = T.person(k, **dict(HIM, expr=expr, blink=blink))
    head = spr.crop((0, int(120 * k), spr.width, int(450 * k)))
    if mask:                                                               # маска CPAP на носі й роті
        from PIL import ImageDraw
        d = ImageDraw.Draw(head)
        cx, cy = head.width / 2, (290 + 50 - 120) * k
        d.rounded_rectangle((cx - 60 * k, cy - 45 * k, cx + 60 * k, cy + 45 * k), radius=int(30 * k),
                            fill=(220, 236, 246), outline=T.PLUM, width=max(1, int(5 * k)))
        d.line((cx + 60 * k, cy, cx + 200 * k, cy + 60 * k), fill=(150, 170, 200), width=max(1, int(14 * k)))
    return head.rotate(angle, resample=Image.BICUBIC, expand=True)


def sleeper(P, t, expr="neutral", blink=True, snore=0.0, mask=False):
    """Чоловік лежить на боці (sleeper.man); expr лишено для сумісності — обличчя завжди спокійне уві сні."""
    SL.man(P, t, HIM, snoring=snore, mask=mask)


def her(P, t, expr="neutral", arms=("down", "down"), x=1030, y=2170, h=1150, **o):
    actor(P, HER, x, y, h, t, seed=5, expr=expr, arms=arms, **o)


def zz(P, x, y, t, loud=1.0, n=3):
    """Хмарка «Z» від хропіння."""
    for i in range(n):
        ph = (t * 0.9 + i / n) % 1.0
        size = (40 + 70 * ph) * loud
        f = font(INTER_B, size)
        px, py = P.p(x + 140 * ph + i * 20, y - 260 * ph)
        a = int(255 * (1 - ph))
        P.d.text((px, py), "Z", font=f, fill=(250, 250, 255, a), stroke_width=int(3 * S), stroke_fill=(30, 30, 60, a))


def saw(P, x, y, t):
    """Зубчасті лінії «бензопила»."""
    for j in range(3):
        pts = [(x + i * 22, y - j * 40 + (14 if (i + int(t * 20)) % 2 else -14)) for i in range(10)]
        P.line(pts, w=6, fill=(255, 230, 120))


def clock(P, cx, cy, w, text):
    h = w * 0.55
    P.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (30, 30, 36), r=w * 0.1, w=5)
    P.rect(cx - w * 0.42, cy - h * 0.34, cx + w * 0.42, cy + h * 0.34, (12, 14, 16), ink=False, r=w * 0.04)
    f = font(DIGI, w * (0.2 if len(text) <= 5 else 0.13))
    x, y = P.p(cx, cy)
    tw = P.d.textlength(text, font=f)
    P.d.text((x - tw / 2, y - w * 0.13 * S), text, font=f, fill=(255, 80, 60))
    P.glow(cx, cy, w * 0.5, h * 0.4, (255, 80, 60), 50, w * 0.06)


def pause_icon(P, cx, cy, r, t):
    P.glow(cx, cy, r * 1.3, r * 1.3, (255, 255, 255), 60, r * 0.4)
    P.ell(cx, cy, r, r, (250, 250, 255), w=5)
    for sx in (-1, 1):
        P.rect(cx + sx * r * 0.28 - r * 0.12, cy - r * 0.42, cx + sx * r * 0.28 + r * 0.12, cy + r * 0.42, (40, 44, 80), ink=False, r=r * 0.05)


def mini_phone(P, cx, cy, h, t, mode):
    """Телефон для цього ролика: 'rec' — запис відео, 'sos' — екстрений виклик."""
    w = h * 0.49
    P.glow(cx, cy, w * 0.9, h * 0.6, (140, 160, 240) if mode == "rec" else (255, 90, 90), 90, h * 0.08)
    P.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (16, 16, 20), r=w * 0.12, w=4)
    scr = (24, 30, 50) if mode == "rec" else (150, 30, 36)
    P.rect(cx - w / 2 + 10, cy - h / 2 + 10, cx + w / 2 - 10, cy + h / 2 - 10, scr, ink=False, r=w * 0.1)

    def text(y, s_, size, fill=(240, 240, 246)):
        f = font(INTER_B, size * h / 900)
        x, yy = P.p(cx, cy - h / 2 + y * h / 900)
        P.d.text((x - P.d.textlength(s_, font=f) / 2, yy), s_, font=f, fill=fill)

    if mode == "rec":
        if (t * 2) % 1 < 0.6:
            P.ell(cx - w * 0.22, cy - h * 0.36, w * 0.06, w * 0.06, (240, 40, 40), ink=False)
        text(70, "REC  0:%02d" % (int(t * 2) % 60), 60)
        P.ell(cx, cy, w * 0.22, w * 0.22, (90, 100, 140), ink=False)                       # силует у видошукачі
        P.rect(cx - w * 0.32, cy + w * 0.2, cx + w * 0.32, cy + h * 0.32, (90, 100, 140), ink=False, r=w * 0.1)
    else:
        text(250, "Emergency", 90)
        text(380, "Calling...", 60, fill=(255, 210, 210))
        P.ell(cx, cy + h * 0.3, w * 0.16, w * 0.16, (230, 50, 50), ink=False)


# ---------- пояснювальні схеми ----------
def throat(P, t, close=0.0):
    """Профіль голови з дихальною трубкою; close 0..1 — язик і м'які тканини перекривають шлях."""
    skin = (240, 204, 172)
    P.ell(700, 900, 330, 360, skin, w=5)                                                  # голова
    P.poly([(400, 900), (330, 1010), (420, 1040)], skin, w=5)                            # ніс
    P.rect(560, 1150, 860, 1900, skin, w=5)                                               # шия
    P.ell(700, 900, 330, 360, skin, ink=False)
    P.rect(565, 1100, 855, 1300, skin, ink=False)
    P.poly([(420, 720), (560, 560), (800, 540), (990, 650), (1010, 820), (900, 700), (600, 660)], (96, 64, 40), ink=False)   # волосся
    air = (250, 170, 180)
    P.line([(420, 1010), (520, 1030), (640, 1080), (690, 1250), (700, 1900)], w=int(70 * S), fill=air)
    P.line([(420, 1010), (520, 1030), (640, 1080), (690, 1250), (700, 1900)], w=int(52 * S), fill=(255, 220, 226))
    # язик зсувається назад і закриває трубку
    tx = 560 + 110 * close
    P.ell(tx, 1120, 110, 70, (220, 100, 110), w=4)
    # стрілка потоку повітря (лише коли відкрито)
    if close < 0.6:
        ph = (t * 1.5) % 1.0
        y = 1300 + 500 * ph
        P.poly([(700, y), (670, y - 50), (730, y - 50)], (80, 160, 230), w=3)


def straw(P, t, pinch=0.0):
    P.rect(450, 1250, 950, 1950, (210, 230, 245), w=5)                                    # склянка
    P.rect(465, 1500, 935, 1935, (240, 160, 70), ink=False)                              # сік
    w0 = 42
    mid = w0 * (1 - 0.85 * pinch)
    P.poly([(700 - w0, 800), (700 + w0, 800), (700 + mid, 1150), (700 + w0, 1500), (700 + w0, 1800),
            (700 - w0, 1800), (700 - w0, 1500), (700 - mid, 1150)], (250, 250, 250), w=5)
    for y in range(840, 1780, 70):                                                       # смужки соломинки
        P.line([(700 - w0, y), (700 + w0, y + 30)], w=8, fill=(230, 80, 90))


def brain(P, cx, cy, r, t, alarm=False):
    P.ell(cx, cy, r, r * 0.8, (246, 170, 190), w=5)
    for i in range(5):
        P.arc(cx - r * 0.5 + i * r * 0.25, cy - r * 0.2, r * 0.3, 200, 340, w=5)
        P.arc(cx - r * 0.4 + i * r * 0.22, cy + r * 0.25, r * 0.25, 20, 160, w=5)
    if alarm:
        sh = 12 * math.sin(t * 60)
        bx, by = cx + r * 0.9 + sh, cy - r * 0.9
        P.ell(bx, by, r * 0.35, r * 0.35, (240, 200, 60), w=5)
        P.ell(bx, by, r * 0.22, r * 0.22, (255, 250, 230), w=3)
        for sx in (-1, 1):
            P.ell(bx + sx * r * 0.3, by - r * 0.32, r * 0.1, r * 0.1, (240, 200, 60), w=4)
        for i in range(3):
            P.arc(bx, by, r * (0.5 + 0.15 * i), 300, 360, w=6, fill=(255, 240, 120))


def o2_meter(P, x, y, h, level):
    P.rect(x - 60, y - h, x + 60, y, (240, 244, 250), w=5, r=30)
    c = (80, 200, 120) if level > 0.6 else (240, 180, 60) if level > 0.35 else (230, 70, 60)
    P.rect(x - 44, y - 16 - (h - 32) * level, x + 44, y - 16, c, ink=False, r=20)
    f = font(INTER_B, 70)
    px, py = P.p(x - 50, y - h - 110)
    P.d.text((px, py), "O₂", font=f, fill=(250, 250, 255), stroke_width=int(3 * S), stroke_fill=(30, 30, 60))


def risk_icons(P, t, shown):
    icons = []
    # тиск
    def gauge(cx, cy):
        P.ell(cx, cy, 120, 120, (250, 250, 250), w=6)
        P.arc(cx, cy, 90, 200, 340, w=10, fill=(230, 70, 60))
        a = math.radians(200 + 130)
        P.line([(cx, cy), (cx + 80 * math.cos(a), cy + 80 * math.sin(a))], w=10)
    def heart(cx, cy):
        P.ell(cx - 55, cy - 30, 65, 65, (230, 70, 80), ink=False)
        P.ell(cx + 55, cy - 30, 65, 65, (230, 70, 80), ink=False)
        P.poly([(cx - 118, cy - 10), (cx + 118, cy - 10), (cx, cy + 130)], (230, 70, 80), ink=False)
        P.line([(cx - 90, cy), (cx - 30, cy), (cx - 10, cy - 50), (cx + 20, cy + 40), (cx + 40, cy), (cx + 90, cy)], w=8, fill=(255, 255, 255))
    for i, (fn, (cx, cy)) in enumerate(((gauge, (700, 700)), (heart, (420, 1300)), (None, (980, 1300)))):
        if i >= shown:
            break
        pop = 1.0
        if fn is None:
            brain(P, cx, cy, 120, t)
        else:
            fn(cx, cy)
        sparkles(P, cx, cy, t, 130, n=2, seed=i)


def doctor_scene(P, t, lt):
    actor(P, DOC, 400, 1800, 1100, t, seed=8, expr="smile", arms=("hip", "point"))
    her(P, t, "smile", ("hold", "hold"), x=1100, y=1820, h=1050)


def compressions(P, t):
    """Схема: людина лежить, руки посередині грудей, ритм ~110/хв."""
    P.rect(40, 1300, 880, 1700, (110, 140, 190), r=200, w=5)                                 # тулуб
    P.ell(960, 1500, 140, 130, (226, 186, 150), w=5)                                         # голова
    for sx in (-1, 1):
        P.ell(960 + sx * 45, 1470, 10, 14, INK, ink=False)
    push = 30 * max(0.0, math.sin(t * 2 * math.pi * 1.85))
    cx, cy = 480, 1300 + push
    for dy in (0, -60):                                                                     # дві долоні одна на одній
        P.rect(cx - 120, cy - 70 + dy, cx + 120, cy + dy, (240, 204, 172), r=30, w=5)
    for sx in (-1, 1):
        P.line([(cx + sx * 90, cy - 120), (cx + sx * 180, cy - 520)], w=int(30 * S), fill=(240, 204, 172))
    for i in range(3):                                                                      # стрілки вниз
        ph = (t * 1.85 + i / 3) % 1.0
        P.poly([(cx + 260, 1050 + 120 * ph), (cx + 220, 990 + 120 * ph), (cx + 300, 990 + 120 * ph)], (255, 240, 120, int(255 * (1 - ph))), w=3)


# ---------- план кадрів ----------
def build():
    F.SHOTS.clear()
    L = F.LINES
    t_sil = Ls(3)
    t_snort = Ls(7)

    def bed_mid(P, t, lt, snoring=True, her_expr="squint", mask=False):
        her(P, t, her_expr, ("down", "down"))
        sleeper(P, t, "laugh" if snoring and not mask else "neutral", blink=True, snore=1.0 if snoring else 0.0, mask=mask)

    def bed_front(P, t, lt, loud=1.0, sawing=False):
        if loud > 0:
            zz(P, 620, 1220, t, loud)
        if sawing:
            saw(P, 300, 1250, t)

    t_rev = Ls(6) + 0.55                                       # кінець від'їзду: обоє в кадрі

    def wife(t):
        """Реакція дружини: спить → розплющує очі → тривога → страх → після фирку — роздратування."""
        if t < t_sil + 0.9:
            return dict(expr="neutral", blink=True)
        if t < Ls(5):
            return dict(expr="neutral", blink=SL.breath(t, 0.6) > 0.97)
        if t < Ls(6):
            return dict(expr="worry")
        if t < t_snort:
            return dict(expr="shock")
        if t < t_snort + 0.8:
            return dict(expr="shock")
        return dict(expr="squint")

    def bed_mid2(P, t, lt, snoring=1.0, mask=False, w=None):
        her(P, t, arms=("down", "down"), **(w or wife(t)))
        sleeper(P, t, snore=snoring, mask=mask)

    def bed_front2(P, t, lt, snoring=1.0, loud=0.0, sawing=False):
        SL.blanket_over(P, t, snoring)
        if loud > 0:
            zz(P, 640, 1250, t, loud)
        if sawing:
            saw(P, 650, 1430, t)

    ECU = (480, 1400, 560)
    shot("hook", "bedroom2", 0.0, Ls(1), [(0, *ECU, 0), (Ls(1), 480, 1400, 510, 0)],
         draw_mid=lambda P, t, lt: bed_mid2(P, t, lt, w=dict(expr="neutral", blink=True)),
         draw_front=lambda P, t, lt: bed_front2(P, t, lt), creep=0.0, dof=3)
    shot("clock", "phone", Ls(1), Ls(2), [(0, 650, 1150, 1300, 0)],
         draw_front=lambda P, t, lt: clock(P, 650, 1150, 900, "2:00"))
    shot("chainsaw", "bedroom2", Ls(2), t_sil, [(0, 500, 1405, 660, 0), (t_sil - Ls(2), 500, 1405, 600, 0)],
         draw_mid=lambda P, t, lt: bed_mid2(P, t, lt, w=dict(expr="neutral", blink=True)),
         draw_front=lambda P, t, lt: bed_front2(P, t, lt, loud=0.9, sawing=True),
         kicks=[Wt("chainsaw", L[2]["s"])], creep=0.0, dof=3)
    shot("silence", "bedroom2", t_sil, t_snort,
         [(0, 500, 1405, 600, 0), (0.9, 500, 1405, 600, 0), (t_rev - t_sil, 740, 1430, 1680, 0)],
         draw_mid=lambda P, t, lt: bed_mid2(P, t, lt, snoring=0.0),
         draw_front=lambda P, t, lt: bed_front2(P, t, lt, snoring=0.0), creep=0.0, dof=0)
    shot("snort", "bedroom2", t_snort, Ls(8), [(0, 740, 1430, 1680, 0)],
         draw_mid=lambda P, t, lt: bed_mid2(P, t, lt, snoring=1.0),
         draw_front=lambda P, t, lt: (bed_front2(P, t, lt, loud=1.0),
                                      burst(P, 640, 1250, 120 * min(1, lt * 5)) if lt < 0.7 else None),
         kicks=[t_snort + 0.05], creep=0.0006)
    shot("rollover", "bedroom2", Ls(8), Ls(9), [(0, 740, 1430, 1680, 0), (Ls(9) - Ls(8), 740, 1450, 1500, 0)],
         draw_mid=lambda P, t, lt: (her(P, t, "squint", ("down", "down"), blink=t > Ls(8) + 0.9), sleeper(P, t, snore=1.0)),
         draw_front=lambda P, t, lt: bed_front2(P, t, lt, loud=0.8), creep=0.0003)

    def apnea_front(P, t, lt):
        if t >= Wt("apnea", L[9]["s"]) - 0.05:
            pause_icon(P, 430, 1180, 110 * min(1, (t - Wt("apnea", L[9]["s"]) + 0.05) * 6), t)

    shot("name", "bedroom2", Ls(9), Ls(10), [(0, 520, 1390, 700, 0)],
         draw_mid=lambda P, t, lt: bed_mid2(P, t, lt, snoring=0.0, w=dict(expr="neutral", blink=True)),
         draw_front=lambda P, t, lt: (SL.blanket_over(P, t), apnea_front(P, t, lt)),
         kicks=[Wt("apnea", L[9]["s"])])
    # пояснення: горло
    t_shut = Wt("folds", L[11]["s"])
    t_straw = Wt("straw", L[11]["s"])
    t_relax = Wt("relax", L[10]["s"])

    def anat(P, t, lt):
        relax = ss((t - (t_relax - 0.4)) / 0.8)
        close = ss((t - t_shut) / 0.7) if t > t_shut else 0.0
        SL.anatomy(P, t, relax=relax, close=close)

    shot("throat", "panel", Ls(10), t_straw - 0.07,
         [(0, 670, 1200, 2000, 0), (t_relax - Ls(10), 700, 1150, 1500, 0), (t_shut - Ls(10) + 0.6, 790, 1100, 1100, 0)],
         draw_front=anat, xfade=True, creep=0.0)
    shot("straw", "panel", t_straw - 0.07, Ls(12), [(0, 700, 1300, 1500, 0)],
         draw_front=lambda P, t, lt: straw(P, t, ss((lt - 0.4) / 0.8)), kicks=[t_straw + 0.5])
    t_jolt = Wt("jolts", L[12]["s"])

    def oxy(P, t, lt):
        lvl = max(0.15, 0.95 - 0.8 * ss(lt / 1.4))
        if t > t_jolt + 0.5:
            lvl = 0.15 + 0.8 * ss((t - t_jolt - 0.5) / 0.6)
        o2_meter(P, 500, 1700, 700, lvl)
        brain(P, 840, 1100, 210, t, alarm=t >= t_jolt)
        if t >= t_jolt:
            burst(P, 840, 720, 150 * min(1, (t - t_jolt) * 5))

    shot("oxygen", "panel", Ls(12), Ls(13), [(0, 700, 1200, 1700, 0), (t_jolt - Ls(12), 760, 1150, 1500, 0)],
         draw_front=oxy, kicks=[t_jolt])

    def hundreds(P, t, lt):
        n = min(60, int(lt * 22) + 1)
        for i in range(n):
            x, y = 230 + (i % 6) * 190, 560 + (i // 6) * 150
            pause_icon(P, x, y, 50, t)
        P.ell(1150, 330, 90, 90, (240, 240, 255), ink=False)

    shot("hundreds", "panel", Ls(13), Ls(14), [(0, 700, 1250, 1900, 0), (2.5, 700, 1150, 2000, 0)], draw_front=hundreds)

    def risks(P, t, lt):
        shown = 1 + (t >= Wt("heart", L[14]["s"])) + (t >= Wt("stroke", L[14]["s"]))
        risk_icons(P, t, shown)

    shot("risks", "panel", Ls(14), Ls(15), [(0, 700, 1050, 1700, 0)], draw_front=risks,
         kicks=[Wt("pressure", L[14]["s"]), Wt("heart", L[14]["s"]), Wt("stroke", L[14]["s"])])
    # що робити
    shot("todo", "bedroom2", Ls(15), Ls(16), [(0, 740, 1430, 1680, 0)],
         draw_mid=lambda P, t, lt: (her(P, t, "proud", ("down", "down")), sleeper(P, t, snore=0.3)),
         draw_front=lambda P, t, lt: (SL.blanket_over(P, t, 0.3), sparkles(P, 1000, 1150, t, 160, n=4, seed=3)), xfade=True, creep=0.0003)

    def calm(P, t, lt):
        her(P, t, "smile", ("down", "down"))
        sleeper(P, t, snore=1.0)

    shot("calm", "bedroom2", Ls(16), Ls(17), [(0, 740, 1430, 1680, 0)], draw_mid=calm,
         draw_front=lambda P, t, lt: bed_front2(P, t, lt, loud=0.8), creep=0.0003)
    t_doc = Wt("doctor", L[17]["s"]) - 0.25

    def record(P, t, lt):
        her(P, t, "squint", ("hold", "hold"))
        sleeper(P, t, snore=1.0)
        mini_phone(P, 900, 1330, 240, t, "rec")

    shot("record", "bedroom2", Ls(17), t_doc, [(0, 740, 1430, 1680, 0), (1.5, 740, 1420, 1580, 0)],
         draw_mid=record, draw_front=lambda P, t, lt: bed_front2(P, t, lt, loud=0.6), creep=0.0003)
    shot("doctor", "doctor", t_doc, Ls(19), [(0, 750, 1300, 1900, 0), (Ls(18) - t_doc + 1.2, 740, 1350, 1700, 0)],
         draw_mid=doctor_scene, draw_front=lambda P, t, lt: sparkles(P, 710, 1560, t, 120, n=3, seed=5) if t > Wt("treatable", L[18]["s"]) else None,
         xfade=True)
    # екстрений випадок
    t_call = Wt("call", L[19]["s"])

    def emergency(P, t, lt):
        if t < t_call:
            her(P, t, "shock", ("out", "out"))
            sleeper(P, t, snore=0.0)
        else:
            her(P, t, "worry", ("hold", "ear"))
            sleeper(P, t, snore=0.0)
            mini_phone(P, 840, 1320, 220, t, "sos")
            P.glow(760, 900, 900, 700, (230, 60, 60), int(60 + 40 * math.sin(t * 8)), 120)

    shot("emergency", "bedroom2", Ls(19), Ls(20), [(0, 740, 1430, 1680, 0), (t_call - Ls(19), 770, 1420, 1600, 2)],
         draw_mid=emergency, draw_front=lambda P, t, lt: SL.blanket_over(P, t, 0.0), kicks=[t_call], creep=0.0003)
    shot("cpr", "panel", Ls(20), Ls(21), [(0, 560, 1250, 1900, 0)], draw_front=lambda P, t, lt: compressions(P, t),
         kicks=[Wt("Hard", L[20]["s"])], creep=0.0008)
    # фінал: лікується — тихий сон з маскою
    shot("final", "bedroom2", Ls(21), F.DUR, [(0, 740, 1430, 1680, 0), (Ls(22) - Ls(21), 760, 1460, 1700, 0)],
         draw_mid=lambda P, t, lt: (her(P, t, "smile", ("down", "down"), blink=True),
                                    sleeper(P, t, snore=0.0, mask=True)),
         draw_front=lambda P, t, lt: (SL.blanket_over(P, t), zz(P, 640, 1250, t, 0.5, n=2)), xfade=True, creep=0.0003)


F.build_shots = build

if __name__ == "__main__":
    F.main()
