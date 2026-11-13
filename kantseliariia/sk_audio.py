#!/usr/bin/env python3
"""Звук «Канцелярської драми»: легка музика мильної опери, драматичні акценти, кроки, гіпноз-«вжух»,
нюхання, скрип дверей, «дун-дун-дун», ляпас лінійкою, «бойнг», зірочки, сміх малюка, писк маркера.
Голос не змінюється, музика приглушується під репліками, підсумок −14 LUFS.

    python3 kantseliariia/sk_audio.py kantseliariia/out/mix.wav
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
import film_k as K  # noqa: E402

F = K.F
K.build()
SH = {s["name"]: s for s in F.SHOTS}
N = D.ns(F.DUR)
R = D.rng(5)
T_HIT = SH["s6"]["a"] + 0.75


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def music():
    buf = np.zeros((2, N))
    # м'яка «мильна» тема: піцикато + педаль, до першого акценту і між ними
    mel = [72, 76, 79, 77, 76, 74, 72, 71]
    def soft(a, b, shift=0, vel=0.45):
        t, k = a, 0
        while t < b:
            D.place(buf, D.pan(I.pluck(m(mel[k % 8] + shift), vel, R, 0.7), -0.2), t, 0.5)
            t += 0.42
            k += 1
        D.place(buf, I.pad([m(48 + shift), m(55 + shift), m(64 + shift)], b - a, 0.3, R, att=0.4), a, 0.5)
    soft(0.0, SH["s2"]["a"] - 0.05)
    soft(SH["s3"]["a"], SH["s4"]["a"] - 0.05, shift=-3, vel=0.35)
    # драматичні акценти (мильна опера)
    for t0 in (SH["s2"]["a"],):
        D.place(buf, D.st(I.brass(m(43), 1.1, 0.9, R, "stab")), t0, 0.6)
        D.place(buf, D.st(I.timpani(m(31), 0.9, R)), t0, 0.8)
    a, b = SH["s4"]["a"], SH["s4"]["b"]                                              # напружений тремоло-пад
    tr = lambda t: 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)                               # noqa: E731
    D.place(buf, I.pad([m(45), m(48), m(52)], b - a, 0.45, R, att=0.3, trem=tr), a, 0.7)
    D.place(buf, D.st(I.brass(m(44), 0.8, 0.7, R, "stab")), b - 0.55, 0.5)
    for i, n in enumerate((43, 42, 38)):                                               # «дун-дун-ДУН» на завмирання
        D.place(buf, D.st(I.brass(m(n), 0.32 if i < 2 else 1.2, 0.9, R, "stab")), SH["s5b"]["a"] + i * 0.28, 0.7)
    D.place(buf, D.st(I.timpani(m(26), 1.0, R)), SH["s5b"]["a"] + 0.56, 0.9)
    # фінал: бадьора комічна пісенька
    t, k = SH["s6"]["a"] + 1.0, 0
    while t < F.DUR - 0.2:
        D.place(buf, D.pan(I.pluck(m([72, 74, 76, 79, 76, 74][k % 6]), 0.5, R, 0.4), 0.2), t, 0.5)
        if k % 2 == 0:
            D.place(buf, D.st(I.brass(m(48), 0.2, 0.5, R, "tuba")), t, 0.45)
        t += 0.25
        k += 1
    return buf


def noise(n):
    return R.standard_normal(n)


def knock(f=160, dur=0.25, bright=0.5):
    return D.modal(dur, [(f, 1.0, .05), (f * 2.3, .5, .03), (f * 3.9, .25, .015)], R) + \
        D.lp(noise(D.ns(dur)), 1500) * np.exp(-D.tt(dur) / 0.006) * bright


def sweep(f0, f1, dur, vib=0.0, vol=0.4):
    t = D.tt(dur)
    f = f0 * (f1 / f0) ** (t / dur) * (1 + vib * np.sin(2 * np.pi * 7 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / D.SR) * np.sin(np.pi * t / dur) * vol


def giggle(dur):
    t = D.tt(dur)
    am = np.clip(np.sin(2 * np.pi * 7 * t), 0, 1) ** 2
    f = 820 + 140 * np.sin(2 * np.pi * 7 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / D.SR) * am * 0.35 * np.minimum(1, (dur - t) * 4)


def sfx():
    buf = np.zeros((2, N))
    for t in np.arange(0.1, 1.6, 0.42):                                               # кроки
        D.place(buf, D.pan(knock(140, 0.2, 0.3), -0.4 + t * 0.4), t, 0.5)
    D.place(buf, D.st(sweep(300, 1200, 0.9, vib=0.05)), 1.85, 0.6)                    # гіпноз «вжух»
    for i in range(3):                                                                 # нюхання
        D.place(buf, D.st(D.bp(noise(D.ns(0.18)), 1500, 6000) * np.hanning(D.ns(0.18)) * 0.5), SH["s4"]["a"] + 0.05 + i * 0.22)
    D.place(buf, D.st(sweep(180, 260, 0.6, vib=0.2, vol=0.25)), SH["s5"]["a"], 0.6)  # скрип дверей
    D.place(buf, D.st(knock(220, 0.4, 1.2)), T_HIT, 1.0)                               # ляпас лінійкою
    D.place(buf, D.st(D.hp(noise(D.ns(0.08)), 2000) * np.exp(-D.tt(0.08) / 0.01)), T_HIT, 0.8)
    D.place(buf, D.st(sweep(160, 90, 0.9, vib=0.15, vol=0.5)), T_HIT + 0.05, 0.7)    # «бойнг»
    for i in range(10):                                                                # зірочки
        D.place(buf, D.pan(I.glock(m([84, 88, 91, 96][i % 4]), 0.35, R, 0.5), (-1) ** i * 0.5), T_HIT + 0.2 + i * 0.18, 0.4)
    D.place(buf, D.st(giggle(1.6)), T_HIT + 0.3, 0.9)                                  # сміх малюка
    a = T_HIT + 0.7                                                                    # писк маркера
    D.place(buf, D.st(D.bp(noise(D.ns(1.1)), 2500, 6500) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * D.tt(1.1))) * 0.25), a, 0.8)
    return buf


def main():
    out = Path(sys.argv[1])
    voice, sr = D.read_wav(str(HERE / "voice" / "voice.wav"))
    v = np.zeros((2, N))
    vv = D.st(voice[0])
    v[:, :min(N, vv.shape[1])] = vv[:, :N]
    mus, fx = music(), sfx()
    env = np.convolve(np.abs(v[0]), np.ones(D.ns(0.15)) / D.ns(0.15), mode="same")
    duck = 1 - 0.5 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus = D.norm_to(mus, -24, "integrated") * duck[None, :]
    fx = D.norm_to(fx, -20, "momentary")
    v = D.norm_to(v, -16, "integrated")
    mix = v + mus * D.dbg(3) + fx * D.dbg(-6)
    mix = D.norm_to(mix, -14, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS, пік {D.true_peak(mix):.1f} dBTP")


if __name__ == "__main__":
    main()
