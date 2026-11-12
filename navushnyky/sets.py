"""Локації (фони) у стилі скіла: насичені мальовані кольори, тепле світло, синьо-фіолетові тіні,
чорні контури ~3 px на 1080. Малюється у 2x (S=2) в одиницях кадру 1080x1920.
Кожна функція повертає (bg RGB, fg RGBA | None): fg — передній план, що закриває персонажів.
"""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 2
INK = (11, 10, 12)
LW = 6  # товщина контуру у 2x (=3 px на 1080)


def canvas(w, h, top, bot):
    g = np.linspace(0, 1, h * S)[:, None, None]
    a = np.array(top) * (1 - g) + np.array(bot) * g
    return Image.fromarray(np.broadcast_to(a, (h * S, w * S, 3)).astype(np.uint8))


def B(box):
    return [v * S for v in box]


def rect(d, box, fill, ink=True, r=0, w=LW):
    if r:
        d.rounded_rectangle(B(box), radius=r * S, fill=fill, outline=INK if ink else None, width=w if ink else 0)
    else:
        d.rectangle(B(box), fill=fill, outline=INK if ink else None, width=w if ink else 0)


def poly(d, pts, fill, ink=True, w=LW):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=INK if ink else None, width=w if ink else 0)


def line(d, pts, w=LW, fill=INK):
    d.line([(x * S, y * S) for x, y in pts], fill=fill, width=w, joint="curve")


def ell(d, box, fill, ink=True, w=LW):
    d.ellipse(B(box), fill=fill, outline=INK if ink else None, width=w if ink else 0)


def glow(img, box, color, alpha=90, blur=60):
    """М'яка пляма світла (віконне світло, лампа)."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse(B(box), fill=alpha)
    img.paste(Image.new("RGB", img.size, color), (0, 0), m.filter(ImageFilter.GaussianBlur(blur * S)))


def shade_c(c, k=0.7):
    return tuple(int(v * k + t * (1 - k) * 0.6) for v, t in zip(c, (40, 40, 95)))


def grain_wall(img, box, strength=5, seed=1):
    """Мальована фактура стіни: м'які мазки."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = box
    for _ in range(int((x1 - x0) * (y1 - y0) / 9000)):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.uniform(20, 60)
        c = rnd.choice([(255, 255, 255, strength), (0, 0, 40, strength)])
        d.ellipse(B((x - r, y - r * 0.5, x + r, y + r * 0.5)), fill=c)


