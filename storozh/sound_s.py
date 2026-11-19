#!/usr/bin/env python3
"""Атмосферний звук без голосу для «Правил нічного сторожа»: нічний вітер, далекий собака, гудіння ліхтаря
і його мерехтіння, скрип гойдалки в ритмі її руху (2.4 с), шурхіт паперу, тріск гучномовця, тиха розстроєна
мелодія, дитячий шепіт і низький удар, коли спалахують очі. −16 LUFS (лишаємо місце під голос).

    python3 storozh/sound_s.py storozh/out/mix.wav
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "navushnyky" / "audio"))
import dsp as D  # noqa: E402
import instruments as I  # noqa: E402

FPS = 30
TOTAL = 1080 / FPS
N = D.ns(TOTAL)
R = D.rng(4)


def sec(f):
    return f / FPS


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def main():
    out = Path(sys.argv[1])
    buf = np.zeros((2, N))
    wind = D.bp(R.standard_normal(N), 120, 900) * (0.5 + 0.5 * D.smooth_noise(N, R, 0.15))
    D.place(buf, D.widen(wind * 0.35, R), 0)
    for t in (3.0, 14.5, 27.0):                                                     # далекий собака
        for k in range(2):
            tt = D.tt(0.25)
            bark = D.bp(R.standard_normal(len(tt)), 400, 1400) * np.exp(-tt / 0.07) * 0.25
            D.place(buf, D.pan(bark, 0.7), t + k * 0.35)
    hum = np.sin(2 * np.pi * 100 * D.tt(TOTAL)) * 0.015                             # гудіння ліхтаря
    D.place(buf, D.st(hum), 0)
    for f in range(400, 470, 18):                                                   # мерехтіння ліхтаря
        D.place(buf, D.st(D.hp(R.standard_normal(D.ns(0.06)), 2000) * 0.2), sec(f))
    D.place(buf, D.st(D.hp(R.standard_normal(D.ns(0.12)), 1500) * 0.4), sec(958))   # клац — згас
    # скрип гойдалки: дві ноти на кожному мертвому положенні (період 2.4 с → кожні 1.2 с)
    for t in np.arange(0.6, TOTAL, 1.2):
        n = D.ns(0.4)
        tt = np.arange(n) / D.SR
        f = 1300 + 400 * np.sin(2 * np.pi * 2.5 * tt)
        sq = np.sin(2 * np.pi * np.cumsum(f) / D.SR) * np.sin(np.pi * tt / 0.4) * 0.12
        gain = 1.0 if 360 <= t * FPS < 570 else 0.35
        D.place(buf, D.pan(sq * gain, 0.3), t)
    D.place(buf, D.st(D.bp(R.standard_normal(D.ns(0.5)), 2000, 7000) * np.hanning(D.ns(0.5)) * 0.25), sec(190))   # папір
    a, b = sec(570), sec(720)                                                        # тріск гучномовця
    n = D.ns(b - a)
    crackle = (R.random(n) > 0.9993).astype(float) * R.standard_normal(n) * 0.9 + D.bp(R.standard_normal(n), 800, 3500) * 0.05
    D.place(buf, D.pan(crackle, -0.2), a)
    mel = [76, 72, 74, 71, 72, 69, 71, 67]                                          # розстроєна мелодія з гучномовця
    for i, nn in enumerate(mel):
        x = I.musicbox(m(nn) * 1.006, 0.45, R, 1.2)
        D.place(buf, D.pan(D.bp(x, 400, 3000), -0.2), a + 0.6 + i * 0.55, 0.5)
    D.place(buf, I.pad([m(45), m(48), m(52)], TOTAL - 2, 0.15, R, att=4, rel=2, warm=500), 1.0, 0.8)   # тиха напруга
    for t in np.arange(sec(965), sec(1060), 0.9):                                    # шепіт дітей
        n = D.ns(0.5)
        wh = D.bp(R.standard_normal(n), 2500, 6500) * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.2
        D.place(buf, D.pan(wh, R.uniform(-0.8, 0.8)), t + R.uniform(0, 0.3))
    D.place(buf, D.st(I.timpani(m(28), 1.0, R, 2.5)), sec(985), 0.9)
    D.place(buf, D.st(I.brass(m(40), 1.6, 0.7, R, "soft")), sec(985), 0.4)
    mix = D.norm_to(buf, -16, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS")


if __name__ == "__main__":
    main()
