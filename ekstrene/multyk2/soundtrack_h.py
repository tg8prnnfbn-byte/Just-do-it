#!/usr/bin/env python3
"""Звук до мультяшної Серії 2 хорору: гул, моторошна музична скринька, серцебиття, вібрація
телефону, шум голосового, вітер, удари на поштовхах. «Answer.» звучить як із телефона,
фінальна фраза з луною. Зведення −14 LUFS.

    python3 ekstrene/multyk2/soundtrack_h.py ekstrene/multyk2/out/mix.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NAV = HERE.parents[1] / "navushnyky"
sys.path.insert(0, str(NAV / "audio"))
sys.path.insert(0, str(HERE))
import dsp as D  # noqa: E402
import instruments as I  # noqa: E402
import film_h  # noqa: E402

F = film_h.F
film_h.build()
SH = {s["name"]: s for s in F.SHOTS}
N = D.ns(F.DUR)
R = D.rng(13)


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def noise(n):
    return R.standard_normal(n)


def music():
    buf = np.zeros((2, N))
    # низький гул на весь ролик, наростає
    t = D.tt(F.DUR)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 55.7 * t) + 0.3 * np.sin(2 * np.pi * 82.4 * t))
    drone *= (0.5 + 0.5 * t / F.DUR) * (0.7 + 0.3 * D.smooth_noise(N, R, 0.3))
    D.place(buf, D.st(drone * 0.25), 0)
    D.place(buf, I.pad([m(50), m(53), m(57)], F.DUR, 0.25, R, att=3, rel=1, warm=600), 0, 0.8)
    # музична скринька (ре мінор), трохи розстроєна — тиха колискова
    motif = [74, 77, 76, 74, 69, 72, 70, 69]
    tt0 = SH["callscreen"]["a"]
    k = 0
    while tt0 < SH["voicemail"]["a"]:
        n = motif[k % len(motif)]
        x = I.musicbox(m(n) * (1 + 0.004 * np.sin(k)), 0.4, R, 1.4)
        D.place(buf, D.pan(x, 0.3), tt0, 0.5)
        tt0 += 0.62
        k += 1
    for name in ("learn", "shelf", "final"):
        tt0, end = SH[name]["a"], SH[name]["b"]
        k = 0
        while tt0 < end:
            D.place(buf, D.pan(I.musicbox(m(motif[k % 8] - 12), 0.35, R, 1.6), -0.3), tt0, 0.45)
            tt0 += 0.8
            k += 1
    # серцебиття під голосовим, частішає
    a, b = SH["voicemail"]["a"], SH["voicemail"]["b"]
    tt0 = a
    while tt0 < b:
        u = (tt0 - a) / (b - a)
        for off, v in ((0, 0.7), (0.18, 0.45)):
            D.place(buf, D.st(I.timpani(m(31), v, R, 0.5)), tt0 + off, 0.8)
        tt0 += 0.95 - 0.4 * u
    # удари на поштовхах
    for s in F.SHOTS:
        for kt in s["kicks"]:
            D.place(buf, D.st(I.timpani(m(29), 0.9, R, 1.8)), kt, 0.9)
            D.place(buf, D.st(I.brass(m(41), 0.9, 0.7, R, "stab")), kt, 0.35)
    return buf


def vibrate(dur):
    t = D.tt(dur)
    return np.sin(2 * np.pi * 165 * t) * (np.sin(2 * np.pi * 1.0 * t) > 0.1) * 0.6


def sfx():
    buf = np.zeros((2, N))
    for name in ("hook", "callscreen", "nopickup"):
        a, b = SH[name]["a"], SH[name]["b"]
        D.place(buf, D.st(vibrate(b - a)), a, 0.5)
    a, b = SH["voicemail"]["a"], SH["voicemail"]["b"]                                 # шум лінії
    n = D.ns(b - a)
    D.place(buf, D.st(D.bp(noise(n), 1500, 5000) * 0.05), a)
    a = F.Ls(11)                                                                     # дихання
    n = D.ns(1.8)
    tt = D.tt(1.8)
    D.place(buf, D.st(D.bp(noise(n), 300, 1600) * np.sin(np.pi * (tt % 0.9) / 0.9) ** 2 * 0.25), a)
    for name in ("rule", "learn"):                                                    # вітер у лісі
        a, b = SH[name]["a"], SH[name]["b"]
        n = D.ns(b - a)
        D.place(buf, D.widen(D.bp(noise(n), 150, 900) * (0.6 + 0.4 * D.smooth_noise(n, R, 0.5)) * 0.25, R), a)
    a, b = SH["road"]["a"], SH["road"]["b"]                                           # двигун
    tt = D.tt(b - a)
    D.place(buf, D.st(D.lp(np.sign(np.sin(2 * np.pi * 38 * tt)) * 0.3 + noise(len(tt)) * 0.1, 300)), a, 0.6)
    D.place(buf, D.st(D.modal(0.3, [(900, 1, .04), (2100, .5, .02)], R)), F.Ls(21), 0.5)   # касета
    a, b = SH["log"]["a"], SH["log"]["b"]
    D.place(buf, D.st(vibrate(1.2)), a, 0.5)
    return buf


def main():
    out = Path(sys.argv[1])
    voice, sr = D.read_wav(str(HERE / "voice" / "voice.wav"))
    v = voice[0]
    L = F.LINES
    a, b = D.ns(L[15]["s"] - 0.03), D.ns(L[15]["e"] + 0.05)                          # «Answer.» з телефона
    seg = D.bp(v[a:b], 400, 3200, 2)
    v[a:b] = np.tanh(seg * 3) * 0.6
    vs = np.zeros((2, N))
    vs[:, :min(N, len(v))] = D.st(v[:N])
    a = D.ns(L[26]["s"] - 0.03)                                                     # луна на фіналі
    tail = vs[:, a:].copy()
    for dly, g in ((0.22, 0.35), (0.45, 0.2), (0.7, 0.1)):
        d = D.ns(dly)
        vs[:, a + d:] += tail[:, :vs.shape[1] - a - d] * g
    mus, fx = music(), sfx()
    env = np.convolve(np.abs(vs[0]), np.ones(D.ns(0.15)) / D.ns(0.15), mode="same")
    duck = 1 - 0.5 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus = D.norm_to(mus, -24, "integrated") * duck[None, :]
    fx = D.norm_to(fx, -22, "momentary")
    vs = D.norm_to(vs, -16, "integrated")
    mix = vs + mus * D.dbg(3) + fx * D.dbg(-6)
    mix = D.norm_to(mix, -14, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS, пік {D.true_peak(mix):.1f} dBTP")


if __name__ == "__main__":
    main()