# ---------- кухня ----------
def kitchen(eve=False):
    W, H = 1500, 2500
    wall = (236, 206, 140) if not eve else (120, 120, 178)
    img = canvas(W, H, wall, shade_c(wall, 0.85))
    d = ImageDraw.Draw(img)
    grain_wall(img, (0, 0, W, 1500), seed=2)
    rect(d, (0, 1180, W, 1500), (170, 96, 70) if not eve else (90, 70, 110), ink=False)       # панель
    for x in range(0, W, 90):
        line(d, [(x, 1180), (x, 1500)], w=3, fill=shade_c((170, 96, 70), 0.7))
    line(d, [(0, 1180), (W, 1180)])
    # підлога: плитка в перспективі
    floor = (196, 82, 64) if not eve else (90, 70, 120)
    poly(d, [(0, 1500), (W, 1500), (W, H), (0, H)], floor, ink=False)
    for i in range(-10, 22):
        line(d, [(W / 2 + i * 70, 1500), (W / 2 + i * 260, H)], w=3, fill=shade_c(floor, 0.8))
    for k in range(9):
        y = 1500 + (H - 1500) * (k / 9) ** 1.6
        line(d, [(0, y), (W, y)], w=3, fill=shade_c(floor, 0.8))
    line(d, [(0, 1500), (W, 1500)])
    # вікно
    sky = (150, 200, 245) if not eve else (40, 50, 110)
    rect(d, (180, 420, 640, 1020), sky)
    if eve:
        ell(d, (480, 470, 560, 550), (245, 240, 210), ink=False)
    rect(d, (180, 420, 640, 1020), None)
    line(d, [(410, 420), (410, 1020)], w=12, fill=(250, 245, 230))
    line(d, [(180, 720), (640, 720)], w=12, fill=(250, 245, 230))
    rect(d, (150, 1010, 670, 1050), (250, 245, 230))
    poly(d, [(130, 400), (260, 400), (220, 1060), (110, 1060)], (200, 70, 80))    # фіранки
    poly(d, [(690, 400), (560, 400), (600, 1060), (710, 1060)], (200, 70, 80))
    # полиці з банками
    rect(d, (820, 520, 1380, 548), (150, 90, 50))
    rect(d, (820, 800, 1380, 828), (150, 90, 50))
    rnd = random.Random(3)
    for shelf in (520, 800):
        x = 840
        while x < 1340:
            w = rnd.uniform(50, 90)
            h = rnd.uniform(90, 160)
            c = rnd.choice([(230, 120, 60), (90, 160, 120), (220, 200, 90), (130, 120, 200), (240, 240, 230)])
            rect(d, (x, shelf - h, x + w, shelf), c, r=10)
            rect(d, (x + 8, shelf - h - 18, x + w - 8, shelf - h + 4), (120, 70, 40))
            x += w + rnd.uniform(14, 30)
    # плита
    rect(d, (1120, 1060, 1440, 1500), (44, 44, 56), r=12)
    rect(d, (1150, 1200, 1410, 1440), (30, 30, 40), r=8)
    rect(d, (1230, 700, 1300, 1060), (44, 44, 56))
    for x in (1170, 1290):
        ell(d, (x, 1080, x + 100, 1130), (70, 70, 84))
    if not eve:
        glow(img, (250, 1100, 1050, 1800), (255, 236, 170), 110, 70)    # сонячна пляма
    else:
        glow(img, (500, 600, 1100, 1300), (255, 200, 110), 120, 60)     # лампа
    # стіл (передній план)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    wood = (170, 104, 52)
    poly(fd, [(120, 1560), (1380, 1560), (1450, 1700), (50, 1700)], wood)
    rect(fd, (50, 1700, 1450, 1760), shade_c(wood, 0.8))
    for x in (110, 1350):
        rect(fd, (x, 1760, x + 50, 2300), shade_c(wood, 0.7))
    for x in range(200, 1400, 180):
        line(fd, [(x, 1572), (x - 30, 1690)], w=3, fill=shade_c(wood, 0.8) + (255,))
    if eve:
        lamp = (700, 1180)
        rect(fd, (lamp[0] - 60, lamp[1] + 250, lamp[0] + 60, lamp[1] + 380), (214, 172, 60), r=20)
    return img, fg


def wire_pile(fd, cx, cy, r=110, seed=5):
    rnd = random.Random(seed)
    for _ in range(36):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(r * 0.3, r)
        line(fd, [(cx + rr * math.cos(a), cy + rr * 0.4 * math.sin(a)),
                  (cx + rr * math.cos(a + 2), cy + rr * 0.4 * math.sin(a + 2))], w=5,
             fill=rnd.choice([(200, 120, 60), (180, 100, 40), (220, 150, 80)]) + (255,))


