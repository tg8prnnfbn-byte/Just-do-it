#!/usr/bin/env python3
"""Трекер трендів YouTube.

Збирає свіжі відео за пошуковими запитами з config.json (і, за бажанням,
чарт популярного в регіоні), рахує швидкість набору переглядів і зберігає
знімок у data/. Якщо є попередній знімок, показує, наскільки відео виросло
між запусками. Звіт пишеться в reports/latest.md.

Запуск:
    YOUTUBE_API_KEY=... python3 trends/tracker.py
    python3 trends/tracker.py --config trends/config.json --top 30

Лише стандартна бібліотека Python, нічого встановлювати не треба.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3"
ROOT = Path(__file__).resolve().parent
SHORTS_MAX_SECONDS = 180


# ---------- API ----------

def api_get(endpoint: str, params: dict, key: str) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(f"{API}/{endpoint}?{query}")
    # Ключ у заголовку, а не в URL: так він не потрапляє в логи.
    req.add_header("X-Goog-Api-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:300]
        raise SystemExit(f"Помилка YouTube API ({e.code}) на {endpoint}: {msg}")


def search_ids(query: str, cfg: dict, key: str, now: datetime) -> list[str]:
    published_after = (now - timedelta(days=cfg["days"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = api_get("search", {
        "part": "id",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": published_after,
        "regionCode": cfg.get("region"),
        "relevanceLanguage": cfg.get("language"),
        "maxResults": cfg.get("max_results_per_query", 25),
    }, key)
    return [it["id"]["videoId"] for it in data.get("items", []) if it.get("id", {}).get("videoId")]


def popular_ids(cfg: dict, key: str) -> list[str]:
    data = api_get("videos", {
        "part": "id",
        "chart": "mostPopular",
        "regionCode": cfg.get("region"),
        "maxResults": 50,
    }, key)
    return [it["id"] for it in data.get("items", [])]


def fetch_videos(ids: list[str], key: str) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        data = api_get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(ids[i:i + 50]),
        }, key)
        out.extend(data.get("items", []))
    return out


# ---------- розрахунки ----------

def parse_duration(iso: str) -> int:
    """PT1H2M3S -> 3723 секунди."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def to_record(item: dict, now: datetime, sources: list[str]) -> dict:
    sn, st, cd = item["snippet"], item.get("statistics", {}), item.get("contentDetails", {})
    published = parse_time(sn["publishedAt"])
    hours = max((now - published).total_seconds() / 3600, 1.0)
    views = int(st.get("viewCount", 0))
    likes = int(st.get("likeCount", 0))
    comments = int(st.get("commentCount", 0))
    duration = parse_duration(cd.get("duration", ""))
    return {
        "id": item["id"],
        "title": sn["title"],
        "channel": sn["channelTitle"],
        "published": sn["publishedAt"],
        "duration": duration,
        "is_short": 0 < duration <= SHORTS_MAX_SECONDS,
        "views": views,
        "likes": likes,
        "comments": comments,
        "views_per_hour": round(views / hours, 1),
        "engagement": round((likes + comments) / views * 100, 2) if views else 0.0,
        "sources": sources,
    }


def add_growth(records: list[dict], prev: dict | None, now: datetime) -> None:
    """Приріст переглядів за годину між попереднім і поточним знімком."""
    if not prev:
        return
    prev_time = parse_time(prev["taken_at"])
    hours = max((now - prev_time).total_seconds() / 3600, 1 / 60)
    prev_views = {r["id"]: r["views"] for r in prev["videos"]}
    for r in records:
        if r["id"] in prev_views:
            r["growth_per_hour"] = round((r["views"] - prev_views[r["id"]]) / hours, 1)


def score(r: dict) -> float:
    """Головний показник: свіжа швидкість (якщо є), інакше середня з моменту публікації."""
    return r.get("growth_per_hour", r["views_per_hour"])


# ---------- знімки та звіт ----------

