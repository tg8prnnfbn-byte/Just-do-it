#!/usr/bin/env python3
"""Проба v2 (~37 с): швидкий темп, оповідач веде історію, субтитри, поворот.

Сюжет проби:
  оповіщення «не відповідай голосам з лісу» → оповідач прокидається о третій,
  його кличе покійна бабуся, голос щоразу ближче → червоний екран: «попереднє
  оповіщення НЕ передавалося» → «вчора я знову почув своє ім'я. З кухні» →
  три стуки → «А ти б відповів?»

    python3 ekstrene/proba2.py /шлях/до/ne-vidpovidai-elevenlabs.mp3 ekstrene/proba-kaseta-1-v2.mp4
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import style_frames as sf  # noqa: E402
from proba import (FPS, SR, bandpass, build_forest_layers, knock, load_mp3,  # noqa: E402
                   snow, text_screen, vhs_fast, alert_screen)

RNG = np.random.default_rng(11)

# Фрази з ne-vidpovidai-elevenlabs.mp3: (початок, кінець) у вихідному файлі
SRC = {
    "rule":    (4.38, 8.30),    # Якщо вночі з лісу тебе кличуть на ім'я — не відповідай.
    "woke":    (26.88, 28.98),  # Я прокинувся близько третьої ночі.
    "called":  (29.46, 33.55),  # За вікном хтось тихо, дуже спокійно кликав мене на ім'я.
    "knew":    (34.55, 36.42),  # Я впізнав цей голос одразу.
    "grandma": (36.83, 37.93),  # Це була бабуся.
    "buried":  (38.28, 40.42),  # Яку ми поховали два роки тому.
    "thrice":  (41.36, 42.66),  # Вона кликала тричі.
    "closer":  (43.02, 45.78),  # І з кожним разом голос лунав ближче до хати.
    "kyiv":    (64.42, 68.55),  # Бо вчора, у своїй квартирі в Києві, я знову почув своє ім'я.
    "kitchen": (69.02, 70.74),  # Цього разу — з кухні.
    "you":     (71.68, 73.20),  # А ти б відповів?
}
TEXT = {
    "rule": "Якщо вночі з лісу тебе кличуть на ім'я — не відповідай.",
    "woke": "Я прокинувся близько третьої ночі.",
    "called": "За вікном хтось тихо, дуже спокійно кликав мене на ім'я.",
    "knew": "Я впізнав цей голос одразу.",
    "grandma": "Це була бабуся.",
    "buried": "Яку ми поховали два роки тому.",
    "thrice": "Вона кликала тричі.",
    "closer": "І з кожним разом голос лунав ближче до хати.",
    "kyiv": "Бо вчора, у своїй квартирі в Києві, я знову почув своє ім'я.",
    "kitchen": "Цього разу — з кухні.",
    "you": "А ти б відповів?",
}
# коли кожна фраза звучить у пробі
AT = {"rule": 1.7, "woke": 6.0, "called": 8.25, "knew": 12.55, "grandma": 14.6, "buried": 15.9,
      "thrice": 18.3, "closer": 19.85, "kyiv": 25.6, "kitchen": 29.95, "you": 33.5}
RADIO = {"rule"}

# сцени: (початок, назва)
SCENES = [(0.0, "alert"), (1.5, "co1"), (5.55, "snow"), (5.85, "window"),
          (22.75, "co2"), (25.35, "door"), (34.9, "end")]
KNOCKS = (31.95, 32.37, 32.79)
HITS = (18.35, 18.85, 19.35)   # «тричі»: постать стрибає ближче з кожним ударом
DUR = 37.6


def scene_at(t):
    name, start = SCENES[0][1], 0.0
    for s, n in SCENES:
        if t >= s:
            name, start = n, s
    return name, start


def phrase_end(k):
    return AT[k] + SRC[k][1] - SRC[k][0]


# ---------- картинки ----------

def ghost(img, gx, gy, s, v):
    g = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(g)
    d.ellipse((gx - 17 * s, gy - 300 * s, gx + 17 * s, gy - 255 * s), fill=v)
    d.polygon([(gx - 22 * s, gy - 255 * s), (gx + 22 * s, gy - 255 * s),
               (gx + 30 * s, gy - 20 * s), (gx - 30 * s, gy - 20 * s)], fill=int(v * 0.8))
    d.line((gx - 22 * s, gy - 245 * s, gx - 36 * s, gy - 40 * s), fill=int(v * 0.7), width=max(6, int(8 * s)))
    d.line((gx + 22 * s, gy - 245 * s, gx + 36 * s, gy - 40 * s), fill=int(v * 0.7), width=max(6, int(8 * s)))
    img.paste(Image.new("RGB", img.size, (182, 184, 176)), (0, 0), g.filter(ImageFilter.GaussianBlur(5 + 2 * s)))


def build_window():
    """Темна кімната зсередини: стіна, рама з хрестовиною, прозорі шибки."""
    m = Image.new("L", (sf.CW, sf.H), 255)
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = 330, 150, 1110, 900
    d.rectangle((x0, y0, x1, y1), fill=0)
    mask = m
    wall = Image.new("RGBA", (sf.CW, sf.H), (9, 9, 11, 255))
    wd = ImageDraw.Draw(wall)
    wd.rectangle((x0, y0, x1, y1), fill=(0, 0, 0, 0))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2 - 60
    wd.rectangle((cx - 14, y0, cx + 14, y1), fill=(14, 13, 12, 255))
    wd.rectangle((x0, cy - 14, x1, cy + 14), fill=(14, 13, 12, 255))
    wd.rectangle((x0 - 30, y0 - 30, x1 + 30, y0), fill=(16, 15, 14, 255))
    wd.rectangle((x0 - 30, y1, x1 + 30, y1 + 40), fill=(20, 18, 16, 255))
    wd.rectangle((x0 - 30, y0, x0, y1), fill=(16, 15, 14, 255))
    wd.rectangle((x1, y0, x1 + 30, y1), fill=(16, 15, 14, 255))
    # фіранка зліва, ледь видна
    wd.polygon([(x0, y0), (x0 + 150, y0), (x0 + 90, y1), (x0, y1)], fill=(22, 22, 26, 200))
    return wall, mask


def build_door():
    """Квартира: темний коридор, прочинені двері на кухню, смужка світла."""
    img = Image.new("RGB", (sf.CW, sf.H), (7, 7, 8))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 920), (sf.CW, 920), (sf.CW, sf.H), (0, sf.H)], fill=(11, 11, 12))
    dx0, dx1, dy0 = 560, 900, 170
    d.rectangle((dx0 - 24, dy0 - 24, dx1 + 24, 920), fill=(15, 15, 16))
    d.rectangle((dx0, dy0, dx1, 920), fill=(4, 4, 5))
    glow = Image.new("L", (sf.CW, sf.H), 0)
    gd = ImageDraw.Draw(glow)
    gd.rectangle((dx1 - 46, dy0 + 6, dx1 - 30, 914), fill=200)
    gd.polygon([(dx1 - 46, 920), (dx1 - 30, 920), (dx1 + 160, sf.H), (dx1 - 120, sf.H)], fill=60)
    img.paste(Image.new("RGB", img.size, (150, 140, 110)), (0, 0), glow.filter(ImageFilter.GaussianBlur(6)))
    return img


def co2_screen():
    img, d = sf.canvas(sf.CO_BLUE)
    red = sf.ALERT_RED
    d.rectangle((0, 130, sf.CW, 250), fill=red)
    sf.center_text(d, 157, "ШТАБ ЦО ОВРУЦЬКОГО Р-НУ", sf.font(62), sf.CO_BLUE)
    for i, ln in enumerate(["ПОПЕРЕДНЄ", "ОПОВІЩЕННЯ", "НЕ ПЕРЕДАВАЛОСЯ", "НАШИМ ШТАБОМ."]):
        sf.center_text(d, 360 + i * 110, ln, sf.font(84), red)
    d.text((110, sf.H - 165), "ОПОВІЩЕННЯ №2", font=sf.font(48), fill=red)
    d.text((sf.CW - 300, sf.H - 175), "03:40", font=sf.font(70), fill=red)
    return img


def subtitle(img, text):
    """Субтитри: білі з чорним обведенням, над смугою трекінгу, до 2 рядків."""
    d = ImageDraw.Draw(img)
    f = sf.font(50)
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) > sf.CW - 220:
            lines.append(cur)
            cur = w
        else:
            cur = test
    lines.append(cur)
    y = sf.H - 120 - 66 * len(lines)
    for ln in lines:
        x = (sf.CW - d.textlength(ln, font=f)) / 2
        d.text((x, y), ln, font=f, fill=(245, 242, 225), stroke_width=5, stroke_fill=(0, 0, 0))
        y += 66
    return img


def current_sub(t):
    for k, at in AT.items():
        if at - 0.05 <= t <= phrase_end(k) + 0.25:
            return TEXT[k]
    return None


def counter(t):
    return f"0:{int(t // 60):02d}:{int(t % 60):02d}"


def render_video(path: Path):
    alert_txt = text_screen(["УВАГА.", "ЦЕ НЕ НАВЧАННЯ."], 112)
    end = text_screen(["КАСЕТА №1", "", "НЕЗАБАРОМ"], 72)
    black = sf.canvas()[0]
    back, front = build_forest_layers()
    wall, _ = build_window()
    door = build_door()
    co1 = {k: alert_screen(4, k) for k in (False, True)}
    co2 = co2_screen()

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{sf.W}x{sf.H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        t = i / FPS
        name, start = scene_at(t)
        strength, osd = 1.0, True
        if name == "alert":
            img = alert_txt.copy() if (t * 6) % 2 < 1.4 else black.copy()   # блимає
        elif name == "co1":
            img = co1[t >= AT["rule"] + 1.6].copy()
        elif name == "snow":
            img, strength, osd = snow(), 1.6, False
        elif name == "window":
            # постать: з'являється на «Це була бабуся», стрибає ближче на «тричі», впритул на «ближче до хати»
            img = back.copy()
            if t >= AT["grandma"]:
                step = sum(t >= h for h in HITS)
                s = [0.55, 0.8, 1.15, 1.6][step]
                if t >= AT["closer"] + 1.4:
                    s = 1.6 + 1.1 * min(1, (t - AT["closer"] - 1.4) / 1.2)
                flick = 150 if RNG.random() > 0.05 else 60
                ghost(img, int(sf.CW * 0.58), int(560 + 220 * (s - 0.55)), s, flick)
            img.paste(front, (0, 0), front)
            # повільний наїзд камери на вікно
            z = 1 + 0.06 * (t - start) / (22.75 - start)
            w, h = int(sf.CW / z), int(sf.H / z)
            img.paste(wall, (0, 0), wall)
            img = img.crop(((sf.CW - w) // 2, (sf.H - h) // 2, (sf.CW + w) // 2, (sf.H + h) // 2)).resize((sf.CW, sf.H))
            strength = 1.3 + (0.5 if any(0 <= t - hh < 0.12 for hh in HITS) else 0)
        elif name == "co2":
            img, strength = co2.copy(), 1.4
        elif name == "door":
            img = door.copy()
            if t >= AT["kitchen"]:   # світло з кухні гасне після «з кухні»
                k = min(1, (t - AT["kitchen"] - 1.0) / 0.3) if t > AT["kitchen"] + 1.0 else 0
                img = Image.blend(img, Image.new("RGB", img.size, (5, 5, 6)), k)
            strength = 1.2
        else:
            img = Image.blend(black, end, min(1.0, (t - start) / 0.5))
            osd, strength = False, 0.8
        sub = current_sub(t)
        if sub and name not in ("snow", "end", "co1"):
            img = subtitle(img if img is not alert_txt else img.copy(), sub)
        fr = vhs_fast(img, strength=strength, osd=osd, counter=counter(t + 1), t=t)
        proc.stdin.write(sf.to_169(fr).tobytes())
    proc.stdin.close()
    proc.wait()


# ---------- звук ----------

def compress(x, thr=0.18, ratio=3.0):
    a = np.abs(x)
    env = np.convolve(a, np.ones(441) / 441, mode="same")
    gain = np.where(env > thr, (thr + (env - thr) / ratio) / np.maximum(env, 1e-6), 1.0)
    return x * gain


def build_audio(voice_mp3: str, path: Path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    voice = load_mp3(voice_mp3)
    vo = np.zeros(n)
    for k, (a, b) in SRC.items():
        seg = voice[int(a * SR):int(b * SR)].astype(np.float64)
        fade = np.minimum(1, np.minimum(np.arange(seg.size), np.arange(seg.size)[::-1]) / (0.015 * SR))
        seg *= fade
        if k in RADIO:
            seg = bandpass(seg, 300, 3600)
            seg = np.tanh(seg * 2.0) * 0.8
        else:
            seg = bandpass(seg, 70, 9000)
            seg = compress(seg) * 1.0
        if k == "kitchen":     # трохи «кімнати»: коротке відлуння
            echo = np.zeros(seg.size + int(0.09 * SR))
            echo[:seg.size] += seg
            echo[int(0.09 * SR):] += seg * 0.25
            seg = echo
        s = int(AT[k] * SR)
        e = min(n, s + seg.size)
        vo[s:e] += seg[:e - s]
    vo = vo / max(1e-6, np.abs(vo).max()) * 0.9

    # фон: шипіння + 50 Гц, притишується під голосом (ducking)
    hiss = bandpass(RNG.normal(0, 1, n), 1500, 9000) * 0.02
    hum = (np.sin(2 * np.pi * 50 * tt) + 0.4 * np.sin(2 * np.pi * 100 * tt)) * 0.022
    venv = np.convolve(np.abs(vo), np.ones(4410) / 4410, mode="same")
    duck = 1 - 0.6 * np.clip(venv / 0.05, 0, 1)
    mix = (hiss + hum) * duck

    def seg_idx(a, b):
        return slice(int(a * SR), int(b * SR))

    # тон оповіщення
    sl = seg_idx(0.0, 1.5)
    tone = (np.sin(2 * np.pi * 1050 * tt[sl]) + 0.5 * np.sin(2 * np.pi * 1057 * tt[sl])) * 0.17
    mix[sl] += tone * np.minimum(1, np.minimum(tt[sl] * 50, (1.5 - tt[sl]) * 50))
    # низький тон під червоним екраном
    sl = seg_idx(22.75, 25.35)
    t2 = tt[sl] - 22.75
    mix[sl] += (np.sin(2 * np.pi * 420 * tt[sl]) + 0.6 * np.sin(2 * np.pi * 427 * tt[sl])) * 0.13 * \
        np.minimum(1, np.minimum(t2 * 30, (2.6 - t2) * 30))
    # сніг
    sl = seg_idx(5.55, 5.85)
    mix[sl] += RNG.normal(0, 0.22, mix[sl].size)
    # гул у сцені з вікном, наростає
    sl = seg_idx(5.85, 22.75)
    t3 = tt[sl] - 5.85
    mix[sl] += np.sin(2 * np.pi * 41 * tt[sl]) * (0.03 + 0.05 * t3 / 16.9) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * tt[sl]))

    # удари «тричі»
    for h in HITS:
        m = int(0.6 * SR)
        x = np.arange(m) / SR
        hit = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 7) * 0.5 + bandpass(RNG.normal(0, 1, m), 40, 400) * np.exp(-x * 14) * 0.3
        s = int(h * SR)
        mix[s:s + m] += hit[:n - s]
    # тиша перед стуками: різко вимикаємо фон на 0.6 с
    mix[seg_idx(31.35, 31.95)] *= 0.15
    for k in KNOCKS:
        kk = knock()
        s = int(k * SR)
        mix[s:s + kk.size] += kk * 0.85

    total = mix + vo
    total = total / max(1.0, np.abs(total).max() / 0.95)
    st = np.stack([total, total], axis=1)
    sl = seg_idx(KNOCKS[0], KNOCKS[-1] + 0.4)
    st[sl, 0] -= (mix[sl] * 0.4)   # стуки зміщені праворуч
    st = np.clip(st, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def main():
    voice_mp3, out = sys.argv[1], Path(sys.argv[2])
    with tempfile.TemporaryDirectory() as tmp:
        v, a = Path(tmp) / "v.mp4", Path(tmp) / "a.wav"
        build_audio(voice_mp3, a)
        render_video(v)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-i", str(a),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    print("Готово:", out)


if __name__ == "__main__":
    main()