# ---------- містечко з храмом ----------
def town():
    W, H = 1500, 3400
    img = canvas(W, H, (62, 127, 210), (184, 208, 236))
    d = ImageDraw.Draw(img)
    for cx, cy, r in ((260, 380, 120), (420, 360, 90), (1100, 560, 140), (1280, 520, 100)):
        for ox in (-r, 0, r):
            ell(d, (cx + ox - r, cy - r * 0.6, cx + ox + r, cy + r * 0.6), (252, 252, 255), ink=False)
    poly(d, [(0, 1700), (250, 1250), (520, 1520), (800, 1100), (1100, 1480), (1350, 1200), (1500, 1400), (1500, 1900),
             (0, 1900)], (120, 110, 170))                                            # гори Уосатч
    poly(d, [(250, 1250), (310, 1350), (220, 1330), (190, 1360)], (240, 240, 250), ink=False)
    poly(d, [(800, 1100), (870, 1210), (760, 1200)], (240, 240, 250), ink=False)
    rect(d, (0, 1800, W, H), (120, 170, 90), ink=False)
    # храм: гранітний, шпилі
    stone = (204, 198, 184)
    rect(d, (430, 1300, 1070, 2150), stone)
    for x in (430, 590, 910, 1010):
        w = 60 if x in (430, 1010) else 90
        xx = x if x != 1010 else 1010
        rect(d, (xx, 1060, xx + w, 1320), stone)
        poly(d, [(xx - 4, 1060), (xx + w + 4, 1060), (xx + w / 2, 900)], shade_c(stone, 0.85))
    poly(d, [(735, 760), (765, 760), (770, 1080), (730, 1080)], (214, 172, 60))      # центральний шпиль
    rect(d, (690, 1080, 810, 1320), stone)
    for i in range(5):
        x = 470 + i * 120
        rect(d, (x, 1450, x + 60, 1650), (70, 90, 150), r=30)
        rect(d, (x, 1780, x + 60, 1980), (70, 90, 150), r=30)
    poly(d, [(1070, 1300), (1120, 1340), (1120, 2150), (1070, 2150)], shade_c(stone, 0.65))
    rect(d, (690, 2000, 810, 2150), (110, 70, 50), r=40)
    # будиночки й дерева
    rnd = random.Random(8)
    for i, x in enumerate(range(-40, 1540, 260)):
        h = rnd.uniform(380, 520)
        c = rnd.choice([(190, 110, 80), (230, 205, 150), (210, 160, 90), (160, 90, 80)])
        y1 = 2700
        rect(d, (x, y1 - h, x + 220, y1), c)
        poly(d, [(x - 20, y1 - h), (x + 240, y1 - h), (x + 110, y1 - h - 140)], (150, 60, 50))
        rect(d, (x + 30, y1 - h + 80, x + 90, y1 - h + 170), (150, 200, 240))
        rect(d, (x + 130, y1 - 170, x + 190, y1), (110, 70, 50))
        poly(d, [(x + 220, y1 - h), (x + 236, y1 - h + 10), (x + 236, y1), (x + 220, y1)], shade_c(c, 0.6))
    for x in (90, 600, 1180):
        rect(d, (x, 2520, x + 30, 2750), (110, 70, 40))
        ell(d, (x - 110, 2300, x + 140, 2560), (80, 150, 70))
    rect(d, (0, 2700, W, H), (200, 180, 140), ink=False)                            # вулиця
    line(d, [(0, 2700), (W, 2700)])
    return img, None


# ---------- храм усередині ----------
def church():
    W, H = 1400, 2500
    img = canvas(W, H, (214, 190, 150), (160, 130, 100))
    d = ImageDraw.Draw(img)
    grain_wall(img, (0, 0, W, 1500), seed=4)
    for x in (120, 520, 920):
        rect(d, (x, 200, x + 340, 1050), (150, 190, 240), r=170)
        line(d, [(x + 170, 200), (x + 170, 1050)], w=8, fill=(240, 230, 200))
    for i in range(14):                                       # труби органа
        x = 470 + i * 34
        rect(d, (x, 1000 - (abs(i - 6.5) < 3) * 160 - 200, x + 26, 1250), (214, 172, 60), r=12)
    rect(d, (560, 1250, 840, 1550), (120, 70, 40))             # кафедра
    rect(d, (0, 1550, W, H), (150, 90, 60), ink=False)
    line(d, [(0, 1550), (W, 1550)])
    for k in range(8):                                        # лави (далі — менші)
        y = 1600 + k ** 1.45 * 70
        h = 40 + k * 14
        rect(d, (40 - k * 30, y, W - 40 + k * 30, y + h), (120, 66, 36))
        rect(d, (40 - k * 30, y + h, W - 40 + k * 30, y + h + 18 + k * 4), shade_c((120, 66, 36), 0.7))
    for x in (120, 520, 920):                                  # промені
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).polygon([(px * S, py * S) for px, py in [(x, 400), (x + 340, 400), (x + 600, 2200), (x + 100, 2200)]], fill=40)
        img.paste(Image.new("RGB", img.size, (255, 240, 200)), (0, 0), m.filter(ImageFilter.GaussianBlur(40)))
    return img, None


# ---------- стіл з листом (вид згори) ----------
def desk():
    W, H = 1400, 2400
    img = canvas(W, H, (150, 92, 48), (128, 76, 40))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 60):
        line(d, [(0, y), (W, y + 30)], w=3, fill=(120, 70, 36))
    poly(d, [(180, 700), (760, 640), (840, 1500), (250, 1560)], (150, 200, 245))      # блакитний аркуш
    poly(d, [(560, 820), (1180, 860), (1130, 1760), (500, 1700)], (250, 170, 200))    # рожевий аркуш
    ell(d, (180, 1720, 380, 1900), (60, 50, 70))                                     # чорнильниця
    ell(d, (210, 1750, 350, 1860), (130, 60, 170))
    return img, None


