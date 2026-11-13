#!/usr/bin/env python3
"""Англійська озвучка реплік голосами Kokoro (різний голос для кожного персонажа).
    ~/kokoro-venv/bin/python kantseliariia/en_voice.py kantseliariia/lines_en.json kantseliariia/voice/raw
"""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

M = os.environ.get("KOKORO_DIR", "/home/user/kokoro-models")
k = Kokoro(os.path.join(M, "kokoro-v1.0.onnx"), os.path.join(M, "voices-v1.0.bin"))
lines = json.load(open(sys.argv[1], encoding="utf-8"))
os.makedirs(sys.argv[2], exist_ok=True)
for i, ln in enumerate(lines):
    x, sr = k.create(ln["text"].replace("GLOWING", "glowing").replace("NEON", "neon").replace("MARKER", "marker"),
                     voice=ln["voice"], speed=ln.get("speed", 1.0), lang="en-us")
    sf.write(os.path.join(sys.argv[2], f"{i:02d}.wav"), np.asarray(x, np.float32), sr)
    print(i, ln["who"], round(len(x) / sr, 2))
