#!/usr/bin/env python3
"""Музика й ефекти до «The Kitchen Headphones» + зведення з голосом.

Музика: легкий комедійний марш (фа мажор, 120 bpm): піцикато-мелодія, туба «ум-па», малий барабан.
Розділи йдуть за картинкою: історія → пауза-загадка «Wait» → нічне пояснення (музична скринька) →
фабрика (бадьорий марш) → падіння (ре мінор) → «проповідь» (тепла педаль) → удар на «verdict».
Зведення: голос без змін, музика приглушується під голосом, ефекти тихіше, підсумок −14 LUFS.

    python3 navushnyky/audio/soundtrack.py navushnyky/out/mix.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import dsp as D  # noqa: E402
import instruments as I  # noqa: E402
import film as F  # noqa: E402

F.build_shots()
SH = {s["name"]: s for s in F.SHOTS}
DUR = F.DUR
N = D.ns(DUR)
Q = 0.5
R = D.rng(7)


def m(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------- музика ----------
THEME = [  # (такт, доля, довжина в чвертях, midi) — 8 тактів
    (0, 0, .5, 72), (0, .5, .5, 69), (0, 1, .5, 70), (0, 1.5, .5, 72), (0, 2, 1, 74), (0, 3, 1, 72),
    (1, 0, .5, 70), (1, .5, .5, 69), (1, 1, 1, 67), (1, 2, 1, 64), (1, 3, 1, 67),
    (2, 0, .5, 69), (2, .5, .5, 70), (2, 1, .5, 72), (2, 1.5, .5, 74), (2, 2, 1, 77), (2, 3, 1, 76),
    (3, 0, 1.5, 74), (3, 1.5, .5, 72), (3, 2, 2, 72),
    (4, 0, .5, 72), (4, .5, .5, 69), (4, 1, .5, 70), (4, 1.5, .5, 72), (4, 2, 1, 74), (4, 3, 1, 77),
    (5, 0, .5, 76), (5, .5, .5, 74), (5, 1, .5, 72), (5, 1.5, .5, 70), (5, 2, 1, 69), (5, 3, 1, 67),
    (6, 0, .75, 69), (6, .75, .25, 70), (6, 1, .5, 72), (6, 1.5, .5, 67), (6, 2, 1, 64), (6, 3, 1, 67),
    (7, 0, 1, 65), (7, 1, 1, 69), (7, 2, 2, 65),
]
CHORDS = ["F", "C7", "F", "C7", "F", "Bb", "C7", "F"]
CH = {"F": (41, [57, 60, 65]), "C7": (36, [55, 58, 64]), "Bb": (34, [58, 62, 65]),
      "Dm": (38, [57, 62, 65]), "Gm": (43, [55, 58, 62]), "A7": (33, [55, 61, 64])}


def band(buf, t0, t1, tempo=1.0, melody=True, drums=True, vel=0.7, chords=CHORDS, theme=THEME, inst="pluck"):
    q = Q / tempo
    bar = 4 * q
    t = t0
    k = 0
    while t < t1:
        ch = chords[k % len(chords)]
        root, tri = CH[ch]
        for beat in range(4):
            tb = t + beat * q
            if tb >= t1:
                break
            if beat % 2 == 0:
                D.place(buf, D.pan(I.brass(m(root + (7 if beat == 2 else 0)), q * 0.8, 0.55 * vel, R, "tuba"), -0.1), tb, 0.5)
            else:
                for n in tri:
                    D.place(buf, D.pan(I.pluck(m(n), 0.35 * vel, R, 0.35), 0.25), tb, 0.35)
            if drums:
                D.place(buf, D.pan(I.snare(0.35 * vel if beat % 2 else 0.2 * vel, R, 0.2), 0.1), tb, 0.35)
        if melody:
            for b, beat, ln, n in theme:
                if b == k % 8:
                    tn = t + beat * q
                    if tn < t1:
                        x = I.pluck(m(n), 0.75 * vel, R, 0.5, bright=0.7) if inst == "pluck" else \
                            I.glock(m(n + 12), 0.45 * vel, R, 1.2)
                        D.place(buf, D.pan(x, -0.2), tn, 0.55)
        t += bar
        k += 1


def music():
    buf = np.zeros((2, N))
    t_wait = SH["ten"]["a"]
    t_expl = SH["nothing"]["a"]
    t_fab = SH["fext"]["a"]
    t_rich = SH["rich"]["a"]
    t_fall = SH["invest"]["a"]
    t_serm = SH["sermon"]["a"]
    t_ver = SH["verdict"]["a"]
    band(buf, 0.0, t_wait - 0.05)                                                     # історія
    for i in range(6):                                                                # «Wait…» — тикання
        D.place(buf, D.st(I.pluck(m(84), 0.5, R, 0.2)), t_wait + i * 0.5, 0.4)
    D.place(buf, D.st(I.timpani(m(41), 0.6, R)), SH["ten"]["a"] + 2.1, 0.5)
    # нічне пояснення: педаль + музична скринька
    D.place(buf, I.pad([m(53), m(57), m(60)], t_fab - t_expl, 0.35, R), t_expl, 0.6)
    band(buf, t_expl, t_fab, tempo=0.9, drums=False, vel=0.5, inst="glock")
    band(buf, t_fab, t_rich, tempo=1.15, vel=0.85)                                    # фабрика
    D.place(buf, D.st(I.cymbal(0.5, R)), t_rich, 0.5)
    for i, n in enumerate([72, 76, 79, 84]):
        D.place(buf, D.st(I.glock(m(n), 0.6, R)), t_rich + i * 0.12, 0.5)
    sad = [(b, beat, ln, n - 3) for b, beat, ln, n in THEME]                         # падіння, мінор
    band(buf, t_fall, t_serm - 0.05, tempo=0.8, drums=False, vel=0.6,
         chords=["Dm", "A7", "Dm", "A7", "Gm", "Dm", "A7", "Dm"], theme=sad)
    D.place(buf, I.pad([m(53), m(57), m(60), m(65)], t_ver - t_serm, 0.4, R, att=0.2), t_serm, 0.7)
    t_v = F.Wt("verdict", F.LINES[24]["s"])
    D.place(buf, D.st(I.timpani(m(38), 0.9, R)), t_v, 0.9)
    D.place(buf, D.st(I.brass(m(38), 1.2, 0.8, R, "stab")), t_v, 0.5)
    D.place(buf, D.st(I.cymbal(0.6, R)), t_v, 0.45)
    return buf


# ---------- ефекти ----------
def noise(n):
    return R.standard_normal(n)


def swish(dur=0.35, lo=600, hi=6000):
    n = D.ns(dur)
    t = np.arange(n) / D.SR
    return D.bp(noise(n), lo, hi, 1) * np.sin(np.pi * t / dur) ** 2 * 0.5


def pop(f0=900, f1=300, dur=0.12):
    t = D.tt(dur)
    f = f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / D.SR) * np.exp(-t / 0.05)


def knock(f=180, dur=0.3):
    return D.modal(dur, [(f, 1.0, 0.05), (f * 2.3, 0.5, 0.03), (f * 3.9, 0.25, 0.015)], R) + \
        D.lp(noise(D.ns(dur)), 800) * np.exp(-D.tt(dur) / 0.01) * 0.5


def clank(f=520):
    return D.modal(0.4, [(f, 1, .15), (f * 2.41, .6, .08), (f * 3.7, .4, .05), (f * 5.2, .2, .03)], R)


def chime(base=84):
    y = np.zeros(D.ns(1.2))
    for i, n in enumerate((base, base + 4, base + 7)):
        x = I.glock(m(n), 0.5, R, 0.9)
        y[D.ns(i * 0.07):D.ns(i * 0.07) + len(x)] += x[:len(y) - D.ns(i * 0.07)]
    return y


def scratch(dur):
    n = D.ns(dur)
    t = np.arange(n) / D.SR
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * t))
    return D.bp(noise(n), 2500, 7000, 2) * am * 0.25


def sfx():
    buf = np.zeros((2, N))
    for s in F.SHOTS[1:]:                                                             # зміна кадру
        D.place(buf, D.pan(swish(0.3), 0.2), s["a"] - 0.15, 0.25)
    for s in F.SHOTS:                                                                 # поштовхи
        for k in s["kicks"]:
            D.place(buf, D.st(pop()), k, 0.5)
    D.place(buf, D.st(chime(84)), 0.3, 0.35)
    D.place(buf, D.st(chime(88)), F.Wt("builds", F.LINES[3]["s"]) + 0.3, 0.4)
    for t in np.arange(SH["build"]["a"] + 0.2, F.Wt("builds", F.LINES[3]["s"]) + 0.2, 0.18):
        D.place(buf, D.pan(D.hp(noise(D.ns(0.05)), 3000) * np.exp(-D.tt(0.05) / 0.01), 0.3), t, 0.25)   # іскри
    D.place(buf, D.pan(scratch(SH["letter"]["b"] - SH["letter"]["a"] - 0.3), -0.3), SH["letter"]["a"] + 0.1, 0.6)
    D.place(buf, D.st(swish(0.5, 300, 3000)), SH["navy"]["a"] + 0.1, 0.5)            # шурхіт паперу
    t_beat = F.Wt("beats", F.LINES[11]["s"])
    D.place(buf, D.st(D.bp(noise(D.ns(t_beat - SH["test"]["a"])), 1500, 4000) * 0.12), SH["test"]["a"], 0.6)  # ефір
    D.place(buf, D.st(chime(91)), t_beat, 0.45)
    D.place(buf, D.st(swish(0.9, 200, 2500)), SH["order"]["a"] + 0.1, 0.5)            # сувій
    D.place(buf, D.st(swish(0.7, 200, 2500)), F.Ls(13) + 0.05, 0.6)
    t_ten = F.Ls(15) + 0.05
    for i in range(10):                                                               # 10 навушників на стіл
        D.place(buf, D.pan(knock(420, 0.12), -0.6 + i * 0.13), t_ten + i / 16, 0.35)
    a, b = SH["wedding"]["a"], SH["wedding"]["b"]                                     # гомін гостей
    n = D.ns(b - a)
    D.place(buf, D.st(D.bp(noise(n), 300, 1800) * (0.6 + 0.4 * D.smooth_noise(n, R, 4.0)) * 0.12), a, 1.0)
    a, b = SH["fint"]["a"], SH["fint"]["b"]                                           # цех
    for t in np.arange(a, b, 0.5):
        D.place(buf, D.pan(clank(R.uniform(450, 650)), R.uniform(-0.6, 0.6)), t, 0.25)
    for t in np.arange(a, b, 0.125):
        D.place(buf, D.pan(knock(1800, 0.04), 0.4), t, 0.12)
    a, b = SH["rich"]["a"], SH["rich"]["b"]                                           # монети
    for t in np.arange(a, b, 0.07):
        D.place(buf, D.pan(clank(R.uniform(2500, 4200)) * 0.3, R.uniform(-0.8, 0.8)), t, 0.25)
    a, b = SH["invest"]["a"], SH["invest"]["b"]                                       # крильця грошей
    n = D.ns(b - a)
    tt = np.arange(n) / D.SR
    D.place(buf, D.st(D.bp(noise(n), 400, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * tt)) * 0.15), a, 1.0)
    for t in (F.Wt("convicts", F.LINES[22]["s"]), F.Wt("verdict", F.LINES[24]["s"])):  # молоток
        D.place(buf, D.st(knock(140, 0.4)), t, 1.0)
        D.place(buf, D.st(knock(140, 0.4)), t + 0.28, 0.7)
    return buf


def main():
    out = Path(sys.argv[1])
    voice, sr = D.read_wav(str(HERE.parent / "voice" / "voice.wav"))
    assert sr == D.SR
    v = np.zeros((2, N))
    vv = D.st(voice[0])
    v[:, :min(N, vv.shape[1])] = vv[:, :N]
    mus, fx = music(), sfx()
    # притишення музики під голосом
    env = np.convolve(np.abs(v[0]), np.ones(D.ns(0.15)) / D.ns(0.15), mode="same")
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus = D.norm_to(mus, -26, "integrated") * duck[None, :]
    fx = D.norm_to(fx, -24, "momentary")
    v = D.norm_to(v, -16, "integrated")
    mix = v + mus * D.dbg(3) + fx * D.dbg(-6)
    mix = D.norm_to(mix, -14, "integrated")
    mix = np.tanh(mix * 1.1) / 1.1                         # м'який обмежувач піків
    D.write_wav(str(out), mix, bits=16)
    print(f"Звук: {out}  {D.integrated(mix):.1f} LUFS, пік {D.true_peak(mix):.1f} dBTP")


if __name__ == "__main__":
    main()
