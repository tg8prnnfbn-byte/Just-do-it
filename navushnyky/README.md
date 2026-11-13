# «The Kitchen Headphones» — мультяшний шортс за скілом cartoon-3d-short

Історія Натаніеля Болдвіна, який у 1910 році зібрав перші сучасні навушники на кухні.
Факти й текст: `../scripts/navushnyky-short.md`.

| Файл | Що робить |
|---|---|
| `script_en.txt` | Текст озвучки (по реченню на рядок, числа словами) |
| `voice.py` | Голос Kokoro `am_adam` → `voice/voice.wav` + тайминги `lines.json`, `words.json` |
| `toon.py` | Персонажі: бобові голови, сливовий контур, руки-палички, 9 виразів, пози |
| `sets.py` | 13 локацій: кухня (день/вечір), Юта з храмом, храм усередині, лист, флот, радіорубка, фабрика, цех, весілля, суд, багатство, графік |
| `film.py` | План кадрів, камера, ефекти, рендер 1080x1920 30 fps |
| `audio/soundtrack.py` | Музика, ефекти, зведення −14 LUFS (`dsp.py`, `instruments.py` — зі скіла, MIT) |

## Збирання
```bash
~/kokoro-venv/bin/python navushnyky/voice.py navushnyky/script_en.txt navushnyky/voice
python3 navushnyky/film.py navushnyky/out/video_silent.mp4          # ~10 хв
python3 navushnyky/film.py navushnyky/out/x.mp4 --stills 1,7,26      # окремі кадри для перевірки
python3 navushnyky/audio/soundtrack.py navushnyky/out/mix.wav
ffmpeg -i navushnyky/out/video_silent.mp4 -i navushnyky/out/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k navushnyky/out/navushnyky-v1.mp4
```

## Відмінності від оригінального скіла
- Замість three.js/Remotion усе малюється в 2D (PIL): у хмарному контейнері немає відеокарти,
  а 3D-моделі Kenney недоступні. Правила вигляду (кольори, контури, камера, темп) взяті зі скіла.
- Тайминги слів наближені (faster-whisper недоступний): тривалість речення ділиться за довжиною слів.
- Без субтитрів, як вимагає скіл.
