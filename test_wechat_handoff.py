"""Check the portable clipboard package against the archived article assets."""

import base64
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec("wewrite"), "Install requirements-wewrite.txt")
class WeChatHandoffTests(unittest.TestCase):
    def setUp(self):
        from bs4 import BeautifulSoup

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.article = self.root / "article.md"
        self.output = self.root / "output"
        self.cover = self.root / "cover.png"
        repository = Path(__file__).resolve().parent
        asset = repository / "examples" / "anthropic-ipo-2026-11-20" / "cover.png"
        self.cover.write_bytes(asset.read_bytes())
        self.script = repository / "wechat_handoff.py"
        self.parse = BeautifulSoup

    def build(self):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(self.script), str(self.article),
             "--summary", "一句摘要", "--author", "信号之外", "--cover", "cover.png",
             "--source-url", "https://example.org/official", "--out", str(self.output)],
            capture_output=True, encoding="utf-8",
        )

    def test_body_clipboard_is_distinct_from_metadata_and_portable(self):
        self.article.write_text(
            "# 可编辑的标题\n\n一句正文。\n\n## 关键发现\n\n![图表](cover.png)\n",
            encoding="utf-8",
        )
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = self.output / "review.html"
        document = self.parse(preview.read_text(encoding="utf-8"), "html.parser")
        body = document.select_one("#body")
        self.assertIsNone(body.h1)
        self.assertEqual(body.h2.get_text(strip=True), "关键发现")
        self.assertIn("25px", body.p["style"])
        self.assertEqual(document.select_one("#source-url")["value"], "https://example.org/official")
        self.assertEqual(document.select_one("#author")["value"], "信号之外")
        for data in (body.img["src"], document.select_one("#download-cover")["href"]):
            self.assertEqual(base64.b64decode(data.split(",", 1)[1]), self.cover.read_bytes())
        receipt = json.loads((self.output / "handoff.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["article_sha256"], sha256(self.article.read_bytes()).hexdigest())
        self.assertEqual(receipt["preview_sha256"], sha256(preview.read_bytes()).hexdigest())
        self.assertEqual(receipt["images"], ["cover.png"])
        self.assertEqual(receipt["cover"], "cover.png")

    def test_remote_or_missing_body_images_fail_before_creating_package(self):
        for url in ("missing.png", "https://example.org/remote.png"):
            with self.subTest(url=url):
                self.article.write_text(f"# 选题\n\n![图表]({url})\n", encoding="utf-8")
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("图片", result.stderr)
                self.assertFalse(self.output.exists())

    def test_executable_markup_never_enters_preview(self):
        self.article.write_text(
            '# 选题\n\n<img src="cover.png" onerror="alert(1)">\n',
            encoding="utf-8",
        )
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("交互", result.stderr)
        self.assertFalse(self.output.exists())

    def test_fenced_code_preserves_hash_comments(self):
        self.article.write_text(
            "# 可编辑的标题\n\n```python\n# 保留注释\nprint(1)\n```\n",
            encoding="utf-8",
        )
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.parse((self.output / "review.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIn("# 保留注释", document.select_one("#body pre").get_text())

    def test_heading_cannot_be_empty_or_repeated(self):
        for text in ("# \n\n一句正文。\n", "# 题目\n\n# 第二个题目\n\n一句正文。\n"):
            with self.subTest(text=text):
                self.article.write_text(text, encoding="utf-8")
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("标题", result.stderr)
                self.assertFalse(self.output.exists())

    def test_chinese_image_path_is_used_without_added_spaces(self):
        (self.root / "图1.png").write_bytes(self.cover.read_bytes())
        self.article.write_text("# 标题\n\n![配图](图1.png)\n", encoding="utf-8")
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.output / "handoff.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["images"], ["图1.png"])