def latest_snapshot(data_dir: Path) -> dict | None:
    files = sorted(data_dir.glob("snapshot-*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def fmt_int(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", " ")


def render_report(records: list[dict], cfg: dict, now: datetime, top: int, has_prev: bool) -> str:
    lines = [
        "# Тренди YouTube",
        "",
        f"Оновлено: {now.strftime('%Y-%m-%d %H:%M')} UTC · регіон {cfg.get('region')} · "
        f"відео за останні {cfg['days']} дн.",
        "",
    ]
    if not has_prev:
        lines += ["> Це перший знімок: швидкість рахується як середня з моменту публікації. "
                  "Запусти трекер ще раз пізніше, і з'явиться колонка «приріст/год».", ""]

    def table(title: str, rows: list[dict]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not rows:
            lines.extend(["_Немає відео._", ""])
            return
        head = "| # | Відео | Канал | Перегляди | Перегл./год |"
        sep = "|---|---|---|---:|---:|"
        if has_prev:
            head += " Приріст/год |"
            sep += "---:|"
        head += " Залученість | Звідки |"
        sep += "---:|---|"
        lines.extend([head, sep])
        for i, r in enumerate(rows, 1):
            title_md = r["title"].replace("|", "\\|")
            row = (f"| {i} | [{title_md}](https://youtu.be/{r['id']}) | {r['channel'].replace('|', '/')} "
                   f"| {fmt_int(r['views'])} | {fmt_int(r['views_per_hour'])} |")
            if has_prev:
                g = r.get("growth_per_hour")
                row += f" {fmt_int(g) if g is not None else 'нове'} |"
            row += f" {r['engagement']}% | {', '.join(r['sources'])} |"
            lines.append(row)
        lines.append("")

    ranked = sorted(records, key=score, reverse=True)
    table("🔥 Найшвидші довгі відео", [r for r in ranked if not r["is_short"]][:top])
    table("⚡ Найшвидші Shorts", [r for r in ranked if r["is_short"]][:top])

    # Підсумок по запитах: яка тема набирає найбільше
    lines += ["## 📈 Теми за швидкістю", "", "| Запит | Відео | Медіана перегл./год | Найкраще |",
              "|---|---:|---:|---|"]
    by_source: dict[str, list[dict]] = {}
    for r in records:
        for s in r["sources"]:
            by_source.setdefault(s, []).append(r)
    stats = []
    for s, rs in by_source.items():
        speeds = sorted(score(r) for r in rs)
        median = speeds[len(speeds) // 2]
        best = max(rs, key=score)
        stats.append((median, s, len(rs), best))
    for median, s, n, best in sorted(stats, reverse=True):
        lines.append(f"| {s} | {n} | {fmt_int(median)} | {best['title'][:60].replace('|', '/')} |")
    lines.append("")
    return "\n".join(lines)


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="Трекер трендів YouTube")
    ap.add_argument("--config", default=str(ROOT / "config.json"))
    ap.add_argument("--top", type=int, default=20, help="скільки відео показувати в кожній таблиці")
    args = ap.parse_args()

    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("Не задано YOUTUBE_API_KEY. Отримай ключ у Google Cloud Console "
              "(YouTube Data API v3) і запусти: YOUTUBE_API_KEY=... python3 trends/tracker.py",
              file=sys.stderr)
        return 1

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    data_dir, report_dir = ROOT / "data", ROOT / "reports"
    data_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    sources: dict[str, list[str]] = {}
    for q in cfg["queries"]:
        for vid in search_ids(q, cfg, key, now):
            sources.setdefault(vid, []).append(q)
    if cfg.get("popular_chart"):
        for vid in popular_ids(cfg, key):
            sources.setdefault(vid, []).append(f"популярне {cfg.get('region')}")

    records = [to_record(it, now, sources[it["id"]]) for it in fetch_videos(list(sources), key)]
    prev = latest_snapshot(data_dir)
    add_growth(records, prev, now)

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    snapshot = {"taken_at": now.isoformat(), "config": cfg, "videos": records}
    (data_dir / f"snapshot-{stamp}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    report = render_report(records, cfg, now, args.top, prev is not None)
    (report_dir / "latest.md").write_text(report, encoding="utf-8")

    print(f"Зібрано {len(records)} відео. Звіт: {report_dir / 'latest.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
