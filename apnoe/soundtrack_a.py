#!/usr/bin/env python3
"""Звук до освітнього мультика про апное: тиха колискова, хропіння, тиша, цокання секунд, фирк,
легкий супровід пояснення, удари на іконках ризиків, тривожний пульс на екстреному виклику,
метроном ~110 уд/хв під час натискань на грудну клітку, тепла педаль у фіналі. −14 LUFS.

    python3 apnoe/soundtrack_a.py apnoe/out/mix.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "navushnyky" / "audio"))
sys.path.insert(0, str(HERE))
import dsp as D  # noqa: E402
import instruments as I  # noqa: E402
import film_a  # noqa: E402

F = film_a.F
film_a.build()
SH = {s["name"]: s for s in F.SHOTS}
N = D.ns(F.DUR)
R = D.rng(21)


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def snore(dur, loud=1.0):
    """Хропіння: вдих з тріпотінням ~28 Гц і шумом, видих тихіше; цикл ~2.4 с."""
    n = D.ns(dur)
    t = np.arange(n) / D.SR
    ph = (t % 2.4) / 2.4
    inhale = np.clip(np.sin(np.pi * ph / 0.55), 0, 1) * (ph < 0.55)
    exhale = np.clip(np.sin(np.pi * (ph - 0.6) / 0.35), 0, 1) * (ph > 0.6) * (ph < 0.95) * 0.35
    flutter = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * t))
    body = D.lp(R.standard_normal(n), 700) * (0.4 + 0.6 * flutter)
    body = D.peq(body, 280, 8, 1.2)
    return body * (inhale + exhale) * 0.6 * loud


def music():
    buf = np.zeros((2, N))
    a_sil, a_snort = SH["silence"]["a"], SH["snort"]["a"]
    lull = [72, 76, 79, 76, 74, 77, 81, 77, 72, 76, 79, 84, 83, 79, 74, 71]
    def lullaby(t0, t1, vel=0.4, inst="glock", step=0.5, shift=0):
        k, t = 0, t0
        while t < t1:
            x = I.glock(m(lull[k % 16] + shift), vel, R, 1.0) if inst == "glock" else I.pluck(m(lull[k % 16] - 12 + shift), vel, R, 0.6)
            D.place(buf, D.pan(x, -0.2 + 0.4 * (k % 2)), t, 0.5)
            t += step
            k += 1
    lullaby(0.0, a_sil - 0.05)                                                      # колискова до тиші
    lullaby(SH["rollover"]["a"], SH["throat"]["a"], vel=0.35)
    lullaby(SH["throat"]["a"], SH["todo"]["a"], vel=0.45, inst="pluck", step=0.4)  # пояснення
    D.place(buf, I.pad([m(48), m(55), m(60)], SH["todo"]["a"] - SH["throat"]["a"], 0.25, R, att=0.8), SH["throat"]["a"], 0.6)
    lullaby(SH["todo"]["a"], SH["emergency"]["a"], vel=0.45, inst="pluck", step=0.35, shift=2)
    D.place(buf, I.pad([m(50), m(57), m(62)], SH["emergency"]["a"] - SH["todo"]["a"], 0.25, R), SH["todo"]["a"], 0.5)
    a, b = SH["emergency"]["a"], SH["final"]["a"]                                    # тривожний пульс
    t = a
    while t < b:
        D.place(buf, D.st(I.timpani(m(38), 0.5, R, 0.4)), t, 0.6)
        t += 0.55
    for s in F.SHOTS:                                                               # удари на поштовхах
        for kt in s["kicks"]:
            D.place(buf, D.st(I.glock(m(84), 0.5, R, 0.8)), kt, 0.4)
            D.place(buf, D.st(I.timpani(m(43), 0.6, R, 1.0)), kt, 0.5)
    a = SH["final"]["a"]
    D.place(buf, I.pad([m(48), m(52), m(55), m(60)], F.DUR - a, 0.4, R, att=0.6), a, 0.7)
    lullaby(a + 0.3, F.DUR - 0.3, vel=0.35, step=0.6)
    return buf


def sfx():
    buf = np.zeros((2, N))
    a_sil, a_snort = SH["silence"]["a"], SH["snort"]["a"]
    D.place(buf, D.st(snore(a_sil - 0.0, 1.0)), 0.0, 0.8)                           # хропіння до тиші
    D.place(buf, D.st(D.bp(R.standard_normal(D.ns(0.7)), 200, 1200) * np.hanning(D.ns(0.7)) * 1.4), a_snort, 0.9)   # фирк
    for name, loud in (("snort", 1.0), ("rollover", 0.9), ("calm", 0.8), ("record", 0.7)):
        D.place(buf, D.st(snore(SH[name]["b"] - SH[name]["a"] - 0.1, loud)), SH[name]["a"] + 0.4 if name == "snort" else SH[name]["a"], 0.7)
    a, b = SH["seconds"]["a"], SH["seconds"]["b"]                                  # цокання
    for t in np.arange(a, b, 0.5):
        D.place(buf, D.st(D.modal(0.05, [(3200, 1, .006), (5100, .5, .004)], R)), t, 0.5)
    a, b = SH["cpr"]["a"], SH["cpr"]["b"]                                           # метроном ~110/хв
    for t in np.arange(a, b, 60 / 110):
        D.place(buf, D.st(D.modal(0.06, [(1800, 1, .01), (2700, .4, .006)], R)), t, 0.6)
    return buf


def main():
    out = Path(sys.argv[1])
    voice, sr = D.read_wav(str(HERE / "voice" / "voice.wav"))
    v = np.zeros((2, N))
    vv = D.st(voice[0])
    v[:, :min(N, vv.shape[1])] = vv[:, :N]
    mus, fx = music(), sfx()
    env = np.convolve(np.abs(v[0]), np.ones(D.ns(0.15)) / D.ns(0.15), mode="same")
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus = D.norm_to(mus, -26, "integrated") * duck[None, :]
    fx = D.norm_to(fx, -22, "momentary") * (1 - 0.3 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1))[None, :]
    v = D.norm_to(v, -16, "integrated")
    mix = v + mus * D.dbg(3) + fx * D.dbg(-6)
    mix = D.norm_to(mix, -14, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS, пік {D.true_peak(mix):.1f} dBTP")


if __name__ == "__main__":
    main()
