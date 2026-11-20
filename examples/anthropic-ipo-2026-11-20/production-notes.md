# Anthropic 上市稿制作记录

- **选题**。运行 WeWrite 4.2.0 热点、公众号检索与 SEO 命令。公众号检索返回 15 条；这些材料提供话题线索。事实依据取自纳斯达克、SEC 和 Anthropic，逐项见[核查底稿](evidence.md)。
- **写作与审稿**。用 Codex 执笔，按 `generate_article` 的原始模板整理读者、问题、资料和大纲。WeWrite 走本地 `draft` 路径，登记一手资料、写作与审稿结果。按 `wechat-article-pipeline` 的写作与视觉说明安排图位和强调，Windows 原生 Python 上该 Skill 的工作台打包脚本缺少 `fcntl`，本例采用 GZH 的 CSS 组件生成[交接 HTML](layout.html)。Codex 完成编辑判断，WeWrite [审稿报告](review.json)用于记录。
- **配图**。用内置 ImageGen 生成 3:2 封面，提示词为「写实冷色数据中心走廊，暖色设备灯，尽头看板只显示 ANT 和 $83，画面清晰，无其他文字、品牌或行情图」。对生成图做了单次修订，移除被误加的行情线和网格。数据图按 SEC 最终招股书数值绘制，2025 与 2026 年均取截至 9 月 30 日的九个月。
- **排版与验收**。420 像素宽的[手机预览](mobile-preview.png)无横向溢出，两张图加载，末尾三条出处。将同一正文、标题和摘要置入秀米匿名画布，读回两张图和三条出处，留下[秀米截图](xiumi-editor.png)。匿名画布供演练，未云端保存。
