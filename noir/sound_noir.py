#!/usr/bin/env python3
"""Звук для «12 Camera Moves»: дощ, далекий місто-гул, кроки по мокрому, нуар-джаз (контрабас піцикато,
щітки, приглушена «труба»), свист повітря на FPV/Ground-Skim/SnapZoom, проїзд машини, гудок таксі на Tilt.
Без голосу, −14 LUFS.

    python3 noir/sound_noir.py noir/out/mix.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "navushnyky" / "audio"))
import dsp as D  # noqa: E402
import instruments as I  # noqa: E402

DUR_SHOT = 3.3
TOTAL = 12 * DUR_SHOT
N = D.ns(TOTAL)
R = D.rng(3)


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def jazz():
    buf = np.zeros((2, N))
    bpm = 96
    q = 60 / bpm
    walk = [38, 41, 43, 44, 45, 43, 41, 40, 38, 36, 38, 41, 43, 46, 45, 43]   # блюзова хода баса
    chords = [[50, 53, 57, 60], [55, 58, 62, 65], [50, 53, 57, 60], [57, 61, 64, 67]]
    t, k = 0.0, 0
    while t < TOTAL - 0.3:
        D.place(buf, D.pan(I.pluck(m(walk[k % 16]), 0.8, R, 0.6, bright=0.3), -0.25), t, 0.8)
        D.place(buf, D.pan(I.brush(0.4 if k % 2 else 0.25, R, 0.25, swish=k % 2 == 0), 0.3), t, 0.5)
        if k % 4 == 0:
            D.place(buf, I.pad([m(n) for n in chords[(k // 4) % 4]], q * 4, 0.22, R, att=0.05, rel=0.4, warm=1400), t, 0.45)
        t += q
        k += 1
    # приглушена «труба» — коротка нуарна фраза двічі
    phrase = [(0, 1.0, 69), (1.2, 0.4, 72), (1.6, 0.4, 70), (2.0, 1.6, 67), (4.0, 0.5, 65), (4.5, 0.5, 67), (5.0, 2.2, 62)]
    for start in (2.0, 21.0):
        for off, ln, n in phrase:
            D.place(buf, D.pan(I.brass(m(n), ln, 0.55, R, "soft"), 0.15), start + off, 0.45)
    return buf


def sfx():
    buf = np.zeros((2, N))
    n = N
    rain = D.bp(R.standard_normal(n), 1500, 9000) * (0.7 + 0.3 * D.smooth_noise(n, R, 0.4))
    rain2 = D.bp(R.standard_normal(n), 300, 1500) * 0.4
    D.place(buf, D.widen(rain * 0.12 + rain2 * 0.08, R), 0)
    D.place(buf, D.st(D.lp(R.standard_normal(n), 120) * 0.25), 0)                    # гул міста
    step = 1.5 / 2 / 1.15                                                            # кроки (крок ~0.65 с)
    for t in np.arange(0.2, TOTAL, step):
        x = D.modal(0.14, [(220, 1, .02), (520, .4, .01)], R) + D.bp(R.standard_normal(D.ns(0.14)), 2000, 7000) * np.exp(-D.tt(0.14) / 0.02) * 0.4
        D.place(buf, D.st(x), t, 0.35)
    def whoosh(t0, dur, vol=0.6):
        tt = D.tt(dur)
        y = D.bp(R.standard_normal(len(tt)), 400, 4000) * np.sin(np.pi * tt / dur) ** 2 * vol
        D.place(buf, D.widen(y, R), t0)
    whoosh(2 * DUR_SHOT + 0.2, 2.8, 0.7)                                             # FPV
    whoosh(9 * DUR_SHOT + 0.3, 2.6, 0.5)                                             # Ground-Skim
    whoosh(11 * DUR_SHOT + 1.05, 0.6, 0.9)                                           # SnapZoom
    D.place(buf, D.st(I.timpani(m(36), 0.8, R, 1.0)), 11 * DUR_SHOT + 1.55, 0.6)
    tt = D.tt(2.2)                                                                    # проїзд машини
    car = D.lp(R.standard_normal(len(tt)), 600) * np.exp(-((tt - 1.1) / 0.5) ** 2) * 0.9
    D.place(buf, D.pan(car, 0.3), 9 * DUR_SHOT + 0.5)
    for k, f in enumerate((415, 523)):                                                # гудок таксі
        tt = D.tt(0.45)
        horn = (np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sin(2 * np.pi * f * 1.5 * tt) * 0.3) * np.minimum(1, (0.45 - tt) * 20)
        D.place(buf, D.st(D.lp(horn, 2500) * 0.3), 10 * DUR_SHOT + 0.6 + k * 0.55)
    return buf


def main():
    out = Path(sys.argv[1])
    mus = D.norm_to(jazz(), -20, "integrated")
    fx = D.norm_to(sfx(), -20, "integrated")
    mix = mus * D.dbg(3) + fx * D.dbg(-2)
    mix = D.norm_to(mix, -14, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS, пік {D.true_peak(mix):.1f} dBTP")


if __name__ == "__main__":
    main()
