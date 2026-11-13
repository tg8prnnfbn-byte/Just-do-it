#!/usr/bin/env python3
"""Вертикальна версія проби v2 для YouTube Shorts (1080x1920, 9:16).

Розкладка: розмитий фон із того самого кадру, кадр плівки 4:3 посередині,
хук угорі, великі субтитри під кадром (вище за зону кнопок Shorts).

    python3 ekstrene/shorts.py /шлях/до/ne-vidpovidai-elevenlabs.mp3 ekstrene/shorts-kaseta-1.mp4
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proba2 as p2  # noqa: E402
import style_frames as sf  # noqa: E402

VW, VH = 1080, 1920
FW, FH = 1080, 810          # кадр 4:3
FY = 470                    # верх кадру
SUB_Y = FY + FH + 70        # субтитри під кадром


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    lines.append(cur)
    return lines


def compose(t, A):
    fr = p2.frame_at(t, A, subs=False)
    # фон: той самий кадр, збільшений, розмитий і темний
    small = fr.resize((180, 135)).filter(ImageFilter.GaussianBlur(4))
    bg = small.resize((int(VH * 4 / 3), VH)).crop(((int(VH * 4 / 3) - VW) // 2, 0, (int(VH * 4 / 3) + VW) // 2, VH))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.65)
    bg.paste(fr.resize((FW, FH)), (0, FY))
    d = ImageDraw.Draw(bg)

    # хук угорі
    tag = "ЗНАЙДЕНИЙ ЗАПИС · 1987"
    f_tag = sf.font(40)
    tw = d.textlength(tag, font=f_tag)
    d.rectangle(((VW - tw) / 2 - 20, 150, (VW + tw) / 2 + 20, 210), fill=sf.ALERT_RED)
    d.text(((VW - tw) / 2, 157), tag, font=f_tag, fill=(255, 255, 255))
    f_hook = sf.font(72)
    for i, ln in enumerate(["НЕ ВІДПОВІДАЙ,", "ЯКЩО КЛИЧУТЬ З ЛІСУ"]):
        w = d.textlength(ln, font=f_hook)
        d.text(((VW - w) / 2, 250 + i * 92), ln, font=f_hook, fill=sf.DIRTY_WHITE,
               stroke_width=4, stroke_fill=(0, 0, 0))

    # субтитри
    name, _ = p2.scene_at(t)
    sub = p2.current_sub(t)
    if sub and name not in ("snow", "end"):
        f = sf.font(62)
        y = SUB_Y
        for ln in wrap(d, sub, f, VW - 120):
            w = d.textlength(ln, font=f)
            d.text(((VW - w) / 2, y), ln, font=f, fill=(250, 246, 225), stroke_width=6, stroke_fill=(0, 0, 0))
            y += 80
    return bg


def main():
    voice_mp3, out = sys.argv[1], Path(sys.argv[2])
    A = p2.make_assets()
    with tempfile.TemporaryDirectory() as tmp:
        v, a = Path(tmp) / "v.mp4", Path(tmp) / "a.wav"
        p2.build_audio(voice_mp3, a)
        p2.write_video(v, (VW, VH), lambda t: compose(t, A), crf=27)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-i", str(a),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    print("Готово:", out)


if __name__ == "__main__":
    main()
