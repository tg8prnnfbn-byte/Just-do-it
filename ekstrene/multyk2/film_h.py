#!/usr/bin/env python3
"""Хорор «Екстрене оповіщення», Серія 2, мультяшна версія (рушій навушників, нічні локації).

    python3 ekstrene/multyk2/film_h.py ekstrene/multyk2/out/video_silent.mp4 [--stills 1,5]
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("VOICE_DIR", str(HERE / "voice"))
sys.path.insert(0, str(HERE.parents[1] / "navushnyky"))
sys.path.insert(0, str(HERE))

from PIL import Image, ImageFont  # noqa: E402

import film as F  # noqa: E402
import hsets  # noqa: E402,F401  (реєструє нічні локації)
import toon as T  # noqa: E402

Ls, Wt, ss, shot, actor, burst, star = F.Ls, F.Wt, F.ss, F.shot, F.actor, F.burst, F.star
S = F.S
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
HAND = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"

ME = dict(skin=(238, 200, 168), hair=(46, 36, 32), hair_style="short", shirt=(84, 104, 96), pants=(40, 44, 60))


def font(path, size):
    return ImageFont.truetype(path, int(size * S))


# ---------- телефон ----------
def phone(P, cx, cy, h, t, mode="call", wave=0.0, red=0.0, log=0):
    w = h * 0.49
    shake = 6 * math.sin(t * 70) if mode == "call" and (t % 1.0) < 0.55 else 0
    cx += shake
    # світіння екрана
    P.glow(cx, cy, w * 0.9, h * 0.6, (120, 140, 230), 110, h * 0.08)
    P.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (16, 16, 20), r=w * 0.12, w=4)
    scr = (int(26 + 150 * red), 30, int(48 * (1 - red) + 16))
    P.rect(cx - w / 2 + 14, cy - h / 2 + 14, cx + w / 2 - 14, cy + h / 2 - 14, scr, ink=False, r=w * 0.1)

    def text(y, s_, size, bold=False, fill=(236, 236, 244)):
        f = font(INTER_B if bold else INTER, size * h / 900)
        x, yy = P.p(cx, cy - h / 2 + y * h / 900)
        P.d.text((x - P.d.textlength(s_, font=f) / 2, yy), s_, font=f, fill=fill)

    text(40, "3:07", 34, True)
    if mode == "call":
        text(150, "Incoming call", 28, fill=(170, 170, 185))
        P.ell(cx, cy - h / 2 + 300 * h / 900, 70 * h / 900, 70 * h / 900, (70, 70, 84), ink=False)
        text(255, "G", 70, True)
        text(390, "Grandma", 50, True)
        text(455, "Landline", 30, fill=(170, 170, 185))
        for sx, col in ((-1, (210, 50, 50)), (1, (60, 180, 90))):
            pulse = 8 if sx > 0 and (t % 1.0) < 0.5 else 0
            P.ell(cx + sx * 100 * h / 900, cy - h / 2 + 720 * h / 900, (46 + pulse) * h / 900, (46 + pulse) * h / 900, col, ink=False)
    elif mode == "vm":
        text(150, "Grandma (Landline)", 40, True)
        text(210, "Voicemail  ·  0:14", 28, fill=(170, 170, 185))
        y0 = cy - h / 2 + 440 * h / 900
        n = 34
        for i in range(n):
            x = cx - w / 2 + 40 + i * (w - 80) / n
            amp = 3 + wave * (16 + 110 * abs(math.sin(i * 0.7 + t * 9)))
            P.rect(x, y0 - amp * h / 900, x + 6 * h / 900, y0 + amp * h / 900, (236, 236, 244) if red < .5 else (255, 210, 210), ink=False)
    elif mode == "log":
        text(150, "Recent", 44, True)
        rows = [("Grandma (Landline)", "Outgoing  ·  0:14", True), ("Grandma (Landline)", "Missed  ·  3:07 AM", False),
                ("Unknown", "Missed  ·  Mon", False)]
        for i, (a, b, hot) in enumerate(rows[:max(0, log)]):
            yy = 260 + i * 140
            text(yy, a, 36, True, fill=(255, 120, 120) if hot else (236, 236, 244))
            text(yy + 52, b, 26, fill=(255, 160, 160) if hot else (160, 160, 175))


# ---------- «воно» ----------
def it_figure(P, x, y, h, t, glow=1.0):
    w = h * 0.17
    P.glow(x, y - h * 0.5, w * 1.6, h * 0.55, (200, 210, 255), int(70 * glow), h * 0.06)
    sway = 6 * math.sin(t * 1.3)
    P.rect(x - w / 2 + sway, y - h, x + w / 2 + sway, y - h * 0.08, (226, 230, 240), r=w / 2, w=4)
    for sx in (-1, 1):                                                   # довгі тонкі руки до колін
        P.line([(x + sx * w * 0.45 + sway, y - h * 0.8), (x + sx * w * 0.75, y - h * 0.5), (x + sx * w * 0.7, y - h * 0.28)],
               w=max(4, int(h * 0.012 * S)), fill=(210, 214, 226))
        P.line([(x + sx * w * 0.2, y - h * 0.1), (x + sx * w * 0.25, y)], w=max(4, int(h * 0.012 * S)), fill=(210, 214, 226))
    for sx in (-1, 1):                                                   # порожні очі
        P.ell(x + sway + sx * w * 0.2, y - h * 0.88, w * 0.1, w * 0.16, (14, 12, 22), ink=False)


def tape(P, cx, cy, w, t, date_flicker=False):
    h = w * 0.62
    P.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (26, 26, 30), r=w * 0.04, w=4)
    P.rect(cx - w * 0.42, cy - h * 0.42, cx + w * 0.42, cy + h * 0.02, (226, 218, 192), w=3)
    for k in range(1, 4):
        P.line([(cx - w * 0.4, cy - h * 0.42 + k * h * 0.11), (cx + w * 0.4, cy - h * 0.42 + k * h * 0.11)], w=2, fill=(170, 175, 205))
    P.rect(cx - w * 0.2, cy + h * 0.12, cx + w * 0.2, cy + h * 0.36, (10, 10, 12), r=w * 0.03, ink=False)
    for sx in (-1, 1):
        P.ell(cx + sx * w * 0.12, cy + h * 0.24, w * 0.05, w * 0.05, (200, 200, 200), ink=False)
    f = font(HAND, w * 0.13)
    x, y = P.p(cx - w * 0.36, cy - h * 0.4)
    P.d.text((x, y), "Tape No. 2", font=f, fill=(30, 30, 80))
    if not (date_flicker and (t * 7) % 1 < 0.2):
        x, y = P.p(cx - w * 0.14, cy - h * 0.2)
        P.d.text((x, y), "Nov 13, 2026", font=font(HAND, w * 0.085), fill=(30, 30, 80))


# ---------- план кадрів ----------
def build():
    F.SHOTS.clear()

    def bed(P, t, lt, expr="shock", arms=("down", "down")):
        actor(P, ME, 420, 2150, 1150, t, seed=1, expr=expr, arms=arms)

    def nightstand_phone(P, t, lt, mode="call"):
        phone(P, 1180, 1610, 160, t, mode)

    shot("hook", "bedroom", 0.0, Ls(1), [(0, 760, 1500, 1800, 0)],
         draw_mid=lambda P, t, lt: bed(P, t, lt), draw_front=nightstand_phone, dof=4)
    shot("callscreen", "phone", Ls(1), Ls(4), [(0, 650, 1150, 1500, 0), (Ls(3) - Ls(1), 650, 1150, 1250, 0)],
         draw_front=lambda P, t, lt: phone(P, 650, 1150, 900, t, "call"), kicks=[Ls(3)])

    def hall(P, t, lt):
        quiet = t >= Ls(5)
        actor(P, ME, 520, 2350, 1200, t, seed=2, expr="worry" if quiet else "shock", arms=("hold", "hold") if quiet else ("down", "down"))

    shot("hall", "hallway", Ls(4), Ls(6), [(0, 700, 1500, 1900, 0), (1.6, 700, 1600, 1600, 0)], draw_front=hall, xfade=True)
    shot("rule", "forest", Ls(6), Ls(7), [(0, 800, 1500, 2100, 0), (2.5, 820, 1550, 1800, 0)],
         draw_mid=lambda P, t, lt: it_figure(P, 900, 1760, 520, t, 0.8), xfade=True)
    shot("nopickup", "bedroom", Ls(7), Ls(8), [(0, 1000, 1550, 1500, 0)],
         draw_mid=lambda P, t, lt: bed(P, t, lt, expr="worry", arms=("hold", "hold")), draw_front=nightstand_phone, dof=5)
    t_ans = Ls(15)

    def vm(P, t, lt):
        wave = 0.0
        if t >= Ls(11):
            wave = 0.25 + 0.12 * math.sin(t * 3) ** 2
        if t >= Ls(12):
            wave = 0.55
        red = 1.0 if t >= t_ans else 0.0
        if t >= t_ans:
            wave = 1.0
        phone(P, 650, 1150, 900, t + 3, "vm", wave=wave, red=red)

    shot("voicemail", "phone", Ls(8), Ls(16), [(0, 650, 1150, 1500, 0), (t_ans - Ls(8), 650, 1150, 1300, 0),
                                               (t_ans - Ls(8) + 0.3, 650, 1150, 1100, 3)],
         draw_front=vm, kicks=[t_ans], creep=0.0012)
    shot("wait", "bedroom", Ls(16), Ls(17), [(0, 430, 1300, 1150, 0), (1.2, 430, 1280, 1000, -4)],
         draw_mid=lambda P, t, lt: bed(P, t, lt, expr="shock", arms=("ear", "ear")), dof=6)

    def learn(P, t, lt):
        k = 0.0 if t < Ls(18) else ss((t - Ls(18)) / 2.6)
        it_figure(P, 900 - 80 * k, 1760 + 640 * k, 520 + 900 * k, t, 0.8 + 0.6 * k)

    shot("learn", "forest", Ls(17), Ls(19), [(0, 800, 1500, 2100, 0), (Ls(18) - Ls(17), 800, 1500, 2100, 0),
                                             (Ls(19) - Ls(17), 820, 1550, 1700, 0)], draw_mid=learn, xfade=True)

    def headlights(P, t, lt):
        P.glow(760, 2700, 700, 300, (255, 240, 190), 120, 80)

    shot("road", "road", Ls(19), Ls(20), [(0, 760, 1700, 2000, 0), (3.0, 760, 1100, 1400, 0)], draw_front=headlights, xfade=True)

    def shelf(P, t, lt):
        tape(P, 470, 1000, 330 if t < Ls(21) else 330, t, date_flicker=t >= Ls(22))

    shot("shelf", "station", Ls(20), Ls(23), [(0, 700, 1300, 1900, 0), (Ls(21) - Ls(20), 470, 1050, 900, 0),
                                              (Ls(22) - Ls(20), 500, 975, 560, 0)],
         draw_front=shelf, kicks=[Ls(22)], creep=0.0008)

    def calllog(P, t, lt):
        n = 0 if t < Ls(24) else 1 + int((t - Ls(24)) * 1.5)
        phone(P, 650, 1150, 900, t, "log", log=n)

    shot("log", "phone", Ls(23), Ls(25), [(0, 650, 1150, 1500, 0), (Ls(24) - Ls(23), 650, 1000, 1200, 0)],
         draw_front=calllog, kicks=[Ls(24)])

    def final(P, t, lt):
        if t >= Ls(26):
            it_figure(P, 1125, 900, 520, t, 1.2)

    def final_front(P, t, lt):
        actor(P, ME, 600, 2400, 1250, t, seed=3, expr="sad" if t < Ls(26) else "shock", arms=("hold", "down"))
        phone(P, 650, 1750, 150, t, "log", log=1)

    shot("final", "station", Ls(25), F.DUR, [(0, 800, 1450, 1900, 0), (Ls(26) - Ls(25), 880, 1180, 1750, 0)],
         draw_mid=final, draw_front=final_front, kicks=[Ls(26)], dof=0)


F.build_shots = build

if __name__ == "__main__":
    F.main()
