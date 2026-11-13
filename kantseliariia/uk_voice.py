#!/usr/bin/env python3
"""Українська озвучка реплік (ukrainian-tts, ESPnet VITS). Запуск з ~/uktts-venv:
    ~/uktts-venv/bin/python kantseliariia/uk_voice.py kantseliariia/lines_uk.json kantseliariia/voice/raw
"""
import json, os, sys
from ukrainian_tts.tts import TTS, Stress

lines = json.load(open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
tts = TTS(device="cpu")
for i, ln in enumerate(lines):
    path = os.path.join(out, f"{i:02d}.wav")
    with open(path, mode="wb") as f:
        _, accented = tts.tts(ln["text"], ln["voice"], Stress.Dictionary.value, f)
    print(i, ln["who"], accented)