# ---------- кабінет флоту ----------
def navy_office():
    W, H = 1500, 2500
    img = canvas(W, H, (176, 206, 186), (140, 172, 160))
    d = ImageDraw.Draw(img)
    grain_wall(img, (0, 0, W, 1500), seed=6)
    rect(d, (300, 380, 900, 820), (140, 100, 50))                                    # картина з кораблем
    rect(d, (330, 410, 870, 790), (150, 200, 235))
    rect(d, (330, 650, 870, 790), (60, 110, 170))
    poly(d, [(420, 650), (780, 650), (740, 720), (460, 720)], (90, 90, 100))
    rect(d, (520, 560, 560, 650), (90, 90, 100))
    rect(d, (640, 580, 680, 650), (90, 90, 100))
    ell(d, (1060, 420, 1360, 720), (150, 200, 235))                                  # ілюмінатор
    ell(d, (1060, 420, 1360, 720), None, w=18)
    rect(d, (0, 1500, W, H), (110, 80, 60), ink=False)
    line(d, [(0, 1500), (W, 1500)])
    glow(img, (900, 300, 1500, 1200), (255, 245, 210), 80, 60)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (60, 1620, 900, 1720), (120, 70, 36))                                   # стіл
    rect(fd, (80, 1720, 880, 2200), shade_c((120, 70, 36), 0.75))
    poly(fd, [(1020, 1820), (1300, 1820), (1260, 2200), (1060, 2200)], (120, 124, 130))   # кошик
    for x in range(1060, 1280, 40):
        line(fd, [(x, 1830), (x + 6, 2190)], w=3, fill=(80, 84, 90, 255))
    return img, fg


# ---------- радіорубка ----------
def radio_room():
    W, H = 1500, 2500
    img = canvas(W, H, (120, 140, 170), (90, 104, 130))
    d = ImageDraw.Draw(img)
    for y in range(120, 1500, 300):
        for x in range(60, W, 120):
            ell(d, (x - 8, y - 8, x + 8, y + 8), (150, 166, 190), ink=False)
    rect(d, (80, 300, 760, 1300), (60, 66, 76), r=16)                                # радіошафа
    for i in range(3):
        for j in range(2):
            ell(d, (150 + i * 200, 420 + j * 260, 270 + i * 200, 540 + j * 260), (230, 220, 190))
            line(d, [(210 + i * 200, 480 + j * 260), (250 + i * 200, 440 + j * 260)], w=6)
    rect(d, (140, 1000, 700, 1220), (30, 34, 40), r=10)
    ell(d, (980, 400, 1340, 760), (60, 120, 180))                                    # ілюмінатор з морем
    rect(d, (1000, 600, 1320, 740), (40, 90, 150), ink=False)
    ell(d, (980, 400, 1340, 760), None, w=20)
    rect(d, (0, 1500, W, H), (70, 80, 96), ink=False)
    line(d, [(0, 1500), (W, 1500)])
    glow(img, (100, 900, 900, 1500), (120, 255, 200), 40, 50)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (40, 1620, 1460, 1720), (90, 96, 110))
    rect(fd, (60, 1720, 1440, 2300), shade_c((90, 96, 110), 0.75))
    for i in range(5):                                                               # купа старих навушників
        x, y = 980 + (i % 3) * 110, 1560 - (i // 3) * 60
        fd.arc(B((x - 50, y - 70, x + 50, y + 30)), 190, 350, fill=(30, 30, 34), width=10)
        ell(fd, (x - 66, y - 10, x - 30, y + 30), (90, 90, 96))
        ell(fd, (x + 30, y - 10, x + 66, y + 30), (90, 90, 96))
    return img, fg


# ---------- фабрика ----------
def factory_ext():
    W, H = 1500, 3000
    img = canvas(W, H, (62, 127, 210), (190, 212, 238))
    d = ImageDraw.Draw(img)
    poly(d, [(0, 1500), (300, 1150), (640, 1420), (1000, 1050), (1500, 1380), (1500, 1700), (0, 1700)], (120, 110, 170))
    rect(d, (0, 1650, W, H), (120, 170, 90), ink=False)
    brick = (184, 84, 64)
    rect(d, (120, 1300, 1380, 2300), brick)
    for k in range(5):                                                               # пилоподібний дах
        x = 120 + k * 252
        poly(d, [(x, 1300), (x + 252, 1300), (x + 252, 1140)], shade_c(brick, 0.8))
        poly(d, [(x + 180, 1300), (x + 252, 1300), (x + 252, 1160)], (150, 200, 240), ink=False)
    for x in (260, 1160):
        rect(d, (x, 700, x + 110, 1300), shade_c(brick, 0.9))
        for j in range(4):
            r = 70 + j * 40
            ell(d, (x + 55 - r + j * 50, 600 - j * 160 - r * 0.6, x + 55 + r + j * 50, 600 - j * 160 + r * 0.6),
                (230, 230, 236), ink=False)
    for i in range(6):
        for j in range(3):
            x, y = 190 + i * 200, 1420 + j * 250
            rect(d, (x, y, x + 120, y + 170), (255, 220, 140))
            line(d, [(x + 60, y), (x + 60, y + 170)], w=4)
    rect(d, (640, 2050, 860, 2300), (110, 70, 50))
    for y in range(1340, 2300, 40):
        line(d, [(120, y), (1380, y)], w=2, fill=shade_c(brick, 0.85))
    rect(d, (0, 2300, W, H), (200, 180, 140), ink=False)
    line(d, [(0, 2300), (W, 2300)])
    return img, None


def factory_int():
    W, H = 2600, 2400
    img = canvas(W, H, (200, 170, 130), (150, 120, 96))
    d = ImageDraw.Draw(img)
    for x in range(100, W, 320):
        rect(d, (x, 160, x + 220, 600), (170, 210, 245))
        line(d, [(x + 110, 160), (x + 110, 600)], w=5)
    rect(d, (0, 1100, W, H), (120, 100, 84), ink=False)
    line(d, [(0, 1100), (W, 1100)])
    glow(img, (0, 200, W, 1200), (255, 240, 200), 60, 80)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (0, 1560, W, 1640), (90, 80, 74))                                       # конвеєр
    rect(fd, (0, 1640, W, 1700), (50, 46, 44))
    for x in range(0, W, 120):
        ell(fd, (x, 1650, x + 40, 1690), (120, 110, 100))
    return img, fg


