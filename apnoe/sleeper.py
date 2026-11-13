"""Сплячий чоловік на боці, реакції дружини і анатомічний розріз горла для шортса про апное.

Чоловік: той самий дизайн (HIM із film_a), лежить на правому боці обличчям до камери, щока на подушці,
шия й плече під ковдрою вирівняні. Рот закритий, крім вдиху під час хропіння. Груди й плече
ледь піднімаються з диханням. Цикл хропіння 2.4 с (вдих 0–55 %) збігається зі звуком.
"""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw

import toon as T

CYCLE = 2.4
HEAD_C = (480, 1395)       # центр голови у світових координатах
K = 2.3                    # масштаб: голова такого ж розміру, як у дружини (h=1150 → k=2.3)
ANGLE = 80                 # поворот: маківка ліворуч, підборіддя праворуч


def inhale(t):
    ph = (t % CYCLE) / CYCLE
    return math.sin(math.pi * ph / 0.55) if ph < 0.55 else 0.0


def breath(t, rate=0.25):
    return 0.5 + 0.5 * math.sin(2 * math.pi * rate * t)


@lru_cache(maxsize=128)
def head(mouth: int, mask: bool, spec_key: tuple):
    """Голова прямо (дизайн 600x600, центр 300,300), потім поворот. mouth 0..10 — відкритість рота."""
    spec = dict(spec_key)
    k = K
    W = int(600 * k)
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * k, y * k)

    def L(w):
        return max(1, int(w * k))

    cx, hc = 300, 300
    hd = T.bean(cx, hc, 252, 234)
    d.polygon([(x * k, y * k) for x, y in hd], fill=spec["skin"])
    d.line([(x * k, y * k) for x, y in hd] + [(hd[0][0] * k, hd[0][1] * k)], fill=T.PLUM, width=L(6), joint="curve")
    d.line([(x * k, y * k) for x, y in hd[6:20]], fill=T.PLUM, width=L(8), joint="curve")
    hair = spec["hair"]                                                           # коротке волосся як у HIM
    d.chord([P(cx - 128, hc - 128), P(cx + 128, hc + 30)], 180, 360, fill=hair)
    d.polygon([P(cx - 122, hc - 40), P(cx - 60, hc - 70), P(cx + 40, hc - 60), P(cx + 124, hc - 40),
               P(cx + 120, hc - 80), P(cx - 120, hc - 80)], fill=hair)
    ex, ey = 33, hc + 4                                                          # закриті очі: м'які дуги вниз
    for s in (-1, 1):
        d.arc([P(cx + s * ex - 15, ey - 10), P(cx + s * ex + 15, ey + 8)], 15, 165, fill=T.INK, width=L(5))
    my = hc + 64
    if mask:
        d.rounded_rectangle([P(cx - 60, my - 52), P(cx + 60, my + 36)], radius=L(30), fill=(220, 236, 246),
                            outline=T.PLUM, width=L(5))
        d.line([P(cx + 60, my - 8), P(cx + 210, my + 40)], fill=(150, 170, 200), width=L(14))
    else:
        if mouth <= 0:
            d.arc([P(cx - 20, my - 10), P(cx + 20, my + 6)], 30, 150, fill=T.PLUM, width=L(5))   # спокійно закритий
        else:
            o = 4 + mouth * 2.2
            d.ellipse([P(cx - 10 - mouth * 0.8, my - o / 2), P(cx + 10 + mouth * 0.8, my + o / 2)],
                      fill=(110, 40, 50), outline=T.PLUM, width=L(4))
        d.polygon([P(cx - 46, my - 14), P(cx, my - 26), P(cx + 46, my - 14), P(cx + 30, my - 4), P(cx, my - 12),
                   P(cx - 30, my - 4)], fill=hair)
    img = T.lit(img, k)
    return img.rotate(ANGLE, resample=Image.BICUBIC, expand=True)


def man(P, t, spec, snoring=0.0, mask=False, vib=True):
    """snoring 0..1 — сила хропіння (рот відкривається на вдиху, легка вібрація горла)."""
    b = breath(t, 0.42 if snoring else 0.25)
    inh = inhale(t) * snoring
    jit = (1.2 * math.sin(t * 2 * math.pi * 28) * inh) if vib else 0.0
    # шия й плече: коротка шия від підборіддя до плеча, плече округле, далі тіло під ковдрою
    lift = 5 * b
    shirt = spec["shirt"]
    P.glow(470, 1500, 170, 45, (30, 26, 60), 110, 16)                              # м'яка тінь голови на подушці
    P.poly([(600, 1372 + jit), (640, 1380), (676, 1470), (612, 1486)], spec["skin"], w=4)
    P.ell(700, 1505 - lift, 120, 70, shirt, w=5)
    P.ell(730, 1515 - lift, 80, 50, T.shade(shirt), ink=False)
    spr = head(int(round(10 * inh)), mask, tuple(sorted(spec.items())))
    k_angle = 0.8 * math.sin(2 * math.pi * 0.25 * t)                                               # мікрорух голови
    if abs(k_angle) > 0.3:
        spr = spr.rotate(k_angle, resample=Image.BICUBIC)
    x, y = HEAD_C[0] + jit * 0.5, HEAD_C[1] - lift * 0.3
    P.img.alpha_composite(spr, (int(x * 2 - spr.width / 2 - P.ox), int(y * 2 - spr.height / 2 - P.oy)))
    if inh > 0.2 and vib:                                                                        # вібрація горла
        for i in range(3):
            r = 30 + i * 22 + 10 * inh
            P.arc(640, 1420, r, -40, 40, w=4, fill=(255, 250, 220, 255))


