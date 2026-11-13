"""Персонажі «Канцелярська драма»: ТАТО-олівець, МАМА-ручка, МАЛЮК-маркер, СУСІД-маркер.

Малюються у світових координатах через Pen рушія (film.Pen), тонкий чорний контур як у наших мультиках,
двотонова світлотінь (світло зліва), м'які відблиски. Усі пропорції задані тут один раз — однакові в кожному кадрі.
"""
from __future__ import annotations

import math

INK = (11, 10, 12)
YELLOW = (250, 204, 46)
YELLOW_D = (214, 160, 26)
YELLOW_L = (255, 230, 120)
ERASER = (244, 140, 160)
FERRULE = (196, 200, 210)
JEANS = (62, 104, 170)
JEANS_D = (44, 76, 132)
PEN_BODY = (200, 226, 250)
PEN_CAP = (40, 90, 200)
INK_BLUE = (30, 60, 170)
NEON = (232, 255, 60)
NEON_D = (186, 214, 30)
GREEN = (60, 170, 80)
WHITE = (252, 252, 250)


# ---------- обличчя ----------
def eye(P, cx, cy, r, t, look=(0.0, 0.0), lid=0.0, spiral=False, lashes=False, iris=GREEN, squint_low=0.0):
    P.ell(cx, cy, r, r * 1.12, WHITE, w=4)
    if spiral:                                                         # гіпнотична спіраль
        a0 = t * 9
        pts = []
        for i in range(60):
            a = a0 + i * 0.32
            rr = r * 0.9 * i / 60
            pts.append((cx + rr * math.cos(a), cy + rr * 1.1 * math.sin(a)))
        P.line(pts, w=5, fill=(120, 40, 160))
    else:
        ix, iy = cx + look[0] * r * 0.38, cy + look[1] * r * 0.3
        P.ell(ix, iy, r * 0.55, r * 0.6, iris, ink=False)
        P.ell(ix, iy, r * 0.28, r * 0.3, INK, ink=False)
        P.ell(ix - r * 0.18, iy - r * 0.22, r * 0.12, r * 0.12, WHITE, ink=False)   # відблиск
    if lid > 0:                                                        # верхня повіка
        P.poly([(cx - r * 1.05, cy - r * 1.2), (cx + r * 1.05, cy - r * 1.2),
                (cx + r * 1.05, cy - r * 1.2 + lid * r * 2.2), (cx - r * 1.05, cy - r * 1.2 + lid * r * 2.2)],
               None, ink=False)
        P.rect(cx - r * 1.04, cy - r * 1.18, cx + r * 1.04, cy - r * 1.18 + lid * r * 2.2, _SKIN[0], ink=False)
        P.line([(cx - r, cy - r * 1.18 + lid * r * 2.2), (cx + r, cy - r * 1.18 + lid * r * 2.2)], w=5)
    if squint_low > 0:
        P.rect(cx - r * 1.04, cy + r * 1.18 - squint_low * r * 1.2, cx + r * 1.04, cy + r * 1.2, _SKIN[0], ink=False)
        P.line([(cx - r, cy + r * 1.18 - squint_low * r * 1.2), (cx + r, cy + r * 1.18 - squint_low * r * 1.2)], w=4)
    if lashes:
        for k in range(3):
            a = math.radians(-120 + k * 30)
            x0, y0 = cx + r * 0.95 * math.cos(a), cy + r * 1.05 * math.sin(a) + lid * r * 2.0
            P.line([(x0, y0), (x0 + r * 0.45 * math.cos(a), y0 + r * 0.5 * math.sin(a))], w=6)


_SKIN = [YELLOW]   # колір «шкіри» для повік поточного персонажа


def brow(P, cx, cy, w, ang, thick=14):
    a = math.radians(ang)
    dx, dy = w / 2 * math.cos(a), w / 2 * math.sin(a)
    P.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], w=thick, fill=(60, 40, 30))


def mouth(P, cx, cy, w, open_=0.0, shape="neutral"):
    if shape == "nervous":                                             # винувата усмішка-«зигзаг»
        P.line([(cx - w / 2, cy), (cx - w / 4, cy - 10), (cx, cy + 6), (cx + w / 4, cy - 10), (cx + w / 2, cy)], w=6)
        if open_ > 0.1:
            P.ell(cx, cy + 8, w * 0.25, w * 0.12 * open_ + 4, (110, 30, 40))
        return
    if open_ > 0.08:
        h = w * 0.15 + w * 0.6 * open_
        P.ell(cx, cy + h * 0.3, w * 0.42, h * 0.5, (110, 30, 40), w=5)
        P.ell(cx, cy + h * 0.55, w * 0.22, h * 0.18, (230, 100, 110), ink=False)
    elif shape == "smile":
        P.arc(cx, cy - w * 0.3, w * 0.5, 30, 150, w=6)
    elif shape == "frown":
        P.arc(cx, cy + w * 0.4, w * 0.45, 210, 330, w=6)
    else:
        P.line([(cx - w * 0.3, cy), (cx + w * 0.3, cy)], w=6)


