#!/usr/bin/env python3
"""Збирає репліки в одну доріжку за планом кадрів і пише voice/voice.wav (48 кГц), lines.json, words.json.
План: дії між репліками (хода, двері, слепстік) — паузи в секундах."""
import json, subprocess, sys, wave
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SR = 48000
lines = json.load(open(HERE / "lines_uk.json", encoding="utf-8"))
# (пауза ПЕРЕД реплікою, пауза ПІСЛЯ)
PLAN = [(2.3, 0.45), (0.35, 0.45), (0.35, 0.55), (0.75, 0.7), (0.8, 1.9)]
TAIL = 4.3   # слепстік після останньої репліки (кадр 5б + 6 враховано в PLAN[4][1] і тут)


def load(p):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    nz = np.nonzero(np.abs(x) > 0.01)[0]
    return x[max(0, nz[0] - 480): nz[-1] + 960] if nz.size else x


t, segs, meta, words = 0.0, [], [], []
for i, (ln, (pre, post)) in enumerate(zip(lines, PLAN)):
    x = load(HERE / "voice" / "raw" / f"{i:02d}.wav")
    t += pre
    d = len(x) / SR
    segs.append((t, x))
    meta.append(dict(text=ln["text"], who=ln["who"], s=round(t, 3), e=round(t + d, 3), pre=pre))
    ws = ln["text"].split()
    wts = np.array([len(w) + 1.5 for w in ws])
    edges = np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * d
    words += [dict(w=w, s=round(t + a, 3), e=round(t + b, 3)) for w, a, b in zip(ws, edges[:-1], edges[1:])]
    t += d + post
total = t + TAIL
y = np.zeros(int(total * SR), np.float32)
for s, x in segs:
    i0 = int(s * SR)
    y[i0:i0 + len(x)] += x[:len(y) - i0]
y = y / (np.abs(y).max() + 1e-9) * 0.9
with wave.open(str(HERE / "voice" / "voice.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((y * 32767).astype(np.int16).tobytes())
meta.append(dict(text="", who="end", s=round(total - 0.01, 3), e=round(total, 3), pre=0))
json.dump(meta, open(HERE / "voice" / "lines.json", "w"), ensure_ascii=False, indent=1)
json.dump(words, open(HERE / "voice" / "words.json", "w"), ensure_ascii=False, indent=0)
print(f"{len(segs)} реплік, {total:.1f} с")
for m in meta:
    print(m["who"], m["s"], m["e"])
