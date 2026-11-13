import unittest
from datetime import datetime, timezone

import tracker


def item(vid, views, published="2026-11-10T12:00:00Z", duration="PT5M"):
    return {
        "id": vid,
        "snippet": {"title": f"Відео {vid}", "channelTitle": "Канал", "publishedAt": published},
        "statistics": {"viewCount": str(views), "likeCount": "10", "commentCount": "5"},
        "contentDetails": {"duration": duration},
    }


NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


class TrackerTest(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(tracker.parse_duration("PT1H2M3S"), 3723)
        self.assertEqual(tracker.parse_duration("PT45S"), 45)
        self.assertEqual(tracker.parse_duration("P1DT1S"), 86401)
        self.assertEqual(tracker.parse_duration(""), 0)

    def test_record(self):
        r = tracker.to_record(item("a", 2400), NOW, ["q"])
        self.assertEqual(r["views_per_hour"], 100.0)
        self.assertEqual(r["engagement"], 0.62)
        self.assertFalse(r["is_short"])
        self.assertTrue(tracker.to_record(item("b", 1, duration="PT50S"), NOW, ["q"])["is_short"])

    def test_growth(self):
        recs = [tracker.to_record(item("a", 3000), NOW, ["q"]),
                tracker.to_record(item("new", 50), NOW, ["q"])]
        prev = {"taken_at": "2026-11-11T10:00:00+00:00", "videos": [{"id": "a", "views": 2000}]}
        tracker.add_growth(recs, prev, NOW)
        self.assertEqual(recs[0]["growth_per_hour"], 500.0)
        self.assertNotIn("growth_per_hour", recs[1])
        self.assertEqual(tracker.score(recs[0]), 500.0)

    def test_report(self):
        recs = [tracker.to_record(item("a", 3000), NOW, ["q1"]),
                tracker.to_record(item("s", 900, duration="PT30S"), NOW, ["q2"])]
        cfg = {"region": "UA", "days": 7}
        md = tracker.render_report(recs, cfg, NOW, 10, has_prev=False)
        self.assertIn("youtu.be/a", md)
        self.assertIn("Shorts", md)
        self.assertIn("q2", md)


if __name__ == "__main__":
    unittest.main()