def arm(P, sx, sy, hx, hy, bend=1.0, w=11, col=INK):
    mx, my = (sx + hx) / 2 + bend * (hy - sy) * 0.15, (sy + hy) / 2 - bend * (hx - sx) * 0.15
    P.line([(sx, sy), (mx, my), (hx, hy)], w=w, fill=col)
    P.ell(hx, hy, 18, 18, (40, 34, 30), ink=False)


# ---------- ТАТО: олівець ----------
def dad(P, x, y, t, s=1.0, walk=None, point=False, tremble=0.0, spiral=False, mouth_open=0.0, expr="neutral",
        look=(0, 0), lid=0.0, lean=0.0, dizzy=0.0, yellow_line=0.0, arms_up=False):
    """x, y — точка між ступнями; висота ~1500*s."""
    _SKIN[0] = YELLOW
    sh = tremble * 6 * math.sin(t * 70)
    wob = dizzy * 9 * math.sin(t * 7)                                  # хитання після удару
    bob = 0.0
    if walk is not None:
        bob = 14 * abs(math.sin(walk * math.pi))
    X = lambda dx: x + (dx + sh) * s + lean * s * 0.0           # noqa: E731
    top = y - 1500 * s - bob * s
    tilt = math.radians(wob + lean)

    def R(px, py):                                                     # нахил тіла навколо ступнів
        dx, dy = px - x, py - y
        return (x + dx * math.cos(tilt) - dy * math.sin(tilt) + sh * s, y + dx * math.sin(tilt) + dy * math.cos(tilt))

    def poly(pts, col, ink=True):
        P.poly([R(*q) for q in pts], col, ink=ink, w=5)

    bw = 150 * s                                                       # півширина корпусу
    # ноги в джинсах
    legs_y = y - 330 * s
    for side, ph in ((-1, 0.0), (1, 0.5)):
        stride = 0.0 if walk is None else 60 * math.sin((walk + ph) * 2 * math.pi)
        hip = R(x + side * 60 * s, legs_y)
        foot = R(x + side * 70 * s + stride * s, y - 20 * s)
        P.line([hip, foot], w=int(48 * s * 2), fill=JEANS)
        P.ell(foot[0] + side * 12 * s, foot[1] + 4 * s, 46 * s, 22 * s, (40, 40, 48), w=4)
    # джинси (низ корпусу)
    poly([(x - bw, y - 640 * s), (x + bw, y - 640 * s), (x + bw, y - 320 * s), (x - bw, y - 320 * s)], JEANS)
    poly([(x + bw * 0.45, y - 640 * s), (x + bw, y - 640 * s), (x + bw, y - 320 * s), (x + bw * 0.45, y - 320 * s)], JEANS_D, ink=False)
    P.line([R(x - bw, y - 600 * s), R(x + bw, y - 600 * s)], w=6, fill=(214, 172, 60))           # ремінь-шов
    # жовтий шестигранний корпус: три грані
    body_top, body_bot = top + 230 * s, y - 640 * s
    poly([(x - bw, body_top), (x + bw, body_top), (x + bw, body_bot), (x - bw, body_bot)], YELLOW)
    poly([(x - bw, body_top), (x - bw * 0.45, body_top), (x - bw * 0.45, body_bot), (x - bw, body_bot)], YELLOW_L, ink=False)
    poly([(x + bw * 0.45, body_top), (x + bw, body_top), (x + bw, body_bot), (x + bw * 0.45, body_bot)], YELLOW_D, ink=False)
    poly([(x - bw, body_top), (x + bw, body_top), (x + bw, body_bot), (x - bw, body_bot)], None)
    # металева обойма і гумка-«зачіска»
    poly([(x - bw * 1.02, top + 150 * s), (x + bw * 1.02, top + 150 * s), (x + bw * 1.02, body_top), (x - bw * 1.02, body_top)], FERRULE)
    for k in range(3):
        yy = top + 165 * s + k * 22 * s
        P.line([R(x - bw, yy), R(x + bw, yy)], w=4, fill=(150, 154, 166))
    er = [R(x - bw * 0.95, top + 150 * s), R(x - bw * 0.95, top + 60 * s), R(x - bw * 0.6, top), R(x + bw * 0.6, top),
          R(x + bw * 0.95, top + 60 * s), R(x + bw * 0.95, top + 150 * s)]
    P.poly(er, ERASER, w=5)
    P.poly([R(x - bw * 0.7, top + 40 * s), R(x - bw * 0.3, top + 15 * s), R(x - bw * 0.35, top + 60 * s)], (255, 190, 200), ink=False)
    # обличчя
    fy = top + 420 * s
    for side in (-1, 1):
        ex, ey = R(x + side * 62 * s, fy)
        eye(P, ex, ey, 52 * s, t, look=look, lid=lid, spiral=spiral, squint_low=0.35 if lid > 0.3 else 0.0)
    b_ang = {"angry": 18, "furious": 26, "suspicious": 10, "shock": -14, "dizzy": -6}.get(expr, 0)
    for side in (-1, 1):
        bx, by = R(x + side * 66 * s, fy - 80 * s - (10 * s if expr == "shock" else 0))
        brow(P, bx, by, 88 * s, side * b_ang, thick=int(22 * s * 2) // 2 + 6)
    mx, my = R(x, fy + 150 * s)
    shape = {"angry": "frown", "furious": "frown", "suspicious": "frown"}.get(expr, "neutral")
    mouth(P, mx, my, 120 * s, mouth_open, shape)
    if yellow_line > 0:                                                # смуга від маркера через обличчя
        x0, y0 = R(x - bw * 1.1, fy + 40 * s)
        x1, y1 = R(x - bw * 1.1 + bw * 2.3 * yellow_line, fy - 30 * s)
        P.line([(x0, y0), (x1, y1)], w=int(40 * s * 2), fill=NEON)
    # руки
    shx, shy = R(x - bw, body_top + 140 * s)
    srx, sry = R(x + bw, body_top + 140 * s)
    if point:
        arm(P, srx, sry, srx + 360 * s, sry - 60 * s + sh * 2, bend=0.2)
    elif arms_up:
        arm(P, srx, sry, srx + 160 * s, sry - 260 * s)
    else:
        swing = 0 if walk is None else 40 * math.sin(walk * 2 * math.pi)
        arm(P, srx, sry, srx + 70 * s, sry + 300 * s + swing * s * 0.3, bend=-0.6)
    swing = 0 if walk is None else -40 * math.sin(walk * 2 * math.pi)
    arm(P, shx, shy, shx - 70 * s - swing * s * 0.3, shy + 300 * s, bend=0.6)
    if dizzy > 0:                                                      # зірочки довкола гумки
        for i in range(4):
            a = t * 5 + i * math.pi / 2
            cx, cy = x + 170 * s * math.cos(a), top + 40 * s + 50 * s * math.sin(a)
            _star(P, cx, cy, 34 * s)


def _star(P, cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    P.poly(pts, (255, 226, 80), w=4)


# ---------- МАМА: кулькова ручка ----------
def mom(P, x, y, t, s=1.0, baby_on=True, look=(0, 0), mouth_open=0.0, expr="neutral", sweat=0.0, ruler=None,
        freeze=False):
    """Прозорий корпус зі стрижнем усередині, синій ковпачок із затиском, вії, фартух з рюшами."""
    _SKIN[0] = PEN_BODY
    bw = 125 * s
    top = y - 1250 * s
    # ноги
    for side in (-1, 1):
        P.line([(x + side * 45 * s, y - 230 * s), (x + side * 50 * s, y - 20 * s)], w=int(16 * s * 2), fill=(40, 40, 60))
        P.ell(x + side * 58 * s, y - 10 * s, 40 * s, 18 * s, (30, 60, 150), w=4)
    # конусний «носик» унизу і прозорий корпус
    P.poly([(x - bw, y - 300 * s), (x + bw, y - 300 * s), (x + 30 * s, y - 210 * s), (x - 30 * s, y - 210 * s)], (180, 200, 220), w=5)
    P.rect(x - bw, top + 300 * s, x + bw, y - 300 * s, PEN_BODY, w=5, r=30 * s)
    P.rect(x - bw * 0.7, top + 320 * s, x - bw * 0.45, y - 320 * s, (235, 246, 255), ink=False, r=10 * s)   # відблиск
    P.rect(x - 16 * s, top + 660 * s, x + 16 * s, y - 320 * s, INK_BLUE, ink=False, r=8 * s)                  # стрижень (нижче обличчя)
    # ковпачок-«зачіска» із затиском
    P.rect(x - bw * 1.05, top, x + bw * 1.05, top + 330 * s, PEN_CAP, w=5, r=60 * s)
    P.rect(x - bw * 0.6, top + 30 * s, x - bw * 0.3, top + 280 * s, (90, 140, 240), ink=False, r=10 * s)
    P.rect(x + bw * 0.75, top + 40 * s, x + bw * 1.0, top + 420 * s, (210, 214, 226), w=4, r=8 * s)     # затиск
    # фартух з рюшами
    ay0, ay1 = top + 640 * s, y - 330 * s
    P.rect(x - bw * 0.85, ay0, x + bw * 0.85, ay1, WHITE, w=4, r=20 * s)
    for i in range(7):
        cx = x - bw * 0.85 + i * bw * 1.7 / 6
        P.ell(cx, ay1, bw * 0.16, bw * 0.12, WHITE, w=3)
    P.line([(x - bw, ay0 + 10 * s), (x + bw, ay0 + 10 * s)], w=6, fill=(240, 240, 240))
    # обличчя
    fy = top + 470 * s
    for side in (-1, 1):
        eye(P, x + side * 50 * s, fy, 44 * s, t, look=look, lashes=True, lid=0.0)
    if expr == "shock":
        for side in (-1, 1):
            brow(P, x + side * 52 * s, fy - 80 * s, 60 * s, -side * 12, thick=8)
    mshape = "nervous" if expr == "nervous" else ("smile" if expr == "smile" else "neutral")
    if expr == "shock":
        P.ell(x, fy + 120 * s, 22 * s, 30 * s, (110, 30, 40), w=4)
    else:
        mouth(P, x, fy + 118 * s, 95 * s, mouth_open, mshape)
    if sweat > 0:                                                       # крапля чорнила на лобі
        dy = 40 * s * min(1, sweat)
        P.poly([(x + 95 * s, fy - 120 * s + dy), (x + 112 * s, fy - 70 * s + dy), (x + 78 * s, fy - 70 * s + dy)], INK_BLUE, w=3)
        P.ell(x + 95 * s, fy - 62 * s + dy, 18 * s, 18 * s, INK_BLUE, w=3)
    # руки
    sl, sr = (x - bw, top + 700 * s), (x + bw, top + 700 * s)
    if ruler is not None:                                               # замах лінійкою лівою рукою (кут у градусах)
        a = math.radians(ruler)
        hx, hy = sl[0] - 40 * s, sl[1] - 180 * s
        arm(P, *sl, hx, hy, bend=-0.3)
        ex, ey = hx + 700 * s * math.cos(a), hy - 700 * s * math.sin(a)
        nx, ny = -math.sin(a) * 45 * s, -math.cos(a) * 45 * s
        P.poly([(hx + nx, hy + ny), (ex + nx, ey + ny), (ex - nx, ey - ny), (hx - nx, hy - ny)], (214, 170, 110), w=4)
        for k in range(1, 12):
            px, py = hx + (ex - hx) * k / 12, hy + (ey - hy) * k / 12
            P.line([(px + nx, py + ny), (px + nx * 0.5, py + ny * 0.5)], w=3)
        arm(P, *sr, x + 40 * s, top + 880 * s, bend=-0.8)                 # друга рука тримає малюка
    elif baby_on:
        arm(P, *sl, x - 20 * s, top + 900 * s, bend=0.8)
        arm(P, *sr, x + 40 * s, top + 880 * s, bend=-0.8)
    else:
        arm(P, *sl, sl[0] - 70 * s, sl[1] + 290 * s, bend=0.6)
        arm(P, *sr, sr[0] + 70 * s, sr[1] + 290 * s, bend=-0.6)


# ---------- МАЛЮК: неоновий маркер у ковдрі ----------
def baby(P, cx, cy, t, s=1.0, blink=False, giggle=0.0, glow=1.0, draw_arm=None):
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    P.glow(cx, cy - 40 * s, 230 * s, 230 * s, (240, 255, 80), int(150 * glow * pulse), 60 * s)
    P.ell(cx, cy + 40 * s, 170 * s, 120 * s, WHITE, w=4)                                 # ковдра
    P.rect(cx - 95 * s, cy - 170 * s, cx + 95 * s, cy + 40 * s, NEON, w=4, r=80 * s)        # пухке тільце
    P.rect(cx - 60 * s, cy - 150 * s, cx - 30 * s, cy - 10 * s, (250, 255, 170), ink=False, r=12 * s)
    P.poly([(cx - 60 * s, cy - 168 * s), (cx + 60 * s, cy - 168 * s), (cx + 30 * s, cy - 215 * s), (cx - 40 * s, cy - 205 * s)], NEON_D, w=4)  # скошений кінчик
    P.poly([(cx - 170 * s, cy + 10 * s), (cx + 170 * s, cy + 10 * s), (cx + 120 * s, cy + 150 * s), (cx - 120 * s, cy + 150 * s)], WHITE, w=4)
    for side in (-1, 1):
        ex, ey = cx + side * 42 * s, cy - 90 * s
        if blink:
            P.arc(ex, ey - 6 * s, 26 * s, 20, 160, w=5)
        else:
            P.ell(ex, ey, 30 * s, 36 * s, WHITE, w=3)
            P.ell(ex, ey + 4 * s, 22 * s, 26 * s, (40, 40, 40), ink=False)
            P.ell(ex - 8 * s, ey - 8 * s, 8 * s, 8 * s, WHITE, ink=False)
    if giggle > 0:
        P.ell(cx, cy - 30 * s, 26 * s, 16 * s + 10 * s * giggle * abs(math.sin(t * 18)), (140, 40, 50), w=3)
    else:
        P.arc(cx, cy - 42 * s, 22 * s, 30, 150, w=5)
    if draw_arm is not None:                                            # ручка з маркер-кінчиком тягнеться
        hx, hy = draw_arm
        P.line([(cx + 80 * s, cy - 60 * s), (hx, hy)], w=int(12 * s * 2), fill=NEON_D)
        P.ell(hx, hy, 16 * s, 16 * s, NEON, w=3)


# ---------- СУСІД: маркер без ковпачка, у темних окулярах ----------
def neighbor(P, x, y, t, s=1.0, lean=8.0, mouth_open=0.0):
    a = math.radians(lean)

    def R(px, py):
        dx, dy = px - x, py - y
        return (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))

    bw = 140 * s
    top = y - 1400 * s
    P.glow(*R(x, y - 800 * s), 260 * s, 600 * s, (230, 255, 80), 60, 50 * s)
    for side in (-1, 1):
        P.line([R(x + side * 50 * s, y - 220 * s), R(x + side * 55 * s, y - 10 * s)], w=int(16 * s * 2), fill=(40, 40, 50))
    P.poly([R(x - bw, top + 200 * s), R(x + bw, top + 200 * s), R(x + bw, y - 220 * s), R(x - bw, y - 220 * s)], NEON, w=5)
    P.poly([R(x + bw * 0.45, top + 200 * s), R(x + bw, top + 200 * s), R(x + bw, y - 220 * s), R(x + bw * 0.45, y - 220 * s)], NEON_D, ink=False)
    P.poly([R(x - bw, top + 200 * s), R(x + bw, top + 200 * s), R(x + bw, y - 220 * s), R(x - bw, y - 220 * s)], None, w=5)
    # без ковпачка: відкритий скошений фетровий кінчик
    P.poly([R(x - bw * 0.7, top + 205 * s), R(x + bw * 0.7, top + 205 * s), R(x + bw * 0.5, top + 90 * s), R(x - bw * 0.3, top + 30 * s)], (210, 240, 40), w=5)
    # темні окуляри
    fy = top + 400 * s
    for side in (-1, 1):
        P.poly([R(x + side * 20 * s, fy - 40 * s), R(x + side * 120 * s, fy - 40 * s), R(x + side * 110 * s, fy + 30 * s),
                R(x + side * 30 * s, fy + 34 * s)], (20, 20, 26), w=4)
        P.poly([R(x + side * 40 * s, fy - 30 * s), R(x + side * 70 * s, fy - 30 * s), R(x + side * 50 * s, fy - 5 * s)], (90, 90, 110), ink=False)
    P.line([R(x - 20 * s, fy - 30 * s), R(x + 20 * s, fy - 30 * s)], w=6)
    mx, my = R(x + 10 * s, fy + 130 * s)
    if mouth_open > 0.08:
        mouth(P, mx, my, 90 * s, mouth_open)
    else:
        P.arc(mx - 10 * s, my - 30 * s, 45 * s, 20, 120, w=6)                         # самовпевнена півусмішка
    sr = R(x + bw, top + 600 * s)
    arm(P, *sr, *R(x + bw + 160 * s, top + 420 * s), bend=-0.4)                         # рука на одвірку
    sl = R(x - bw, top + 600 * s)
    arm(P, *sl, *R(x - bw - 40 * s, top + 900 * s), bend=0.6)
