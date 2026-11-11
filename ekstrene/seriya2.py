#!/usr/bin/env python3
"""Серія 2 «Дзвінок з номера, якого немає» — Shorts 9:16.

З озвучкою: файл ElevenLabs з 8 абзаців, розділених довгими паузами.
Скрипт сам знаходить абзаци за паузами і будує під них сцени.
Без озвучки ("-"): аніматик з тими самими сценами, субтитрами і звуками.

    python3 ekstrene/seriya2.py ozvuchka.mp3 ekstrene/seriya-2-shorts.mp4
    python3 ekstrene/seriya2.py - ekstrene/seriya-2-animatyk.mp4
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import style_frames as sf  # noqa: E402
from proba import FPS, SR, bandpass, load_mp3, snow, vhs_fast  # noqa: E402
from proba2 import build_door, compress, write_video  # noqa: E402
from shorts import FH, FW, FY, SUB_Y, VH, VW, wrap  # noqa: E402

RNG = np.random.default_rng(22)
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
HAND = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"

BEATS = [  # (сцена, текст абзацу)
    ("kitchen", "Я не відповів. Голос із кухні замовк."),
    ("phone", "А о третій сім задзвонив телефон. Номер бабусиної хати."),
    ("line", "Ту лінію обрізали ще шість років тому."),
    ("vm", "Я не взяв слухавку. Воно залишило голосове повідомлення."),
    ("vm2", "Спершу — тиша. І дихання. А потім — мій власний голос. «Відповідай»."),
    ("station", "Зранку я поїхав на ту станцію. «Овруч-3». На полиці лежала друга касета."),
    ("tape", "На ній була наклейка. Моїм почерком. І завтрашня дата."),
    ("tape2", "Я не пам'ятаю, щоб я її підписував."),
]
GAP = 0.35        # пауза між абзацами в монтажі
LEAD = 0.6        # тиша на початку
END_CARD = 2.6
TAPE_DATE = "12.11.2026"


# ---------- таймлайн ----------

def speech_segments(mp3: str, min_pause: float):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af",
                          f"silencedetect=noise=-38dB:d={min_pause}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()[2]) + \
        60 * int(re.search(r"Duration: (\d+):(\d+)", out).group(2))
    segs, cur = [], 0.0
    for s, e in zip(starts, ends):
        if s - cur > 0.15:
            segs.append((max(0, cur - 0.04), s + 0.04))
        cur = e
    if dur - cur > 0.15:
        segs.append((cur - 0.04, dur))
    return segs


def find_paragraphs(mp3: str):
    for d in (0.8, 0.9, 0.7, 1.0, 0.6, 1.2, 0.5):
        segs = speech_segments(mp3, d)
        if len(segs) == len(BEATS):
            return segs
    raise SystemExit(f"Не вдалося знайти {len(BEATS)} абзаців за паузами. Перевір, що між абзацами "
                     "в ElevenLabs стоїть [long pause] і абзаців рівно 8.")


def timeline(paras):
    """[(сцена, текст, початок, кінець, (src_a, src_b) | None)] + тривалість."""
    t, out = LEAD, []
    for (scene, text), p in zip(BEATS, paras):
        d = (p[1] - p[0]) if p else max(1.6, len(text) * 0.068)
        hold = {"line": 1.2, "vm2": 0.6, "tape2": 0.8}.get(scene, 0)   # сцени, яким треба «подихати»
        out.append((scene, text, t, t + d, p))
        t += d + GAP + hold
    return out, t + END_CARD


# ---------- сцени (4:3) ----------

def f_inter(size, bold=False):
    return ImageFont.truetype(INTER_B if bold else INTER, size)


def phone_frame(lt, mode, wave_level=0.0, red=0.0):
    """Телефон у темряві. mode: 'call' | 'vm'."""
    img = Image.new("RGB", (sf.CW, sf.H), (5, 5, 6))
    shake = int(6 * math.sin(lt * 70)) if mode == "call" and (lt % 1.0) < 0.55 else 0
    px0, py0, pw, ph = 520 + shake, 120, 400, 820
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).rounded_rectangle((px0 - 60, py0 - 60, px0 + pw + 60, py0 + ph + 60), 90, fill=70)
    img.paste(Image.new("RGB", img.size, (60, 70, 90)), (0, 0), glow.filter(ImageFilter.GaussianBlur(50)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((px0, py0, px0 + pw, py0 + ph), 48, fill=(14, 14, 16))
    scr = (px0 + 14, py0 + 14, px0 + pw - 14, py0 + ph - 14)
    base = (int(18 + 120 * red), 22, int(34 * (1 - red) + 10))
    d.rounded_rectangle(scr, 38, fill=base)
    cx = px0 + pw // 2

    def ctext(y, s, f, fill=(235, 235, 240)):
        d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)

    ctext(py0 + 40, "03:07", f_inter(30, True))
    if mode == "call":
        ctext(py0 + 150, "Вхідний виклик", f_inter(28), (170, 170, 180))
        d.ellipse((cx - 70, py0 + 210, cx + 70, py0 + 350), fill=(60, 60, 70))
        ctext(py0 + 248, "Б", f_inter(70, True))
        ctext(py0 + 380, "Бабуся (хата)", f_inter(44, True))
        ctext(py0 + 440, "Стаціонарний", f_inter(28), (170, 170, 180))
        for x, col in ((cx - 95, (210, 50, 50)), (cx + 95, (60, 180, 90))):
            r = 46 + (6 if col[1] > 100 and (lt % 1.0) < 0.5 else 0)
            d.ellipse((x - r, py0 + 640 - r, x + r, py0 + 640 + r), fill=col)
    else:
        ctext(py0 + 150, "Бабуся (хата)", f_inter(40, True))
        ctext(py0 + 205, "Голосове повідомлення · 0:14", f_inter(26), (170, 170, 180))
        y0 = py0 + 420
        xs = np.arange(scr[0] + 30, scr[2] - 30, 9)
        for i, x in enumerate(xs):
            h = 3 + wave_level * (20 + 120 * abs(math.sin(i * 0.7 + lt * 9)) * RNG.uniform(0.4, 1))
            col = (230, 230, 235) if red < 0.5 else (255, 210, 210)
            d.rounded_rectangle((x, y0 - h, x + 5, y0 + h), 2, fill=col)
        prog = min(1, lt / 4.0)
        d.rectangle((scr[0] + 30, py0 + 620, scr[2] - 30, py0 + 626), fill=(70, 70, 80))
        d.rectangle((scr[0] + 30, py0 + 620, scr[0] + 30 + (scr[2] - scr[0] - 60) * prog, py0 + 626), fill=(230, 230, 235))
    return img


def line_frame(lt):
    img, d = sf.canvas()
    rows = ["Абонентську лінію", "відключено:", "14.03.2020"]
    f = sf.font(66)
    n = int(lt / 0.045)
    y = 360
    for r in rows:
        shown, n = r[:max(0, n)], n - len(r)
        x = (sf.CW - d.textlength(r, font=f)) / 2
        d.text((x, y), shown, font=f, fill=sf.DIRTY_WHITE if r[0] != "1" else sf.ALERT_RED)
        if 0 <= len(shown) < len(r) or (r == rows[-1] and n >= 0):
            if (lt * 2) % 2 < 1.2:
                cx = x + d.textlength(shown, font=f) + 8
                d.rectangle((cx, y + 8, cx + 34, y + 72), fill=sf.DIRTY_WHITE)
            break
        y += 110
    return img


def zoom(img, z, cy=None):
    w, h = int(sf.CW / z), int(sf.H / z)
    cy = cy or sf.H // 2
    top = max(0, min(sf.H - h, cy - h // 2))
    return img.crop(((sf.CW - w) // 2, top, (sf.CW + w) // 2, top + h)).resize((sf.CW, sf.H))


def station_frame(lt):
    img = Image.new("RGB", (sf.CW, sf.H))
    g = np.linspace(0, 1, sf.H)[:, None, None]
    a = np.array([92, 96, 100]) * (1 - g) + np.array([38, 40, 42]) * g
    img = Image.fromarray(np.broadcast_to(a, (sf.H, sf.CW, 3)).astype(np.uint8))
    d = ImageDraw.Draw(img)
    cx, top, base = 760 + int(lt * 6), 90, 900
    col = (28, 29, 30)
    for side in (-1, 1):   # гратчаста щогла
        d.line((cx + side * 12, top, cx + side * 95, base), fill=col, width=7)
    for k in range(14):
        y1 = top + (base - top) * k / 14
        y2 = top + (base - top) * (k + 1) / 14
        w1, w2 = 12 + 83 * k / 14, 12 + 83 * (k + 1) / 14
        d.line((cx - w1, y1, cx + w2, y2), fill=col, width=4)
        d.line((cx + w1, y1, cx - w2, y2), fill=col, width=4)
        d.line((cx - w2, y2, cx + w2, y2), fill=col, width=3)
    d.rectangle((cx - 5, top - 70, cx + 5, top), fill=col)
    if (lt % 1.6) < 0.25:  # червоний вогник на верхівці
        d.ellipse((cx - 9, top - 88, cx + 9, top - 70), fill=(200, 40, 30))
    d.rectangle((0, 860, sf.CW, sf.H), fill=(30, 31, 30))     # земля
    for x in range(0, sf.CW, 46):                              # паркан
        d.line((x, 800, x, 900), fill=(22, 22, 22), width=4)
    d.line((0, 812, sf.CW, 812), fill=(22, 22, 22), width=3)
    d.line((0, 850, sf.CW, 850), fill=(22, 22, 22), width=3)
    fog = Image.new("L", img.size, 0)
    ImageDraw.Draw(fog).rectangle((0, 640, sf.CW, 900), fill=110)
    img.paste(Image.new("RGB", img.size, (120, 124, 126)), (0, 0), fog.filter(ImageFilter.GaussianBlur(70)))
    return img


def hand_text(img, xy, text, size, color=(25, 25, 60)):
    """«Почерк»: курсив, кожна літера трохи повернута і зсунута."""
    f = ImageFont.truetype(HAND, size)
    x, y = xy
    for ch in text:
        g = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((size // 2, size // 3), ch, font=f, fill=color + (235,))
        g = g.rotate(RNG.uniform(-7, 7), resample=Image.BICUBIC)
        img.paste(g, (int(x - size // 2), int(y + RNG.uniform(-3, 3) - size // 3)), g)
        x += ImageDraw.Draw(img).textlength(ch, font=f) * RNG.uniform(0.95, 1.08)


_TAPE = {}


def tape_base():
    if "img" in _TAPE:
        return _TAPE["img"]
    img = Image.new("RGB", (sf.CW, sf.H), (20, 17, 14))   # дерев'яна полиця
    a = np.asarray(img).astype(np.float32)
    a += (np.sin(np.arange(sf.H) / 9)[:, None, None] * 4 + RNG.normal(0, 3, (sf.H, sf.CW, 1)))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 230, 260, 1210, 860
    d.rounded_rectangle((x0 + 14, y0 + 18, x1 + 14, y1 + 18), 26, fill=(6, 5, 4))      # тінь
    d.rounded_rectangle((x0, y0, x1, y1), 26, fill=(24, 24, 26))
    d.rounded_rectangle((x0 + 330, y0 + 330, x1 - 330, y0 + 470), 18, fill=(10, 10, 11))  # віконце
    for cx in (x0 + 400, x1 - 400):
        d.ellipse((cx - 50, y0 + 350, cx + 50, y0 + 450), fill=(45, 40, 34))
        d.ellipse((cx - 16, y0 + 384, cx + 16, y0 + 416), fill=(200, 200, 200))
    lab = (x0 + 90, y0 + 50, x1 - 90, y0 + 290)
    d.rectangle(lab, fill=(222, 214, 190))
    for k in range(1, 5):
        d.line((lab[0] + 20, lab[1] + k * 46, lab[2] - 20, lab[1] + k * 46), fill=(170, 175, 200), width=2)
    hand_text(img, (lab[0] + 60, lab[1] + 30), "КАСЕТА №2", 96)
    hand_text(img, (lab[0] + 360, lab[1] + 150), TAPE_DATE, 72)
    _TAPE["img"] = img
    return img


def tape_frame(lt, dark=0.0, date_flicker=False):
    img = tape_base()
    z = 1 + 0.05 * lt
    w, h = int(sf.CW / z), int(sf.H / z)
    cx, cy = sf.CW // 2 + 120, sf.H // 2 - 60
    img = img.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)).resize((sf.CW, sf.H))
    if date_flicker and RNG.random() < 0.18:
        ImageDraw.Draw(img).rectangle((760, 440, 1300, 560), fill=(222, 214, 190))
    if dark:
        img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), dark)
    return img


def end_frame(lt):
    img, d = sf.canvas()
    sf.center_text(d, 410, "КАСЕТА №2", sf.font(96), sf.DIRTY_WHITE)
    sf.center_text(d, 560, "ЗАВТРА", sf.font(72), sf.ALERT_RED)
    return Image.blend(sf.canvas()[0], img, min(1, lt / 0.4))


def scene_image(scene, lt, beat_len):
    if scene == "kitchen":
        if "door" not in _TAPE:
            door = build_door()
            _TAPE["door"] = Image.blend(door, Image.new("RGB", door.size, (5, 5, 6)), 0.75)
        return _TAPE["door"].copy()
    if scene == "phone":
        return zoom(phone_frame(lt, "call"), 1.35, 530)
    if scene == "line":
        return line_frame(lt)
    if scene == "vm":
        return zoom(phone_frame(lt, "vm", wave_level=0.0), 1.35, 530)
    if scene == "vm2":
        k = lt / beat_len
        spike = k > 0.8
        return zoom(phone_frame(lt + 4, "vm", wave_level=0.25 + (1.0 if spike else 0.15 * math.sin(lt * 3) ** 2),
                                red=1.0 if spike else 0.0), 1.35 + (0.15 if spike else 0), 530)
    if scene == "station":
        return station_frame(lt)
    if scene == "tape":
        return tape_frame(lt)
    if scene == "tape2":
        return tape_frame(lt + beat_len, dark=0.35, date_flicker=True)
    return end_frame(lt)


# ---------- кадр Shorts ----------

HOOK = ["МЕНІ ПОДЗВОНИЛИ", "З НОМЕРА, ЯКОГО НЕМАЄ"]


def make_frame(t, tl, total):
    cur = None
    for i, (scene, text, a, b, _) in enumerate(tl):
        nxt = tl[i + 1][2] if i + 1 < len(tl) else total - END_CARD
        if a - GAP / 2 <= t < nxt - GAP / 2 or (i == 0 and t < a):
            cur = (scene, text, a, b)
            break
    if cur is None:
        scene, text, a, b = "end", None, total - END_CARD, total
    else:
        scene, text, a, b = cur
    lt = max(0.0, t - a)
    # коротка перебивка снігом на стиках сцен
    edges = [x[2] for x in tl[1:]]
    if any(abs(t - (e - GAP / 2)) < 0.06 for e in edges):
        img, strength, osd = snow(), 1.6, False
    else:
        img = scene_image(scene, lt, b - a)
        strength = 1.6 if scene == "vm2" and lt / (b - a) > 0.8 else 1.15
        osd = scene != "end"
    fr = vhs_fast(img, strength=strength, osd=osd, counter=f"0:00:{int(t) + 1:02d}", t=t)

    small = fr.resize((180, 135)).filter(ImageFilter.GaussianBlur(4))
    bw = int(VH * 4 / 3)
    bg = small.resize((bw, VH)).crop(((bw - VW) // 2, 0, (bw + VW) // 2, VH))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.65)
    bg.paste(fr.resize((FW, FH)), (0, FY))
    d = ImageDraw.Draw(bg)
    tag = "ЗНАЙДЕНИЙ ЗАПИС · ЧАСТИНА 2"
    ft = sf.font(38)
    tw = d.textlength(tag, font=ft)
    d.rectangle(((VW - tw) / 2 - 20, 150, (VW + tw) / 2 + 20, 208), fill=sf.ALERT_RED)
    d.text(((VW - tw) / 2, 156), tag, font=ft, fill=(255, 255, 255))
    fh = sf.font(64)
    for i, ln in enumerate(HOOK):
        w = d.textlength(ln, font=fh)
        d.text(((VW - w) / 2, 250 + i * 86), ln, font=fh, fill=sf.DIRTY_WHITE, stroke_width=4, stroke_fill=(0, 0, 0))
    if text and a - 0.05 <= t <= b + 0.3:
        f = sf.font(58)
        y = SUB_Y
        for ln in wrap(d, text, f, VW - 120):
            w = d.textlength(ln, font=f)
            d.text(((VW - w) / 2, y), ln, font=f, fill=(250, 246, 225), stroke_width=6, stroke_fill=(0, 0, 0))
            y += 76
    return bg


# ---------- звук ----------

def build_audio(mp3, tl, total, path):
    n = int(total * SR)
    tt = np.arange(n) / SR
    vo = np.zeros(n)
    if mp3:
        voice = load_mp3(mp3)
        for scene, _, a, _, src in tl:
            seg = voice[int(src[0] * SR):int(src[1] * SR)].astype(np.float64)
            fade = np.minimum(1, np.minimum(np.arange(seg.size), np.arange(seg.size)[::-1]) / (0.015 * SR))
            seg = compress(bandpass(seg * fade, 70, 9000))
            if scene == "vm2":   # друга половина звучить «з телефона»
                h = seg.size // 2
                seg[h:] = np.tanh(bandpass(seg[h:], 400, 3200) * 2.5) * 0.7
            s = int(a * SR)
            e = min(n, s + seg.size)
            vo[s:e] += seg[:e - s]
        vo = vo / max(1e-6, np.abs(vo).max()) * 0.9

    hiss = bandpass(RNG.normal(0, 1, n), 1500, 9000) * 0.02
    hum = (np.sin(2 * np.pi * 50 * tt) + 0.4 * np.sin(2 * np.pi * 100 * tt)) * 0.02
    venv = np.convolve(np.abs(vo), np.ones(4410) / 4410, mode="same")
    mix = (hiss + hum) * (1 - 0.6 * np.clip(venv / 0.05, 0, 1))

    def sl(a, b):
        return slice(int(a * SR), min(n, int(b * SR)))

    by = {s: (a, b) for s, _, a, b, _ in tl}
    # вібрація телефону: імпульси 160 Гц
    a, b = by["phone"]
    s = sl(a - 0.2, b + 0.3)
    x = tt[s]
    mix[s] += np.sin(2 * np.pi * 160 * x) * ((x - x[0]) % 1.0 < 0.55) * 0.12
    # дихання у голосовому
    a, b = by["vm2"]
    s = sl(a, a + (b - a) * 0.55)
    x = tt[s] - a
    breath = bandpass(RNG.normal(0, 1, x.size), 300, 1600) * (np.sin(np.pi * (x % 1.6) / 1.6) ** 2) * 0.07
    mix[s] += breath
    # вітер біля станції
    a, b = by["station"]
    s = sl(a - 0.2, b + 0.4)
    x = tt[s] - tt[s][0]
    mix[s] += bandpass(RNG.normal(0, 1, x.size), 150, 900) * (0.05 + 0.03 * np.sin(x * 0.9)) \
        * np.minimum(1, x / 0.8)
    # гул, що наростає до кінця
    a = by["tape"][0]
    s = sl(a, total - END_CARD)
    x = tt[s] - a
    mix[s] += np.sin(2 * np.pi * 41 * tt[s]) * (0.03 + 0.04 * x / max(1, x[-1]))
    # низький удар на кінцевій картці
    s0 = int((total - END_CARD) * SR)
    m = int(1.4 * SR)
    x = np.arange(m) / SR
    hit = np.sin(2 * np.pi * 48 * x) * np.exp(-x * 3) * 0.6
    mix[s0:s0 + m] += hit[:n - s0]
    # сніг на стиках
    for e in [x[2] for x in tl[1:]]:
        s = sl(e - GAP / 2 - 0.06, e - GAP / 2 + 0.06)
        mix[s] += RNG.normal(0, 0.15, mix[s].size)

    total_sig = mix + vo
    total_sig = np.clip(total_sig / max(1.0, np.abs(total_sig).max() / 0.95), -1, 1)
    st = np.stack([total_sig, total_sig], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def main():
    mp3, out = sys.argv[1], Path(sys.argv[2])
    mp3 = None if mp3 == "-" else mp3
    paras = find_paragraphs(mp3) if mp3 else [None] * len(BEATS)
    tl, total = timeline(paras)
    import proba2
    proba2.DUR = total   # write_video бере тривалість звідти
    with tempfile.TemporaryDirectory() as tmp:
        v, a = Path(tmp) / "v.mp4", Path(tmp) / "a.wav"
        build_audio(mp3, tl, total, a)
        write_video(v, (VW, VH), lambda t: make_frame(t, tl, total), crf=27)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-i", str(a),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    print(f"Готово: {out} ({total:.1f} с)")


if __name__ == "__main__":
    main()
