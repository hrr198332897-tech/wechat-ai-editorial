import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from editorial import Item, Store, assess, canonical, matches, write_bundle
from sources import extract_feed, verify


NOW = datetime(2026, 11, 20, 9, tzinfo=timezone.utc)


def item(title, url, **overrides):
    fields = dict(
        source="Vendor", region="海外", kind="official", subject="",
        title=title, url=url, published=NOW.isoformat(),
        summary="A new model with a public API and multimodal input.",
    )
    fields.update(overrides)
    return Item(**fields)


class WorkflowTests(unittest.TestCase):
    def test_versions_and_distinct_events(self):
        a = item("Introducing Gemini 3.5 Flash", "https://example.com/a")
        b = item("Google releases Gemini 3.5 Flash", "https://news.example.org/b", kind="media")
        self.assertTrue(matches(a, b))
        self.assertFalse(matches(a, item("Introducing Gemini 3.5 Pro", "https://example.com/c")))
        self.assertFalse(matches(a, item("Gemini 3.5 Flash price cut", "https://example.com/p")))
        self.assertFalse(matches(
            item("Gemini 3.5 Flash now available in app", "https://example.com/app"),
            item("Gemini 3.5 Flash now available in API", "https://example.com/api"),
        ))
        self.assertFalse(matches(
            item("Introducing Qwen 3.5-9B", "https://example.com/9b"),
            item("Introducing Qwen 3.5-27B", "https://example.com/27b"),
        ))
        self.assertFalse(matches(
            item("Gemini 3.5 Flash launches native audio support", "https://example.com/audio"),
            item("Gemini 3.5 Flash launches new vision support", "https://example.com/vision"),
        ))
        self.assertFalse(matches(a, item("Introducing Gemini 3.5 Flash", "https://example.com/old",
                                        published=(NOW - timedelta(days=30)).isoformat())))
        self.assertEqual(canonical("https://EXAMPLE.com/a/?utm_source=test&id=2#x"),
                         "https://example.com/a?id=2")
        self.assertNotEqual(canonical("https://example.com/changelog#2026-11"),
                            canonical("https://example.com/changelog#2026-10"))
        self.assertNotEqual(canonical("https://example.com/model-release#202611:~:text=seedream"),
                            canonical("https://example.com/model-release#202611:~:text=seedance"))

    def test_releases_do_not_merge_across_products(self):
        a = item("v1.10.2", "https://github.com/org/one/releases/tag/v1.10.2",
                 kind="repository", subject="one")
        b = item("v1.10.2", "https://github.com/org/two/releases/tag/v1.10.2",
                 kind="repository", subject="two")
        self.assertFalse(matches(a, b))

    def test_evidence_must_match_and_media_cannot_promote_itself(self):
        a = item("Introducing Gemini 3.5 Flash", "https://example.com/a")
        headers = {"Content-Type": "text/html"}
        body = b"<html><title>Sign in</title><main><p>Sign in to continue.</p></main></html>"
        with patch("sources.fetch", return_value=(a.url, headers, body)):
            self.assertFalse(verify(a, ["example.com"])["matched"])
        body = b"<html><title>Introducing Gemini 3.5 Flash</title><main><p>Gemini 3.5 Flash is available via the API. The vendor reports it beats its predecessor in a benchmark.</p></main></html>"
        with patch("sources.fetch", return_value=(a.url, headers, body)):
            evidence = verify(a, ["example.com"])
        self.assertTrue(evidence["matched"])
        self.assertEqual(assess([(a, {})], NOW)["grade"], "D")
        card = assess([(a, evidence)], NOW)
        self.assertIn(card["grade"], "AB")
        self.assertIn("厂商", card["claims"])
        media = item(a.title, a.url, kind="media")
        self.assertEqual(assess([(media, evidence)], NOW)["grade"], "D")

    def test_atom_keeps_published_date_and_resolves_relative_url(self):
        raw = b"""<feed xmlns="http://www.w3.org/2005/Atom"><title>Tool</title>
        <entry><id>1</id><title>v1.2.0</title><link href="/r/1"/>
        <published>2026-11-19T08:00:00Z</published><updated>2026-11-20T08:00:00Z</updated>
        <summary>API support added.</summary></entry></feed>"""
        source = dict(name="Tool", region="国内", kind="repository", subject="Tool")
        result = extract_feed(source, "https://example.com/feed", {}, raw)
        self.assertEqual(result[0].url, "https://example.com/r/1")
        self.assertTrue(result[0].published.startswith("2026-11-19"))

    def test_public_named_model_release_can_rank_a_but_nightlies_stay_archived(self):
        a = item("Introducing Gemini 4 Neon", "https://example.com/neon",
                 summary="")
        ev = dict(matched=True, url=a.url, title=a.title, excerpt="Gemini 4 Neon is now available in the Gemini app.")
        self.assertEqual(assess([(a, ev)], NOW)["grade"], "A")
        b = item("Release v2.0.0-nightly", "https://github.com/org/tool/releases/tag/v2.0.0-nightly",
                 kind="repository", subject="Tool")
        self.assertEqual(assess([(b, ev | {"excerpt": "Adds a public API for local inference."})], NOW)["grade"], "C")

    def test_persistence_and_review_gate(self):
        a = item("Introducing Gemini 3.5 Flash", "https://example.com/a")
        b = item("Google releases Gemini 3.5 Flash", "https://news.example.org/b", kind="media")
        ev = dict(matched=True, url=a.url, title=a.title, excerpt="Gemini 3.5 Flash is available via the API.")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with Store(path / "db.sqlite") as db:
                batch = [(a, ev), (b, {})]
                db.save_run(NOW, batch, [])
                db.save_run(NOW, batch, [])
                entries = db.list()
                self.assertEqual(len(entries), 1)
                event = entries[0]["id"]
                self.assertEqual(len(db.get(event)["sources"]), 2)
                with self.assertRaises(ValueError):
                    write_bundle(db.get(event), path / "exports")
                db.review(event, "approved", "核对了原始公告")
                result = write_bundle(db.get(event), path / "exports")
                self.assertTrue((result / "draft.html").is_file())
                self.assertIn(a.url, (result / "draft.txt").read_text(encoding="utf-8"))
                self.assertIn("核对了原始公告", json.loads((result / "card.json").read_text(encoding="utf-8"))["review_note"])
                db.save_run(NOW, [(a, {})], [])
                self.assertEqual(db.get(event)["status"], "approved")
                db.save_run(NOW, [(a, dict(ev, excerpt="Gemini rollout was withdrawn."))], [])
                self.assertEqual(db.get(event)["status"], "pending")
                with self.assertRaises(ValueError):
                    write_bundle(db.get(event), path / "exports")


if __name__ == "__main__":
    unittest.main()