def clock(fd, cx, cy, r, t, speed=12.0):
    ell(fd, (cx - r, cy - r, cx + r, cy + r), (250, 246, 230), w=10)
    for i in range(12):
        a = i * math.pi / 6
        line(fd, [(cx + r * 0.8 * math.sin(a), cy - r * 0.8 * math.cos(a)), (cx + r * 0.92 * math.sin(a), cy - r * 0.92 * math.cos(a))], w=6)
    for L, sp, w in ((0.5, speed / 12, 14), (0.8, speed, 8)):
        a = t * sp
        line(fd, [(cx, cy), (cx + r * L * math.sin(a), cy - r * L * math.cos(a))], w=w)


# ---------- весілля ----------
def wedding():
    W, H = 1500, 2500
    img = canvas(W, H, (120, 180, 235), (200, 225, 245))
    d = ImageDraw.Draw(img)
    rect(d, (0, 1300, W, H), (130, 185, 100), ink=False)
    for x in (100, 1150):
        rect(d, (x, 700, x + 40, 1400), (250, 250, 248))
        rect(d, (x + 210, 700, x + 250, 1400), (250, 250, 248))
        d.arc(B((x, 560, x + 250, 840)), 180, 360, fill=(250, 250, 248), width=40)
        for k in range(8):
            ell(d, (x + k * 30 - 20, 620 + abs(k - 3.5) * 22, x + k * 30 + 20, 660 + abs(k - 3.5) * 22), (240, 140, 170))
    cake = [(560, 940, 940, 1180), (610, 760, 890, 940), (660, 600, 840, 760), (700, 470, 800, 600)]
    for b in cake:
        rect(d, b, (252, 246, 236), r=14)
        line(d, [(b[0] + 10, b[1] + 30), (b[2] - 10, b[1] + 30)], w=8, fill=(240, 150, 180))
    rnd = random.Random(12)
    for row in range(5):                                                             # гості
        y = 1250 + row * 120
        for i in range(12):
            x = 40 + i * 125 + (row % 2) * 60 + rnd.uniform(-20, 20)
            c = rnd.choice([(200, 90, 100), (90, 120, 190), (230, 190, 90), (120, 170, 120), (170, 110, 190)])
            rect(d, (x, y + 50, x + 90, y + 200), c, r=30)
            ell(d, (x + 5, y - 40, x + 85, y + 50), rnd.choice([(240, 200, 165), (214, 168, 128), (244, 214, 186)]))
            ell(d, (x + 28, y, x + 38, y + 14), INK, ink=False)
            ell(d, (x + 52, y, x + 62, y + 14), INK, ink=False)
    return img, None


