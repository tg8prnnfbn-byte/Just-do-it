#!/usr/bin/env python3
"""«Канцелярська драма»: 2D-мультик 1080x1920, 30 fps (рушій навушників). 6 кадрів за сценарієм користувача.

    python3 kantseliariia/film_k.py kantseliariia/out/video_silent.mp4 [--stills 1,5]
"""
from __future__ import annotations

import math
import os
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
os.environ.setdefault("VOICE_DIR", str(HERE / "voice"))
sys.path.insert(0, str(HERE.parent / "navushnyky"))
sys.path.insert(0, str(HERE))

import film as F  # noqa: E402
import lset  # noqa: E402
import chars as C  # noqa: E402

ss, shot = F.ss, F.shot
L = F.LINES

# ---------- синхронізація губ: огинаюча голосу по кадрах ----------
with wave.open(str(HERE / "voice" / "voice.wav")) as w:
    _v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    _sr = w.getframerate()
_hop = _sr // 30
_env = np.sqrt(np.convolve(_v ** 2, np.ones(_hop) / _hop, mode="same"))[::_hop]
_env = np.clip(_env / (np.percentile(_env[_env > 0.01], 90) + 1e-6), 0, 1) if (_env > 0.01).any() else _env


def talk(t, who):
    for ln in L:
        if ln["who"] == who and ln["s"] - 0.02 <= t <= ln["e"]:
            i = min(len(_env) - 1, int(t * 30))
            return float(_env[i]) ** 0.7
    return 0.0


def line_of(i):
    return L[i]["s"], L[i]["e"]


# позиції (світові координати, ступні)
DAD_X, DAD_Y = 650, 2230
DAD_NEAR = 1150
MOM_X, MOM_Y, MOM_S = 1600, 2180, 0.95


def mom_top():
    return MOM_Y - 1250 * MOM_S


def baby_pos():
    return MOM_X + 10, mom_top() + 960 * MOM_S


