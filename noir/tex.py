"""Мальовані текстури для ретро-нуару «Нью-Йорк 1950-х»: фасади з вікнами, пожежними драбинами, театральним
козирком з лампочками й неоном, мокра бруківка з відблисками, тротуари, небо з силуетами хмарочосів,
ліхтарі й машини (спрайти). Усе генерується кодом, PPM — пікселів на метр."""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PPM = 36
INK = (16, 14, 18)
AMBER = (255, 196, 110)
WARM = (255, 170, 80)
FOG = (120, 108, 120)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def paint_noise(img, amp=0.07, seed=0):
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    rnd = np.random.default_rng(seed)
    tex = np.zeros((h, w), np.float32)
    for sc, k in ((6, 1.0), (24, 0.7), (80, 0.4)):
        small = rnd.standard_normal((h // sc + 2, w // sc + 2)).astype(np.float32)
        tex += k * np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC))
    a[..., :3] *= (1 + amp * tex / 1.6)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), img.mode)


def glow_layer(img, pts, color, r, alpha=120):
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    for x, y in pts:
        d.ellipse((x - r, y - r, x + r, y + r), fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.8))
    img.paste(Image.new(img.mode, img.size, color + ((255,) if img.mode == "RGBA" else ())), (0, 0), m)


# ---------- фасади ----------
def facade(length_m=140, height_m=42, seed=1, side="left"):
    rnd = random.Random(seed)
    W, H = int(length_m * PPM), int(height_m * PPM)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lights = []
    x = 0
    theater_done = False
    while x < W:
        bw = int(rnd.uniform(9, 17) * PPM)
        bh = int(rnd.uniform(18, 38) * PPM)
        top = H - bh
        col = rnd.choice([(128, 66, 54), (150, 92, 70), (112, 88, 82), (160, 128, 100), (96, 70, 70)])
        d.rectangle((x, top, x + bw, H), fill=col, outline=INK, width=3)
        d.rectangle((x, top, x + bw, top + 18), fill=tuple(int(c * 0.7) for c in col), outline=INK, width=2)   # карниз
        for yy in range(top + 30, H - 4 * PPM, 10):                                                           # цегляні ряди
            d.line((x + 2, yy, x + bw - 2, yy), fill=tuple(int(c * 0.88) for c in col), width=1)
        # вікна
        cols = max(2, bw // int(2.6 * PPM))
        rows = max(3, (bh - 6 * PPM) // int(3.3 * PPM))
        ww, wh = int(1.2 * PPM), int(1.9 * PPM)
        for r in range(rows):
            for c in range(cols):
                wx = x + int((c + 0.5) * bw / cols) - ww // 2
                wy = top + int(1.6 * PPM) + r * int(3.3 * PPM)
                lit = rnd.random() < 0.38
                fill = (AMBER if rnd.random() < 0.7 else (255, 220, 160)) if lit else (40, 44, 64)
                d.rectangle((wx, wy, wx + ww, wy + wh), fill=fill, outline=INK, width=2)
                d.line((wx, wy + wh // 2, wx + ww, wy + wh // 2), fill=INK, width=2)
                if lit:
                    lights.append((wx + ww // 2, wy + wh // 2))
                d.rectangle((wx - 4, wy + wh, wx + ww + 4, wy + wh + 6), fill=(200, 190, 170), outline=INK, width=1)
        # пожежна драбина
        if rnd.random() < 0.55 and rows > 3:
            fx = x + int(bw * rnd.uniform(0.2, 0.5))
            fw = int(3.4 * PPM)
            for r in range(1, rows):
                fy = top + int(1.6 * PPM) + r * int(3.3 * PPM) + wh + 4
                d.rectangle((fx, fy - 4, fx + fw, fy), fill=INK)
                d.line((fx, fy - 28, fx + fw, fy - 28), fill=INK, width=2)
                for k in range(0, fw, 10):
                    d.line((fx + k, fy - 28, fx + k, fy), fill=INK, width=1)
                d.line((fx + 8, fy, fx + fw - 8, fy + int(3.3 * PPM) - 30), fill=INK, width=3)
        # перший поверх: вітрини, маркізи, театр
        gy = H - int(4.4 * PPM)
        if not theater_done and x > 30 * PPM and rnd.random() < 0.5:
            theater_done = True
            d.rectangle((x + 10, gy - 30, x + bw - 10, gy + 40), fill=(60, 30, 34), outline=INK, width=3)     # козирок
            for k in range(x + 20, x + bw - 20, 14):
                for yy in (gy - 22, gy + 32):
                    d.ellipse((k - 4, yy - 4, k + 4, yy + 4), fill=(255, 236, 170))
                    lights.append((k, yy))
            f = ImageFont.truetype(SERIF, 46)
            d.text((x + bw // 2 - d.textlength("PALACE", font=f) // 2, gy - 18), "PALACE", font=f, fill=(255, 210, 140))
            bx = x + bw // 2 - 30                                                                             # вертикальна вивіска
            d.rectangle((bx, top + 80, bx + 60, gy - 40), fill=(150, 30, 40), outline=INK, width=3)
            f2 = ImageFont.truetype(BOLD, 44)
            for i, ch in enumerate("THEATRE"):
                d.text((bx + 14, top + 100 + i * 58), ch, font=f2, fill=(255, 140, 150))
                lights.append((bx + 30, top + 120 + i * 58))
            d.rectangle((x + 30, gy + 40, x + bw - 30, H), fill=(240, 200, 120), outline=INK, width=3)
        else:
            d.rectangle((x + 6, gy, x + bw - 6, H), fill=(54, 40, 44), outline=INK, width=3)
            for k in range(3):
                sx0 = x + 14 + k * (bw - 28) // 3
                sx1 = sx0 + (bw - 28) // 3 - 10
                lit = rnd.random() < 0.7
                d.rectangle((sx0, gy + 50, sx1, H - 10), fill=(255, 200, 120) if lit else (50, 54, 70), outline=INK, width=2)
                if lit:
                    lights.append(((sx0 + sx1) // 2, gy + 90))
            aw = rnd.choice([(170, 40, 40), (40, 90, 80), (190, 150, 60)])                                    # маркіза
            for k in range(x + 6, x + bw - 6, 24):
                d.polygon([(k, gy - 10), (k + 24, gy - 10), (k + 30, gy + 46), (k + 6, gy + 46)],
                          fill=aw if (k // 24) % 2 else (230, 220, 200), outline=INK)
            if rnd.random() < 0.6:                                                                            # неонова вивіска
                word = rnd.choice(["DINER", "HOTEL", "BAR", "JAZZ", "CAFE", "DRUGS", "RADIO", "SHOES"])
                f = ImageFont.truetype(BOLD, 54)
                tw = d.textlength(word, font=f)
                nx, ny = x + bw // 2 - tw // 2, gy - 120
                ncol = rnd.choice([(255, 90, 120), (120, 220, 255), (255, 170, 60), (180, 255, 140)])
                d.rectangle((nx - 14, ny - 8, nx + tw + 14, ny + 66), fill=(30, 24, 30), outline=INK, width=3)
                d.text((nx, ny), word, font=f, fill=ncol)
                lights.append((nx + tw // 2, ny + 30))
        # рекламний щит на даху
        if rnd.random() < 0.3:
            bx0, bx1 = x + bw // 6, x + bw * 5 // 6
            d.rectangle((bx0, top - 6 * PPM, bx1, top - 30), fill=(230, 210, 170), outline=INK, width=4)
            d.ellipse((bx0 + 20, top - 6 * PPM + 20, bx0 + 20 + 3 * PPM, top - 50), fill=(220, 150, 120), outline=INK, width=3)
            f = ImageFont.truetype(SERIF, 64)
            d.text((bx0 + 3.6 * PPM, top - 4.6 * PPM), rnd.choice(["COLA", "SMOKE", "RADIO"]), font=f, fill=(150, 40, 40))
            for k in range(bx0 + 30, bx1, 80):
                d.line((k, top - 30, k, top), fill=INK, width=4)
        x += bw
    img = paint_noise(img, 0.06, seed)
    glow_layer(img, lights[::2], (255, 190, 110), 26, 70)
    if side == "right":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# ---------- вулиця ----------
def street(width_m=12, length_m=140, seed=3):
    W, H = int(width_m * PPM), int(length_m * PPM)          # H — уздовж вулиці (0 = близько)
    img = Image.new("RGB", (W, H), (44, 46, 58))
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(1600):                                    # бруківка
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        s = rnd.uniform(10, 18)
        c = rnd.randint(40, 62)
        d.rounded_rectangle((x, y, x + s * 1.4, y + s), radius=4, fill=(c, c + 2, c + 14))
    for y in range(0, H, 120):                               # розмітка
        d.rectangle((W // 2 - 5, y, W // 2 + 5, y + 60), fill=(200, 170, 80))
    for k in range(10):                                      # пішохідний перехід
        d.rectangle((20 + k * (W - 40) // 10, 24 * PPM, 20 + k * (W - 40) // 10 + 24, 27 * PPM), fill=(190, 186, 176))
    a = np.asarray(img).astype(np.float32)                    # мокрі відблиски: теплі смуги від ліхтарів і вітрин
    xs = np.arange(W)[None, :]
    ys = np.arange(H)[:, None]
    for z in range(5, int(length_m), 12):
        for xr in (0.08, 0.92):
            cx = xr * W
            band = np.exp(-((xs - cx) / (W * 0.05)) ** 2) * np.exp(-((ys - z * PPM) / (PPM * 6)) ** 2)
            a += band[..., None] * np.array([170, 120, 60])
    for _ in range(40):                                      # калюжі
        px, py = rnd.uniform(0, W), rnd.uniform(0, H)
        band = np.exp(-(((xs - px) / 40) ** 2 + ((ys - py) / 70) ** 2))
        a += band[..., None] * np.array([40, 40, 60])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return paint_noise(img, 0.08, seed)


def sidewalk(width_m=3.5, length_m=140, seed=4):
    W, H = int(width_m * PPM), int(length_m * PPM)
    img = Image.new("RGB", (W, H), (96, 92, 98))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 50):
        d.line((0, y, W, y), fill=(70, 68, 76), width=2)
    d.line((W // 2, 0, W // 2, H), fill=(70, 68, 76), width=2)
    d.rectangle((0, 0, 10, H), fill=(140, 134, 130))
    return paint_noise(img, 0.08, seed)


def sky():
    W, H = 2400, 1500
    g = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([70, 62, 92]), np.array([214, 150, 120])
    a = top * (1 - g) + bot * g
    img = Image.fromarray(np.broadcast_to(a, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    x = 0
    while x < W:                                             # силуети хмарочосів у димці
        bw = rnd.randint(60, 160)
        bh = rnd.randint(300, 1000)
        col = (110, 96, 116)
        d.rectangle((x, H - bh, x + bw, H), fill=col)
        if rnd.random() < 0.25:
            d.polygon([(x + bw * 0.3, H - bh), (x + bw * 0.5, H - bh - 160), (x + bw * 0.7, H - bh)], fill=col)
        for _ in range(int(bh * bw / 2500)):
            wx, wy = x + rnd.uniform(6, bw - 6), H - rnd.uniform(10, bh - 10)
            if rnd.random() < 0.4:
                d.rectangle((wx, wy, wx + 4, wy + 6), fill=(240, 190, 120))
        x += bw + rnd.randint(-20, 10)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    return paint_noise(img, 0.05, 7)


# ---------- спрайти ----------
def lamp():
    W, H = 160, 1600                                         # 4.4 м
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((W // 2 - 8, 160, W // 2 + 8, H), fill=(30, 32, 36), outline=INK)
    d.rectangle((W // 2 - 22, H - 80, W // 2 + 22, H), fill=(30, 32, 36), outline=INK)
    d.polygon([(W // 2 - 50, 150), (W // 2 + 50, 150), (W // 2 + 30, 60), (W // 2 - 30, 60)], fill=(255, 220, 150), outline=INK)
    d.polygon([(W // 2 - 60, 60), (W // 2 + 60, 60), (W // 2, 10)], fill=(30, 32, 36), outline=INK)
    glow_layer(img, [(W // 2, 110)], (255, 210, 140), 70, 160)
    return img


def car(kind="taxi", view="front"):
    """Машини 1950-х: таксі (жовте) і седан (бордовий), вид спереду або збоку."""
    col = (232, 184, 40) if kind == "taxi" else (120, 30, 36)
    if view == "front":
        W, H = 760, 560
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((40, 200, W - 40, 470), radius=70, fill=col, outline=INK, width=6)
        d.rounded_rectangle((150, 60, W - 150, 230), radius=60, fill=col, outline=INK, width=6)
        d.rounded_rectangle((180, 90, W - 180, 210), radius=30, fill=(70, 80, 110), outline=INK, width=4)
        d.rectangle((150, 330, W - 150, 420), fill=(200, 200, 205), outline=INK, width=4)        # хромована решітка
        for k in range(170, W - 160, 30):
            d.line((k, 335, k, 415), fill=(120, 120, 130), width=4)
        for cx in (110, W - 110):
            d.ellipse((cx - 50, 260, cx + 50, 360), fill=(255, 240, 190), outline=INK, width=5)
        d.rectangle((60, 440, W - 60, 480), fill=(210, 210, 215), outline=INK, width=4)
        for cx in (130, W - 130):
            d.rectangle((cx - 50, 470, cx + 50, 550), fill=(20, 20, 24))
        if kind == "taxi":
            d.rectangle((W // 2 - 60, 30, W // 2 + 60, 70), fill=(250, 240, 200), outline=INK, width=3)
        glow_layer(img, [(110, 310), (W - 110, 310)], (255, 230, 170), 60, 120)
    else:
        W, H = 1400, 520
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((20, 220, W - 20, 430), radius=90, fill=col, outline=INK, width=6)
        d.rounded_rectangle((330, 70, W - 380, 260), radius=80, fill=col, outline=INK, width=6)
        for x0 in (370, 690):
            d.rounded_rectangle((x0, 100, x0 + 280, 230), radius=30, fill=(70, 80, 110), outline=INK, width=4)
        d.rectangle((40, 330, W - 40, 350), fill=(210, 210, 215))
        for cx in (290, W - 290):
            d.ellipse((cx - 100, 340, cx + 100, 520), fill=(20, 20, 24), outline=INK, width=5)
            d.ellipse((cx - 45, 385, cx + 45, 475), fill=(200, 200, 205))
        if kind == "taxi":
            d.rectangle((640, 40, 760, 80), fill=(250, 240, 200), outline=INK, width=3)
            for k in range(500, 900, 40):
                d.rectangle((k, 360, k + 20, 380), fill=INK if (k // 40) % 2 else (250, 250, 250))
    return paint_noise(img, 0.05, 11)
