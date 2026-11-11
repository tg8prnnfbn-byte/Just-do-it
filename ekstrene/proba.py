#!/usr/bin/env python3
"""Проба ~28 с: «Екстрене оповіщення: Полісся, 1987».

Голос: ElevenLabs «Хорор оповідач» із файлу ne-vidpovidai-elevenlabs.mp3
(фраза-правило на початку і «А ти б відповів?» у кінці).

    python3 ekstrene/proba.py /шлях/до/ne-vidpovidai-elevenlabs.mp3 ekstrene/proba-kaseta-1.mp4
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

FPS = 25
SR = 44100
DUR = 28.0

# таймінг (секунди)
T_ALERT_TEXT = 2.0
T_SNOW1 = (4.6, 5.2)
T_CO = 5.2
VOICE_A = (0.0, 8.35)      # «На Поліссі є правило… не відповідай.»
T_VOICE_A = 5.7
T_RULE3 = T_VOICE_A + 4.6   # підсвітити правило 3, коли звучить «якщо вночі з лісу…»
T_SNOW2 = (14.4, 15.0)
T_FOREST = 15.0
T_KNOCKS = 19.6
VOICE_B = (71.62, 73.17)   # «А ти б відповів?»
T_VOICE_B = 22.6
T_END = 24.6

RNG = np.random.default_rng(7)


# ---------- кадри ----------

def vhs_fast(img: Image.Image, strength=1.0, osd=True, counter="0:00:00", t=0.0) -> Image.Image:
    """Швидка VHS-обробка для відео (векторизована версія sf.vhs)."""
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    a = np.asarray(img).astype(np.float32)
    h, w, _ = a.shape
    s = int(4 * strength)
    a[..., 0] = np.roll(a[..., 0], s, axis=1)
    a[..., 2] = np.roll(a[..., 2], -s, axis=1)
    for c in (0, 2):  # горизонтальне розмиття кольору (коробковий фільтр через cumsum)
        cs = np.cumsum(np.pad(a[..., c], ((0, 0), (5, 4)), mode="edge"), axis=1)
        a[..., c] = (cs[:, 9:] - cs[:, :-9]) / 9
    # тремтіння рядків: зсув усього кадру блоками
    jitter = np.round(RNG.normal(0, 0.8 * strength, h // 4)).astype(int)
    idx = (np.arange(w)[None, :] - np.repeat(jitter, 4)[:h, None]) % w
    a = a[np.arange(h)[:, None], idx]
    # смуга трекінгу, що повільно повзе
    y0 = int(h * 0.94 + 18 * np.sin(t * 0.7))
    band = slice(max(y0, 0), min(y0 + 26, h))
    a[band] = np.roll(a[band], int(RNG.uniform(12, 30)), axis=1) * 0.55 + 90
    a[::2] *= 0.8
    a += RNG.normal(0, 9 * strength, (h, w, 1))
    a *= VIGNETTE[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if osd:
        d = ImageDraw.Draw(out)
        f = sf.font(46, bold=False)
        d.text((70, 52), "PLAY ▶", font=f, fill=(235, 235, 235))
        d.text((sf.CW - 330, 52), counter, font=f, fill=(235, 235, 235))
    return out


yy, xx = np.mgrid[0:sf.H, 0:sf.CW]
_r = np.sqrt(((xx - sf.CW / 2) / (sf.CW / 2)) ** 2 + ((yy - sf.H / 2) / (sf.H / 2)) ** 2)
VIGNETTE = np.clip(1.15 - 0.42 * _r ** 2.2, 0, 1).astype(np.float32)


def snow() -> Image.Image:
    a = RNG.integers(0, 255, (sf.H // 3, sf.CW // 3), dtype=np.uint8)
    return Image.fromarray(a).resize((sf.CW, sf.H), Image.NEAREST).convert("RGB")


def alert_screen(n_rows: int, highlight: bool) -> Image.Image:
    img, d = sf.canvas(sf.CO_BLUE)
    c = sf.DIRTY_WHITE
    d.rectangle((0, 130, sf.CW, 250), fill=c)
    sf.center_text(d, 157, "ШТАБ ЦО ОВРУЦЬКОГО Р-НУ", sf.font(62), sf.CO_BLUE)
    d.text((sf.CW - 300, sf.H - 175), "02:14", font=sf.font(70), fill=c)
    d.text((110, sf.H - 165), "ОПОВІЩЕННЯ №1", font=sf.font(48), fill=c)
    rows = [("1. ЗАЛИШАЙТЕСЯ ВДОМА", 1), ("   ВІД ЗАХОДУ ДО СВІТАНКУ.", 1),
            ("2. ЗАВІСЬТЕ ВІКНА,", 2), ("   ЩО ВИХОДЯТЬ НА ЛІС.", 2),
            ("3. НЕ ВІДПОВІДАЙТЕ ГОЛОСАМ", 3), ("   З БОКУ ЛІСУ.", 3),
            ("   ПЕРЕРАХУЙТЕ РІДНИХ.", 3),
            ("4. НЕ ВІДЧИНЯЙТЕ ТИМ,", 4), ("   ХТО СТУКАЄ ТРИЧІ.", 4)]
    f = sf.font(44)
    y = 295
    for text, rule in rows:
        if rule <= n_rows:
            if highlight and rule == 3:
                d.rectangle((95, y - 4, 95 + d.textlength(text, font=f) + 30, y + 56), fill=c)
                d.text((110, y), text, font=f, fill=sf.CO_BLUE)
            else:
                d.text((110, y), text, font=f, fill=c)
        y += 62
    return img


def build_forest_bg() -> Image.Image:
    img = Image.new("RGB", (sf.CW, sf.H))
    g = np.linspace(0, 1, sf.H)[:, None, None]
    a = np.array([22, 26, 30]) * (1 - g) + np.array([8, 9, 10]) * g
    img = Image.fromarray(np.broadcast_to(a, (sf.H, sf.CW, 3)).astype(np.uint8))
    return img


def draw_spruce(d, x, top, base, bw, shade):
    hgt = base - top
    d.rectangle((x - bw * 0.05, top + hgt * 0.2, x + bw * 0.05, sf.H), fill=(shade,) * 3)
    for t in range(7):
        ty = top + hgt * 0.72 * t / 7
        tw = bw * (0.25 + 0.75 * t / 7) * RNG.uniform(0.8, 1.1)
        d.polygon([(x, ty), (x - tw / 2, ty + hgt * 0.2), (x + tw / 2, ty + hgt * 0.2)], fill=(shade,) * 3)


def build_forest_layers():
    """Задній план (з туманом) і передній чорний шар (RGBA), між ними — постать."""
    back = build_forest_bg()
    d = ImageDraw.Draw(back)
    for layer, (shade, count, base, scale) in enumerate([(34, 40, 700, 0.6), (20, 26, 760, 1.0)]):
        for _ in range(count):
            draw_spruce(d, RNG.uniform(-40, sf.CW + 40), RNG.uniform(170, 330) - layer * 80, base,
                        RNG.uniform(70, 120) * scale, shade)
        d.rectangle((0, base, sf.CW, sf.H), fill=(shade,) * 3)
        fog = Image.new("L", (sf.CW, sf.H), 0)
        ImageDraw.Draw(fog).rectangle((0, base - 200, sf.CW, base + 30), fill=60 - layer * 20)
        back.paste(Image.new("RGB", (sf.CW, sf.H), (76, 80, 84)), (0, 0), fog.filter(ImageFilter.GaussianBlur(60)))
        d = ImageDraw.Draw(back)
    front = Image.new("RGBA", (sf.CW, sf.H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(front)
    gx = int(sf.CW * 0.6)
    for _ in range(14):
        x = RNG.uniform(-40, sf.CW + 40)
        if abs(x - gx) < 120:
            continue
        draw_spruce(fd, x, RNG.uniform(-60, 120), 860, RNG.uniform(170, 260), 4)
    fd.rectangle((0, 860, sf.CW, sf.H), fill=(4, 4, 4, 255))
    return back, front


def forest_frame(back, front, closeness: float, flicker: float) -> Image.Image:
    """closeness 0..1: постать повільно росте (наближається)."""
    img = back.copy()
    s = 1.0 + 0.22 * closeness
    gx, gy = int(sf.CW * 0.6), 700 + int(40 * closeness)
    ghost = Image.new("L", (sf.CW, sf.H), 0)
    gd = ImageDraw.Draw(ghost)
    v = int(150 * flicker)
    gd.ellipse((gx - 17 * s, gy - 300 * s, gx + 17 * s, gy - 255 * s), fill=v)
    gd.polygon([(gx - 22 * s, gy - 255 * s), (gx + 22 * s, gy - 255 * s),
                (gx + 30 * s, gy - 20 * s), (gx - 30 * s, gy - 20 * s)], fill=int(v * 0.8))
    gd.line((gx - 22 * s, gy - 245 * s, gx - 40 * s, gy - 60 * s), fill=int(v * 0.73), width=9)
    gd.line((gx + 22 * s, gy - 245 * s, gx + 40 * s, gy - 60 * s), fill=int(v * 0.73), width=9)
    img.paste(Image.new("RGB", (sf.CW, sf.H), (178, 180, 172)), (0, 0), ghost.filter(ImageFilter.GaussianBlur(6)))
    img.paste(front, (0, 0), front)
    return img


def text_screen(lines, size=88):
    img, d = sf.canvas()
    y = sf.H / 2 - len(lines) * size * 0.65
    for ln in lines:
        sf.center_text(d, y, ln, sf.font(size), sf.DIRTY_WHITE)
        y += size * 1.3
    return img


def counter(t):
    return f"0:{int(t // 60):02d}:{int(t % 60):02d}"


def render_video(path: Path):
    alert_txt = text_screen(["УВАГА.", "ЦЕ НЕ НАВЧАННЯ."], 104)
    black = sf.canvas()[0]
    end = text_screen(["КАСЕТА №1", "", "НЕЗАБАРОМ"], 72)
    back, front = build_forest_layers()
    alert_cache = {}

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{sf.W}x{sf.H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        t = i / FPS
        tape_t = t + 1  # лічильник плівки
        if t < T_ALERT_TEXT:
            fr = vhs_fast(black, counter=counter(tape_t), t=t)
        elif t < T_SNOW1[0]:
            fr = vhs_fast(alert_txt, counter=counter(tape_t), t=t)
        elif t < T_SNOW1[1] or T_SNOW2[0] <= t < T_SNOW2[1]:
            fr = vhs_fast(snow(), strength=1.6, osd=False, t=t)
        elif t < T_SNOW2[0]:
            rows = min(4, 1 + int(max(0, t - T_CO - 0.3) / 1.1))
            key = (rows, t >= T_RULE3)
            if key not in alert_cache:
                alert_cache[key] = alert_screen(*key)
            fr = vhs_fast(alert_cache[key], counter=counter(tape_t), t=t)
        elif t < T_END:
            k = (t - T_FOREST) / (T_END - T_FOREST)
            # після стуку постать різко ближче
            closeness = 0.35 * k + (0.55 if t >= T_KNOCKS + 0.9 else 0)
            flicker = 1.0 if RNG.random() > 0.04 else 0.4
            fr = vhs_fast(forest_frame(back, front, min(closeness, 1), flicker),
                          strength=1.5, counter=counter(tape_t), t=t)
        else:
            fade = min(1.0, (t - T_END) / 0.6)
            img = Image.blend(black, end, fade)
            fr = vhs_fast(img, osd=False, strength=0.8, t=t)
        proc.stdin.write(sf.to_169(fr).tobytes())
        if i % 100 == 0:
            print(f"  кадр {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()


# ---------- звук ----------

def load_mp3(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(x.size, 1 / SR)
    X[(f < lo) | (f > hi)] *= 0.03
    return np.fft.irfft(X, x.size)


def place(mix, sig, t, gain=1.0):
    s = int(t * SR)
    e = min(mix.size, s + sig.size)
    mix[s:e] += sig[:e - s] * gain


def knock():
    n = int(0.28 * SR)
    tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 28)
    click = bandpass(RNG.normal(0, 1, n), 200, 2500) * np.exp(-tt * 90)
    return (body * 0.9 + click * 0.5)


def build_audio(voice_mp3: str, path: Path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    mix = np.zeros(n)

    # плівка: шипіння + гудіння мережі 50 Гц (є всюди, крім фінального напису)
    hiss = bandpass(RNG.normal(0, 1, n), 1500, 9000) * 0.018
    hum = (np.sin(2 * np.pi * 50 * tt) + 0.4 * np.sin(2 * np.pi * 100 * tt)) * 0.02
    bed = (hiss + hum)
    bed[int(T_END * SR):] *= np.linspace(1, 0.3, n - int(T_END * SR))
    mix += bed

    # тон оповіщення (свій: 1050 Гц з легким биттям)
    s, e = int(T_ALERT_TEXT * SR), int(T_SNOW1[0] * SR)
    tone = (np.sin(2 * np.pi * 1050 * tt[s:e]) + 0.5 * np.sin(2 * np.pi * 1057 * tt[s:e])) * 0.16
    env = np.minimum(1, np.minimum((tt[s:e] - tt[s]) * 40, (tt[e - 1] - tt[s:e]) * 40))
    mix[s:e] += tone * env

    # снігові перебивки
    for a, b in (T_SNOW1, T_SNOW2):
        mix[int(a * SR):int(b * SR)] += RNG.normal(0, 0.2, int(b * SR) - int(a * SR))

    voice = load_mp3(voice_mp3)
    # голос А: як із гучномовця / телевізора
    va = voice[int(VOICE_A[0] * SR):int(VOICE_A[1] * SR)]
    va = bandpass(va, 320, 3400)
    va = np.tanh(va * 3.2) * 0.45
    place(mix, va, T_VOICE_A)

    # гул у лісі
    s = int(T_FOREST * SR)
    drone = (np.sin(2 * np.pi * 41 * tt[s:]) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * tt[s:]))) * 0.06
    drone *= np.minimum(1, (tt[s:] - tt[s]) / 2)
    drone[int((T_END - T_FOREST) * SR):] *= 0
    mix[s:] += drone

    # три стуки
    for k in range(3):
        place(mix, knock(), T_KNOCKS + k * 0.42, 0.75)

    # голос Б: близько, без «радіо», ніби в кімнаті
    vb = voice[int(VOICE_B[0] * SR):int(VOICE_B[1] * SR)]
    vb = bandpass(vb, 90, 7000) * 1.6
    vb *= np.minimum(1, np.arange(vb.size) / (0.02 * SR))
    place(mix, vb, T_VOICE_B)

    mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.95), -1, 1)
    stereo = np.stack([mix, mix], axis=1)
    # стуки трохи праворуч, «з-за кадру»
    s = int(T_KNOCKS * SR)
    e = int((T_KNOCKS + 1.4) * SR)
    stereo[s:e, 0] *= 0.6
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())


def main():
    voice_mp3, out = sys.argv[1], Path(sys.argv[2])
    with tempfile.TemporaryDirectory() as tmp:
        v, a = Path(tmp) / "v.mp4", Path(tmp) / "a.wav"
        print("звук…")
        build_audio(voice_mp3, a)
        print("відео…")
        render_video(v)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-i", str(a),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
    print("Готово:", out)


if __name__ == "__main__":
    main()
