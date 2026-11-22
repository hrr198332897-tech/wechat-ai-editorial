"""Verify the optional Word export against Xiumi's import behavior."""

import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


@unittest.skipUnless(
    all(importlib.util.find_spec(name) for name in ("docx", "markdown", "bs4")),
    "Install requirements-xiumi.txt to verify Word export",
)
class XiumiHandoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.article = self.root / "article.md"
        self.output = self.root / "handoff"
        self.script = Path(__file__).with_name("xiumi_handoff.py")

    def export(self, *options):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(self.script), str(self.article),
             "--summary", "保存在秀米摘要栏", "--out", str(self.output), *options],
            capture_output=True, encoding="utf-8",
        )

    def test_word_import_projects_links_as_visible_text_and_embeds_image(self):
        from docx import Document

        cover = Path(__file__).parent / "examples" / "anthropic-ipo-2026-11-20" / "cover.png"
        (self.root / "cover.png").write_bytes(cover.read_bytes())
        self.article.write_text(
            "# 新稿标题\n\n![算力机房](cover.png)\n\n*概念图*\n\n"
            "## 关键数字\n\n正文有 **重点** 和 [招股书](https://example.org/filing)。\n",
            encoding="utf-8",
        )
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        docx = self.output / "xiumi-import.docx"
        doc = Document(docx)
        self.assertEqual(len(doc.inline_shapes), 1)
        self.assertIn("招股书（https://example.org/filing）", doc.paragraphs[-1].text)
        self.assertTrue(any(p.style.name == "Heading 2" for p in doc.paragraphs))
        self.assertNotIn("新稿标题", "\n".join(p.text for p in doc.paragraphs))
        self.assertEqual(
            (self.output / "title-summary.txt").read_text(encoding="utf-8").splitlines(),
            ["新稿标题", "", "保存在秀米摘要栏"],
        )
        with ZipFile(docx) as archive:
            self.assertIn("算力机房", archive.read("word/document.xml").decode("utf-8"))

    def test_missing_image_rejects_export_before_writing_artifacts(self):
        self.article.write_text("# 新稿标题\n\n![配图](missing.png)\n", encoding="utf-8")
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("找不到正文图片", result.stderr)
        self.assertFalse(self.output.exists())

    def test_batch_html_uses_xiumi_hosted_assets_only(self):
        from bs4 import BeautifulSoup

        cover = Path(__file__).parent / "examples" / "anthropic-ipo-2026-11-20" / "cover.png"
        (self.root / "cover.png").write_bytes(cover.read_bytes())
        self.article.write_text(
            "# 新稿标题\n\n![机房](cover.png)\n\n## 算力账单\n\n[原文](https://example.org/filing)\n",
            encoding="utf-8",
        )
        mapping = self.root / "image-urls.json"
        hosted = "https://img.xiumi.us/sample/cover.png"
        mapping.write_text(json.dumps({"cover.png": hosted}), encoding="utf-8")
        result = self.export("--image-urls", str(mapping), "--author", "作者")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = BeautifulSoup((self.output / "xiumi-import.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(html.img["src"], hosted)
        self.assertEqual(html.a["href"], "https://example.org/filing")
        self.assertIn("style", html.h2.attrs)
        self.assertIsNone(html.h1)
        self.assertNotIn("data:", str(html))
        metadata = json.loads((self.output / "handoff.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["author"], "作者")
        self.assertEqual(metadata["images"][0]["source"], "cover.png")

    def test_batch_html_rejects_other_image_hosts(self):
        self.article.write_text("# 新稿标题\n\n![配图](cover.png)\n", encoding="utf-8")
        mapping = self.root / "image-urls.json"
        mapping.write_text('{"cover.png":"https://other.example/cover.png"}', encoding="utf-8")
        result = self.export("--image-urls", str(mapping))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("秀米图床", result.stderr)
        self.assertFalse(self.output.exists())