# ---------- суд ----------
def court():
    W, H = 1600, 2500
    img = canvas(W, H, (150, 96, 60), (110, 66, 40))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 200):
        rect(d, (x + 20, 120, x + 180, 1100), (130, 80, 48), w=4)
    ell(d, (640, 160, 960, 480), (214, 172, 60))
    ell(d, (700, 220, 900, 420), (150, 96, 60))
    rect(d, (430, 1000, 1170, 1450), (100, 56, 30))                                   # суддівський стіл
    rect(d, (430, 1000, 1170, 1060), (130, 80, 48))
    rect(d, (0, 1450, W, H), (90, 56, 40), ink=False)
    line(d, [(0, 1450), (W, 1450)])
    rnd = random.Random(14)
    rect(d, (40, 1180, 420, 1500), (110, 64, 36))                                    # присяжні
    for i in range(6):
        x, y = 70 + (i % 3) * 115, 1040 + (i // 3) * 110
        c = rnd.choice([(200, 90, 100), (90, 120, 190), (230, 190, 90), (120, 170, 120)])
        rect(d, (x, y + 70, x + 90, y + 170), c, r=26)
        ell(d, (x + 5, y - 10, x + 85, y + 75), rnd.choice([(240, 200, 165), (214, 168, 128)]))
        ell(d, (x + 28, y + 24, x + 38, y + 38), INK, ink=False)
        ell(d, (x + 52, y + 24, x + 62, y + 38), INK, ink=False)
    rect(d, (40, 1180, 420, 1500), (110, 64, 36))
    glow(img, (300, 200, 1300, 1300), (255, 220, 150), 70, 70)
    fg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    rect(fd, (1050, 1900, 1560, 2050), (110, 64, 36))                                # лава підсудного
    for x in range(1070, 1560, 70):
        rect(fd, (x, 1700, x + 20, 1900), (110, 64, 36))
    rect(fd, (1050, 1690, 1560, 1720), (130, 80, 48))
    return img, fg


# ---------- багатство / інвестиції ----------
def gold():
    W, H = 1400, 2400
    img = canvas(W, H, (255, 200, 110), (200, 110, 80))
    d = ImageDraw.Draw(img)
    for i in range(24):
        a = i * math.pi / 12
        poly(d, [(700, 1100), (700 + 2000 * math.cos(a), 1100 + 2000 * math.sin(a)),
                 (700 + 2000 * math.cos(a + 0.12), 1100 + 2000 * math.sin(a + 0.12))], (255, 220, 140), ink=False)
    rect(d, (0, 1800, W, H), (170, 80, 60), ink=False)
    for x in range(100, 1300, 160):                                                  # стоси монет
        for k in range(5):
            ell(d, (x, 1800 - k * 30, x + 120, 1850 - k * 30), (240, 196, 70))
    return img, None


def office_chart():
    W, H = 1400, 2400
    img = canvas(W, H, (110, 116, 170), (70, 72, 120))
    d = ImageDraw.Draw(img)
    rect(d, (180, 300, 1220, 1100), (246, 242, 230))
    for x in range(230, 1200, 100):
        line(d, [(x, 340), (x, 1060)], w=2, fill=(200, 200, 210))
    rect(d, (0, 1500, W, H), (70, 60, 80), ink=False)
    line(d, [(0, 1500), (W, 1500)])
    return img, None


SETS = dict(kitchen=kitchen, kitchen_eve=lambda: kitchen(True), town=town, church=church, desk=desk,
            navy=navy_office, radio=radio_room, fext=factory_ext, fint=factory_int, wedding=wedding,
            court=court, gold=gold, chart=office_chart)
