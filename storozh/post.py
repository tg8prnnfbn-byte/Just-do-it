#!/usr/bin/env python3
"""Збирає кадри Blender у відео 1080x1920 30 fps: апскейл, легкий нічний серпанок, теплі світла / холодні тіні,
плівкове зерно, віньєтка. Звук (якщо є) домішується.

    python3 storozh/post.py storozh/out/frames storozh/out/mix.wav storozh/storozh-v1.mp4
"""
import subprocess
import sys
from pathlib import Path

frames, audio, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
vf = ("scale=1080:1920:flags=lanczos,"
      "colorbalance=rs=-0.03:bs=0.05:rh=0.04:bh=-0.03,"
      "eq=contrast=1.06:saturation=1.08:gamma=1.04,"
      "noise=alls=7:allf=t,"
      "vignette=angle=0.55")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-start_number", "0", "-i", str(frames / "f_%04d.png")]
if Path(audio).exists():
    cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print("Готово:", out)
