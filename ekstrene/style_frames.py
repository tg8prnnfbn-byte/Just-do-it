#!/usr/bin/env python3
"""Кадри оформлення «Екстрене оповіщення: Полісся, 1987».

Малює ключові екрани серії кодом (без ШІ-картинок) і накладає VHS-ефекти.
Ці самі функції стануть основою для збирання відео.

    python3 ekstrene/style_frames.py   ->  ekstrene/kadry/*.png + doshka.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
CW = 1440                      # картинка 4:3 усередині 16:9
X0 = (W - CW) // 2
OUT = Path(__file__).resolve().parent / "kadry"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

CO_BLUE = (14, 32, 150)
DIRTY_WHITE = (226, 226, 214)
ALERT_RED = (230, 40, 34)
RNG = np.random.default_rng(1987)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def canvas(color=(0, 0, 0)) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (CW, H), color)
    return img, ImageDraw.Draw(img)


def center_text(d, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text(((CW - w) / 2, y), text, font=f, fill=fill)


# ---------- VHS-обробка ----------

def vhs(img: Image.Image, strength: float = 1.0, osd: str | None = "PLAY",
        counter: str = "0:00:00", tracking: bool = True) -> Image.Image:
    """Плівка: розмиття, розходження кольорів, розгортка, шум, трекінг, віньєтка."""
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    a = np.asarray(img).astype(np.float32)
    h, w, _ = a.shape

    # кольори «пливуть»: червоний вправо, синій вліво, і розмиті по горизонталі
    shift = int(4 * strength)
    a[..., 0] = np.roll(a[..., 0], shift, axis=1)
    a[..., 2] = np.roll(a[..., 2], -shift, axis=1)
    k = np.ones(9) / 9
    for c in (0, 2):
        a[..., c] = np.apply_along_axis(lambda r: np.convolve(r, k, mode="same"), 1, a[..., c])

    # легке горизонтальне тремтіння рядків
    jitter = (RNG.normal(0, 0.7 * strength, h)).astype(int)
    for y in np.nonzero(jitter)[0]:
        a[y] = np.roll(a[y], jitter[y], axis=0)

    # смуга трекінгу внизу кадру
    if tracking:
        y0 = int(h * RNG.uniform(0.955, 0.965))
        band = slice(y0, y0 + 26)
        a[band] = np.roll(a[band], int(RNG.uniform(14, 30)), axis=1)
        a[band] = a[band] * 0.55 + 90
        speck = RNG.random((26, w)) > 0.965
        a[band][speck] = 235

    # розгортка
    a[::2] *= 0.8
    # шум
    a += RNG.normal(0, 9 * strength, (h, w, 1))
    # віньєтка
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a *= np.clip(1.15 - 0.42 * r ** 2.2, 0, 1)[..., None]

    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if osd:
        d = ImageDraw.Draw(out)
        f = font(46, bold=False)
        d.text((70, 52), f"{osd} ▶", font=f, fill=(235, 235, 235))
        d.text((CW - 330, 52), counter, font=f, fill=(235, 235, 235))
    return out


def to_169(img: Image.Image) -> Image.Image:
    frame = Image.new("RGB", (W, H), (0, 0, 0))
    frame.paste(img, (X0, 0))
    return frame


# ---------- екрани ----------

def frame_cold_open():
    img, d = canvas()
    center_text(d, 430, "УВАГА.", font(118), DIRTY_WHITE)
    center_text(d, 570, "ЦЕ НЕ НАВЧАННЯ.", font(96), DIRTY_WHITE)
    return vhs(img, counter="0:00:03")


def frame_intro():
    img, d = canvas()
    f = font(40, bold=False)
    lines = ["Плівку знайдено у 2024 році в архіві закритої",
             "ретрансляційної станції «Овруч-3»,",
             "Житомирська обл.", "",
             "Запис оцифровано без змін.",
             "Деякі фрагменти пошкоджені."]
    y = 330
    for ln in lines:
        d.text((150, y), ln, font=f, fill=DIRTY_WHITE)
        y += 60
    d.text((150, y + 60), "КАСЕТА №1", font=font(64), fill=DIRTY_WHITE)
    d.rectangle((150 + d.textlength("КАСЕТА №1", font=font(64)) + 18, y + 72,
                 150 + d.textlength("КАСЕТА №1", font=font(64)) + 50, y + 128), fill=DIRTY_WHITE)
    return vhs(img, osd=None, strength=0.7, tracking=False)


def frame_news_card(date="14.10.87", dark=False):
    """Заставка програми «Вісті Полісся» з кольоровими смугами."""
    img, d = canvas((8, 8, 12))
    bars = [(192, 192, 192), (192, 192, 0), (0, 192, 192), (0, 192, 0),
            (192, 0, 192), (192, 0, 0), (0, 0, 192)]
    bh = 230
    for i, c in enumerate(bars):
        if dark:
            c = tuple(int(v * 0.35) for v in c)
        d.rectangle((i * CW // 7, 0, (i + 1) * CW // 7, bh), fill=c)
    blue = (20, 40, 120) if not dark else (8, 14, 40)
    d.rectangle((0, bh, CW, H), fill=blue)
    # емблема: коло з хвилями (антена)
    cx, cy = CW // 2, 520
    ring = DIRTY_WHITE if not dark else (120, 120, 115)
    d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), outline=ring, width=10)
    for r in (40, 75):
        d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=ring, width=8)
    d.line((cx, cy - 10, cx, cy + 90), fill=ring, width=10)
    center_text(d, 690, "ВІСТІ ПОЛІССЯ", font(100), ring)
    center_text(d, 820, "ОВРУЦЬКЕ РАЙОННЕ ТЕЛЕБАЧЕННЯ", font(34, bold=False), ring)
    # плашка дати
    d.rectangle((0, H - 120, 420, H - 50), fill=(200, 30, 30) if not dark else (70, 12, 12))
    d.text((40, H - 112), date, font=font(54), fill=(255, 255, 255) if not dark else (150, 150, 150))
    return vhs(img, counter="0:00:31" if not dark else "-:--:--", strength=1.0 if not dark else 1.4)


def frame_alert(n: int):
    """Синій екран цивільної оборони. n=1 — біле, n=2 — червоне."""
    img, d = canvas(CO_BLUE)
    color = DIRTY_WHITE if n == 1 else ALERT_RED
    d.rectangle((0, 130, CW, 250), fill=color)
    center_text(d, 157, "ШТАБ ЦО ОВРУЦЬКОГО Р-НУ", font(62), CO_BLUE)
    d.text((CW - 300, H - 175), "02:14" if n == 1 else "03:40", font=font(70), fill=color)
    d.text((110, H - 165), "ОПОВІЩЕННЯ №%d" % n, font=font(48), fill=color)
    f = font(44)
    if n == 1:
        rows = ["1. ЗАЛИШАЙТЕСЯ ВДОМА", "   ВІД ЗАХОДУ ДО СВІТАНКУ.",
                "2. ЗАВІСЬТЕ ВІКНА,", "   ЩО ВИХОДЯТЬ НА ЛІС.",
                "3. НЕ ВІДПОВІДАЙТЕ ГОЛОСАМ", "   З БОКУ ЛІСУ.",
                "   ПЕРЕРАХУЙТЕ РІДНИХ.",
                "4. НЕ ВІДЧИНЯЙТЕ ТИМ,", "   ХТО СТУКАЄ ТРИЧІ."]
    else:
        rows = ["ПОПЕРЕДНЄ ОПОВІЩЕННЯ", "НЕ ПЕРЕДАВАЛОСЯ НАШИМ ШТАБОМ.", "",
                "1. ЗНІМІТЬ ЗАВІСИ.", "   ВИ ПОВИННІ БАЧИТИ ЛІС.",
                "2. ВІДПОВІДАЙТЕ, КОЛИ КЛИЧУТЬ.",
                "3. ПРАЦІВНИКИ ШТАБУ", "   СТУКАЮТЬ ТРИЧІ.",
                "4. НЕ ПЕРЕРАХОВУЙТЕ РІДНИХ."]
    y = 295
    for r in rows:
        d.text((110, y), r, font=f, fill=color)
        y += 62
    return vhs(img, counter="0:01:42" if n == 1 else "0:05:07", strength=1.0 if n == 1 else 1.3)


def frame_tape():
    """Аудіозапис: панель з осцилограмою і підписом."""
    img, d = canvas((10, 10, 9))
    f = font(36, bold=False)
    d.text((110, 150), "АУДІОЗАПИС · 17.10.1987", font=font(48), fill=DIRTY_WHITE)
    d.text((110, 230), "Розмова дільничного інспектора П. Гнатюка", font=f, fill=(170, 170, 160))
    d.text((110, 280), "з мешканкою с. Вовчий Брід Г. Ковальчук, 79 р.", font=f, fill=(170, 170, 160))
    # бобіни
    for cx in (CW // 2 - 260, CW // 2 + 260):
        cy = 480
        d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), outline=(120, 120, 112), width=6)
        d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=(120, 120, 112))
        for ang in (0, 120, 240):
            t = np.deg2rad(ang)
            d.line((cx, cy, cx + 100 * np.cos(t), cy + 100 * np.sin(t)), fill=(120, 120, 112), width=5)
    d.line((CW // 2 - 260, 600, CW // 2 + 260, 600), fill=(90, 70, 50), width=4)
    # осцилограма
    top, bot = 700, 930
    d.rectangle((110, top, CW - 110, bot), outline=(60, 60, 56), width=2)
    mid = (top + bot) // 2
    xs = np.arange(110, CW - 110)
    env = np.abs(np.sin(xs / 37)) * np.abs(np.sin(xs / 211)) + 0.08
    env[xs > CW * 0.72] = 0.02                        # голос обірвався
    ys = mid + (RNG.normal(0, 1, xs.size) * env * 90)
    d.line(list(zip(xs, ys)), fill=(190, 220, 170), width=2)
    d.text((CW - 330, bot + 20), "■ ЗАПИС", font=font(34), fill=ALERT_RED)
    return vhs(img, osd=None, strength=0.9)


def frame_forest():
    """Узлісся вночі, між деревами ледь видна світла постать."""
    img = Image.new("RGB", (CW, H))
    a = np.zeros((H, CW, 3), np.float32)
    g = np.linspace(0, 1, H)[:, None]
    a[...] = (np.array([22, 26, 30]) * (1 - g) + np.array([8, 9, 10]) * g)[..., None].transpose(0, 2, 1)
    img = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(img)

    def spruce(d, x, top, base_w, shade):
        """Ялина/сосна: тонкий стовбур і ярусні трикутники."""
        hgt = base - top
        d.rectangle((x - base_w * 0.05, top + hgt * 0.2, x + base_w * 0.05, H), fill=(shade,) * 3)
        tiers = 7
        for t in range(tiers):
            ty = top + hgt * 0.72 * t / tiers
            tw = base_w * (0.25 + 0.75 * t / tiers) * RNG.uniform(0.8, 1.1)
            d.polygon([(x, ty), (x - tw / 2, ty + hgt * 0.2), (x + tw / 2, ty + hgt * 0.2)], fill=(shade,) * 3)

    # дальній шар у тумані
    for layer, (shade, count, base, scale) in enumerate([(34, 40, 700, 0.6), (20, 26, 760, 1.0)]):
        for _ in range(count):
            x = RNG.uniform(-40, CW + 40)
            top = RNG.uniform(170, 330) - layer * 80
            spruce(d, x, top, RNG.uniform(70, 120) * scale, shade)
        d.rectangle((0, base, CW, H), fill=(shade,) * 3)
        fog = Image.new("L", (CW, H), 0)
        ImageDraw.Draw(fog).rectangle((0, base - 200, CW, base + 30), fill=60 - layer * 20)
        fog = fog.filter(ImageFilter.GaussianBlur(60))
        img.paste(Image.new("RGB", (CW, H), (76, 80, 84)), (0, 0), fog)
        d = ImageDraw.Draw(img)

    # постать між деревами: висока, худа, розмита, без деталей
    ghost = Image.new("L", (CW, H), 0)
    gd = ImageDraw.Draw(ghost)
    gx, gy = int(CW * 0.6), 700
    gd.ellipse((gx - 17, gy - 300, gx + 17, gy - 255), fill=150)
    gd.polygon([(gx - 22, gy - 255), (gx + 22, gy - 255), (gx + 30, gy - 20), (gx - 30, gy - 20)], fill=120)
    gd.line((gx - 22, gy - 245, gx - 40, gy - 60), fill=110, width=9)
    gd.line((gx + 22, gy - 245, gx + 40, gy - 60), fill=110, width=9)
    ghost = ghost.filter(ImageFilter.GaussianBlur(6))
    img.paste(Image.new("RGB", (CW, H), (178, 180, 172)), (0, 0), ghost)
    d = ImageDraw.Draw(img)

    # ближній чорний шар, з просвітом там, де стоїть постать
    base = 860
    for _ in range(14):
        x = RNG.uniform(-40, CW + 40)
        if abs(x - gx) < 110:
            continue
        spruce(d, x, RNG.uniform(-60, 120), RNG.uniform(170, 260), 4)
    d.rectangle((0, base, CW, H), fill=(4, 4, 4))
    return vhs(img, counter="0:06:02", strength=1.5)


def frame_final():
    img, d = canvas()
    center_text(d, 420, "ОПОВІЩЕННЯ ДЛЯ ТИХ,", font(78), DIRTY_WHITE)
    center_text(d, 530, "ХТО ЗНАЙШОВ ЦЕЙ ЗАПИС", font(78), DIRTY_WHITE)
    return vhs(img, counter="0:07:15", strength=0.8, tracking=False)


def thumbnail():
    """Обкладинка 1280x720."""
    img = Image.new("RGB", (CW, H), CO_BLUE)
    d = ImageDraw.Draw(img)
    forest = frame_forest().crop((0, 330, CW, 880)).resize((CW, 440))
    img.paste(forest, (0, H - 440))
    f = font(150)
    for i, t in enumerate(["НЕ", "ВІДПОВІДАЙТЕ"]):
        w = d.textlength(t, font=f)
        d.text(((CW - w) / 2 + 6, 110 + i * 170 + 6), t, font=f, fill=(0, 0, 40))
        d.text(((CW - w) / 2, 110 + i * 170), t, font=f, fill=DIRTY_WHITE)
    d.rectangle((60, 40, 470, 100), fill=ALERT_RED)
    d.text((80, 44), "КАСЕТА №1", font=font(46), fill=(255, 255, 255))
    out = vhs(img, osd=None, strength=0.8, tracking=False)
    full = Image.new("RGB", (W, H), CO_BLUE)
    full.paste(out.resize((W, H)), (0, 0))
    return full.resize((1280, 720))


def main():
    OUT.mkdir(exist_ok=True)
    frames = [
        ("01-vidkryt", frame_cold_open()),
        ("02-zastavka", frame_intro()),
        ("03-visti-polissia", frame_news_card()),
        ("04-opovishchennia-1", frame_alert(1)),
        ("05-audiozapys", frame_tape()),
        ("06-opovishchennia-2", frame_alert(2)),
        ("07-lis", frame_forest()),
        ("08-efir-bez-daty", frame_news_card("--.--.--", dark=True)),
        ("09-final", frame_final()),
    ]
    for name, f in frames:
        to_169(f).save(OUT / f"{name}.png")
    thumbnail().save(OUT / "obkladynka.png")

    # дошка 3x3 для швидкого перегляду
    tw, th = 640, 360
    board = Image.new("RGB", (tw * 3 + 40, th * 3 + 40), (20, 20, 20))
    for i, (_, f) in enumerate(frames):
        board.paste(to_169(f).resize((tw, th)), (10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 10)))
    board.save(OUT / "doshka.png")
    print("Готово:", OUT)


if __name__ == "__main__":
    main()
