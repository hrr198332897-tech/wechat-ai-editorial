import unittest

from models import Item
from writing import build_copy


def example(title, *, source="示例实验室", kind="official", summary=""):
    return Item(source, "海外", kind, "", title, "https://example.com/update", "2026-11-20", summary)


class WritingTests(unittest.TestCase):
    def test_verified_features_give_a_specific_headline_and_opening(self):
        copy = build_copy(
            example("Introducing Model X2"),
            {"matched": True, "excerpt": "Model X2 adds support for transparent PNG output via the API."},
            "模型发布", "Model X2",
        )
        self.assertIn("透明 PNG", copy["headline"])
        self.assertIn("透明 PNG", copy["draft"][0][1])
        self.assertIn("透明 PNG", copy["change"])
        self.assertIn("列为本次新增", copy["comparison"])
        self.assertEqual(set(copy["takeaways"]), {"开发者", "企业", "普通用户"})
        self.assertEqual(len(set(copy["takeaways"].values())), 3)
        self.assertIn("核实", " ".join(copy["image_sources"]))

    def test_promise_and_hype_do_not_turn_into_title_facts(self):
        copy = build_copy(
            example("Revolutionary Model X2"),
            {"matched": True, "excerpt": "The upcoming API will support transparent PNG. It is the world's best model."},
            "模型发布", "Model X2",
        )
        self.assertNotIn("透明 PNG", copy["headline"])
        self.assertNotIn("world's best", copy["headline"])
        self.assertIn("前版", copy["comparison"])

    def test_unverified_excerpt_cannot_enter_public_facing_copy(self):
        copy = build_copy(
            example("Model X2", summary="Model X2 adds support for native transparent PNG."),
            {"matched": False, "excerpt": "Model X2 adds support for native transparent PNG."},
            "模型发布", "Model X2",
        )
        self.assertNotIn("透明 PNG", copy["headline"])
        self.assertNotIn("transparent PNG", str(copy["draft"]))
        self.assertIn("待核实", copy["abstract"])

    def test_research_headline_and_draft_keep_reported_results_attributed(self):
        copy = build_copy(
            example("Memory-efficient image models", kind="research"),
            {"matched": True, "excerpt": "We propose an attention method that uses less memory on our benchmark."},
            "技术研究", "图像模型",
        )
        self.assertIn("实验", copy["headline"])
        self.assertIn("作者", " ".join(p for _, p in copy["draft"]))
        self.assertNotIn("更省", copy["headline"])

    def test_market_share_is_not_open_weights_and_tool_releases_have_versions(self):
        article = example("v2.1.0", kind="repository")
        copy = build_copy(
            article, {"matched": True, "excerpt": "The release updates pricing. It has no open weights."},
            "工具更新", "MyTool", "升级前检查现有脚本",
        )
        self.assertIn("v2.1.0", copy["headline"])
        self.assertNotIn("权重可下载", copy["change"])
        self.assertIn("升级前检查现有脚本", copy["editor_note"])
        self.assertNotIn("升级前检查现有脚本", str(copy["draft"]))

    def test_review_card_has_previous_release_comparison_without_a_draft(self):
        copy = build_copy(
            example("v2.1.0", kind="repository"),
            {
                "matched": True,
                "excerpt": "The new version adds tool calling through a public API.",
                "previous": {"title": "v2.0.0", "url": "https://example.com/update/2.0.0"},
            },
            "工具更新", "MyTool", include_draft=False,
        )
        self.assertIn("v2.0.0", copy["comparison"])
        self.assertEqual(copy["draft"], [])
        self.assertEqual(copy["impact"], copy["takeaways"])

    def test_media_excerpt_cannot_appear_as_a_primary_observation(self):
        copy = build_copy(
            example("Model X2", kind="media"),
            {"matched": True, "excerpt": "Model X2 adds support for native transparent PNG."},
            "模型发布", "Model X2",
        )
        self.assertNotIn("透明 PNG", copy["headline"])
        self.assertIn("待核实", copy["abstract"])

    def test_chinese_release_uses_documented_change_and_not_marketing(self):
        copy = build_copy(
            example("图像模型版本更新"),
            {"matched": True, "excerpt": "新增原生 RGBA 图片输出。图像创作能力全面领先。"},
            "模型发布", "图像模型",
        )
        self.assertIn("RGBA", copy["headline"])
        self.assertIn("本次新增", copy["comparison"])
        self.assertNotIn("全面领先", copy["headline"])


if __name__ == "__main__":
    unittest.main()
