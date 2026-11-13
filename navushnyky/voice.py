#!/usr/bin/env python3
"""Озвучка Kokoro (am_adam) по реченню + тайминги речень і слів.

    ~/kokoro-venv/bin/python navushnyky/voice.py navushnyky/script_en.txt navushnyky/voice
Вихід: voice.wav (48 кГц моно), lines.json [{"text","s","e"}], words.json [{"w","s","e"}].
Тайминги слів наближені: тривалість речення ділиться за довжиною слів (faster-whisper тут недоступний).
"""
import json, os, re, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

script, outdir = sys.argv[1], sys.argv[2]
VOICE, SPEED, GAP, LEAD = os.environ.get("VOICE", "am_adam"), float(os.environ.get("SPEED", "1.2")), 0.12, 0.05
MODELS = os.environ.get("KOKORO_DIR", "/home/user/kokoro-models")
k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
lines = [l.strip() for l in open(script, encoding="utf-8") if l.strip()]
parts, t, meta, words = [], LEAD, [], []
sr = 24000
parts.append(np.zeros(int(LEAD * sr), np.float32))
for ln in lines:
    m = re.match(r"#p([\d.]+)\s+(.*)", ln)                # «#p0.8 текст» — додаткова пауза перед реченням
    if m:
        extra, ln = float(m.group(1)), m.group(2)
        parts.append(np.zeros(int(extra * sr), np.float32))
        t += extra
    x, sr = k.create(ln, voice=VOICE, speed=SPEED, lang="en-us")
    x = np.asarray(x, np.float32)
    # обрізати тишу на краях
    nz = np.nonzero(np.abs(x) > 0.01)[0]
    x = x[max(0, nz[0] - 240): nz[-1] + 480] if nz.size else x
    d = x.size / sr
    meta.append({"text": ln, "s": round(t, 3), "e": round(t + d, 3)})
    ws = ln.split()
    weights = np.array([len(re.sub(r"\W", "", w)) + 1.5 for w in ws], float)
    edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * d
    for w, a, b in zip(ws, edges[:-1], edges[1:]):
        words.append({"w": w, "s": round(t + a, 3), "e": round(t + b, 3)})
    pause = GAP + (0.18 if ln.endswith(("?", ".")) and len(ws) <= 4 else 0)
    parts += [x, np.zeros(int(pause * sr), np.float32)]
    t += d + pause
y = np.concatenate(parts)
y = y / (np.abs(y).max() + 1e-9) * 0.9
tmp = os.path.join(outdir, "_24k.wav")
sf.write(tmp, y, sr, subtype="PCM_16")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-ar", "48000", "-ac", "1", os.path.join(outdir, "voice.wav")], check=True)
os.remove(tmp)
json.dump(meta, open(os.path.join(outdir, "lines.json"), "w"), ensure_ascii=False, indent=1)
json.dump(words, open(os.path.join(outdir, "words.json"), "w"), ensure_ascii=False, indent=0)
print(f"{len(lines)} речень, {len(words)} слів, {t:.1f} с, {len(words)/t:.2f} слова/с")