def build():
    F.SHOTS.clear()
    s0, e0 = line_of(0)
    s1, e1 = line_of(1)
    s2, e2 = line_of(2)
    s3, e3 = line_of(3)
    s4, e4 = line_of(4)
    T1 = e0 + 0.45
    T2 = e1 + 0.45
    T3 = e2 + 0.55
    T4 = e3 + 0.7
    T5 = e4 + 0.3
    T6 = T5 + 1.6
    END = F.DUR

    def mom_baby(P, t, expr="smile", look=(0, 0), sweat=0.0, blink=None, giggle=0.0, ruler=None, draw_arm=None):
        C.mom(P, MOM_X, MOM_Y, t, s=MOM_S, look=look, mouth_open=talk(t, "mom"), expr=expr, sweat=sweat, ruler=ruler)
        bx, by = baby_pos()
        bl = blink if blink is not None else ((t * 0.7) % 1) < 0.06
        C.baby(P, bx, by, t, s=0.85, blink=bl, giggle=giggle, draw_arm=draw_arm)

    # 1. Загальний: тато заходить, завмирає, очі-спіралі
    def s1_draw(P, t, lt):
        mom_baby(P, t, expr="smile")
        walking = t < 1.6
        x = -200 + (DAD_X + 200) * ss(min(1, t / 1.6))
        spiral = t > 1.85
        drop = 0.45 * ss((t - 1.85) / 0.25) if t > 1.85 else 0.0
        C.dad(P, x, DAD_Y, t, walk=t * 1.7 if walking else None, spiral=spiral,
              mouth_open=max(drop, talk(t, "dad")), expr="shock" if t > 1.7 else "neutral")

    shot("s1", "living", 0.0, T1, [(0, 1100, 1500, 2350, 0), (1.7, 1080, 1480, 2250, 0)], draw_mid=s1_draw, creep=0.0004)

    # 2. Крупно: тато показує на маму, тремтить, драматичний наїзд
    def s2_draw(P, t, lt):
        C.dad(P, DAD_X, DAD_Y, t, point=True, tremble=1.0, expr="furious", mouth_open=talk(t, "dad"), look=(0.6, 0))

    shot("s2", "living", T1, T2, [(0, 760, 1220, 1250, 0), (T2 - T1, 760, 1200, 980, 0)], draw_mid=s2_draw,
         creep=0.0, kicks=[s1 + 0.05], dof=6)

    # 3. Крупно: мама з малюком, винувата усмішка, очі бігають
    def s3_draw(P, t, lt):
        look = (1.0 if math.sin(t * 5) > 0 else -1.0, 0.1)
        mom_baby(P, t, expr="nervous", look=look, blink=(lt % 1.6) > 1.45)

    shot("s3", "living", T2, T3, [(0, MOM_X, 1580, 1200, 0), (T3 - T2, MOM_X, 1580, 1100, 0)], draw_mid=s3_draw,
         creep=0.0, dof=6)

    # 4. Надкрупно: тато мружиться і нюхає малюка, повільний наїзд
    def s4_draw(P, t, lt):
        mom_baby(P, t, expr="nervous", look=(-1, 0))
        C.dad(P, DAD_NEAR, DAD_Y, t, lid=0.5, expr="suspicious", lean=7 * ss(lt / 0.6), mouth_open=talk(t, "dad"),
              look=(1, 0.3))
        if lt < 0.8:                                                    # лінії нюхання
            for i in range(3):
                ph = (lt * 3 + i / 3) % 1
                P.arc(1330 + 40 * ph, 1180, 30 + 20 * i, 300, 60, w=4)

    shot("s4", "living", T3, T4, [(0, 1290, 1250, 900, 0), (T4 - T3, 1300, 1230, 720, 0)], draw_mid=s4_draw,
         creep=0.0, dof=4)

    # 5а. Двері відчиняються, сусід у дверях
    def s5_draw(P, t, lt):
        mom_baby(P, t, expr="nervous", look=(1, 0))
        lset.door_leaf(P, ss(lt / 0.6))
        if lt > 0.25:
            C.neighbor(P, 2260, 1905, t, s=0.82, lean=-8, mouth_open=talk(t, "neighbor"))

    shot("s5", "living", T4, T5, [(0, 2050, 1350, 1700, 0), (T5 - T4, 2150, 1320, 1500, 0)], draw_mid=s5_draw, creep=0.0)

    # 5б. Мама завмерла: очі навстіж, крапля чорнила на лобі
    def s5b_draw(P, t, lt):
        mom_baby(P, t, expr="shock", look=(0, 0), sweat=ss(lt / 1.2), blink=False)

    shot("s5b", "living", T5, T6, [(0, MOM_X, 1450, 900, 0), (T6 - T5, MOM_X, 1440, 820, 0)], draw_mid=s5b_draw,
         kicks=[T5 + 0.03], creep=0.0, dof=6)

    # 6. Загальний: лінійкою по голові, зірочки, малюк малює жовту смугу
    t_hit = T6 + 0.75

    def s6_draw(P, t, lt):
        if t < T6 + 0.45:
            ang = 80 - 25 * ss(lt / 0.45)                                # замах назад
        elif t < t_hit:
            ang = 55 + 58 * ss((t - T6 - 0.45) / 0.3)                    # удар зверху по гумці
        else:
            ang = 113 - 6 * math.sin((t - t_hit) * 20) * math.exp(-(t - t_hit) * 4)
        line = ss((t - (t_hit + 0.7)) / 1.1) if t > t_hit + 0.7 else 0.0
        reach = None
        if line > 0:
            reach = (DAD_NEAR - 160 + 360 * line, 1100 - 60 * line)
        mom_baby(P, t, expr="smile" if t < t_hit else "nervous", look=(-1, 0), ruler=ang,
                 giggle=1.0 if t > t_hit + 0.3 else 0.0, draw_arm=reach)
        C.dad(P, DAD_NEAR, DAD_Y, t, expr="dizzy" if t > t_hit else "suspicious", dizzy=1.0 if t > t_hit else 0.0,
              spiral=t > t_hit, yellow_line=line, mouth_open=0.3 if t > t_hit else 0.0)

    shot("s6", "living", T6, END, [(0, 1320, 1480, 2150, 0), (END - T6, 1320, 1460, 2000, 0)], draw_mid=s6_draw,
         kicks=[t_hit], creep=0.0, xfade=False)


F.build_shots = build

if __name__ == "__main__":
    F.main()