def blanket_over(P, t, snoring=0.0):
    """Ковдра облягає його плече й бік плавним горбком і піднімається з диханням."""
    b = breath(t, 0.42 if snoring else 0.25)
    lift = 6 * b
    col = (120, 150, 200)
    pts = []
    for i in range(25):                                                        # плавний горб від 560 до 900
        u = i / 24
        x = 560 + 340 * u
        y = 1562 - (60 + lift) * math.sin(math.pi * u) ** 1.3
        pts.append((x, y))
    P.poly(pts + [(900, 1600), (560, 1600)], col, ink=False)
    P.line(pts, w=5)
    P.line([(620, 1548), (700, 1522 - lift), (790, 1518 - lift)], w=3, fill=(100, 128, 180))


# ---------- анатомічний розріз (сагітальний, профіль ліворуч) ----------
SKIN = (240, 204, 172)
TISSUE = (242, 178, 176)
DEEP = (214, 130, 136)
AIR = (226, 238, 255)
BONE = (246, 236, 210)


def anatomy(P, t, relax=0.0, close=0.0, flow=True):
    """relax 0..1 — м'яке піднебіння провисає і вібрує (хропіння); close 0..1 — язик і піднебіння
    западають до задньої стінки глотки, дихальний шлях закривається."""
    ink = 5
    # зовнішній контур голови й шиї
    outline = [(600, 470), (480, 540), (430, 700), (400, 790), (330, 865), (360, 900), (420, 905), (402, 965),
               (410, 1000), (400, 1040), (430, 1130), (560, 1190), (610, 1260), (612, 1950), (1000, 1950),
               (1000, 1250), (1030, 1000), (1020, 720), (900, 520), (760, 465)]
    P.poly(outline, SKIN, w=ink)
    P.poly([(q[0] + (8 if q[0] > 500 else 10), q[1]) for q in outline[2:16]] + [(990, 1950), (990, 1250)], TISSUE, ink=False)
    P.poly(outline, None, w=ink)
    # хребет (позаду глотки)
    for i in range(9):
        y = 930 + i * 112
        P.rect(905, y, 990, y + 96, BONE, r=16, w=4)
    # тверде піднебіння (кістка) — дно носової порожнини, дах рота
    P.poly([(420, 945), (720, 935), (722, 962), (430, 975)], BONE, w=4)
    # носова порожнина: повітря від ніздрі до носоглотки
    P.poly([(345, 880), (430, 860), (600, 830), (760, 835), (860, 870), (870, 935), (722, 935), (420, 945)], AIR, w=4)
    for y in (870, 900):                                                             # носові раковини
        P.ell(600, y, 90, 12, DEEP, w=3)
    # глотка: повітряний канал позаду язика (задня стінка x≈890)
    back = 890
    sag = 25 * relax + 60 * close
    front_top = 800 + 70 * close
    P.poly([(760, 935), (back, 935), (back, 1300), (front_top + 60, 1300), (front_top, 1160), (790, 1060)], AIR, w=4)
    # трахея (спереду) з хрящовими кільцями і стравохід (позаду, зімкнутий)
    P.rect(690, 1300, 820, 1950, AIR, w=4)
    for y in range(1340, 1940, 55):
        P.line([(692, y), (818, y)], w=6, fill=(250, 220, 220))
    P.rect(830, 1300, 895, 1950, DEEP, w=4)
    # надгортанник
    P.poly([(800, 1250), (842, 1196), (856, 1206), (820, 1262)], DEEP, w=4)
    # ротова порожнина і язик
    P.poly([(410, 1000), (460, 980), (720, 975), (790, 1010), (790, 1060), (440, 1060)], AIR, w=4)
    tb = 70 * close + 18 * relax                                                     # корінь язика западає назад
    tongue = [(445, 1065), (520, 1010), (640, 985), (760, 1000), (800 + tb * 0.6, 1060), (front_top + tb * 0.4, 1170),
              (front_top + 40 + tb * 0.3, 1290), (640, 1250), (520, 1170)]
    P.poly(tongue, DEEP, w=ink)
    P.line([(520, 1060), (640, 1030), (740, 1040)], w=3, fill=(240, 160, 170))
    # м'яке піднебіння з язичком: продовження твердого, звисає в глотку
    vib = math.sin(t * 2 * math.pi * 6) * 12 * relax * (1 - close)
    root = (722, 948)
    tip_x = 800 + sag + vib
    tip_y = 1060 + 20 * relax + 30 * close
    P.poly([root, (730, 935), (790, 960), (tip_x + 14, tip_y - 6), (tip_x, tip_y + 16), (tip_x - 18, tip_y), (760, 985), (722, 968)], DEEP, w=ink)
    if relax > 0.2 and close < 0.6:                                                   # лінії вібрації = звук хропіння
        for i in range(3):
            P.arc(tip_x + 10, tip_y, 30 + i * 24, -60, 60, w=4, fill=(255, 250, 200))
    # потік повітря: точки рухаються ніс → носоглотка → глотка → трахея
    path = [(360, 885), (600, 870), (830, 885), (860, 1000), (850, 1200), (760, 1320), (755, 1900)]
    if flow:
        stop = 1.0 if close < 0.5 else 0.42
        for i in range(10):
            u = ((t * 0.35 + i / 10) % 1.0) * stop
            seg = u * (len(path) - 1)
            j = min(int(seg), len(path) - 2)
            f = seg - j
            x = path[j][0] + (path[j + 1][0] - path[j][0]) * f
            y = path[j][1] + (path[j + 1][1] - path[j][1]) * f
            P.ell(x, y, 12, 12, (70, 140, 230), ink=False)
    if close > 0.7:                                                                   # місце перекриття
        P.glow(850, 1110, 90, 90, (255, 60, 60), int(120 * (close - 0.7) / 0.3), 30)
