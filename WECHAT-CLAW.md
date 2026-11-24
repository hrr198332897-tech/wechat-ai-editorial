# wechat-claw 本地部署

本机 Codex 安装名为 `wechat-mp-writer`。上游锁定在提交 `566d36c3caa9509d202934544d0171235a069239`。根目录许可证为 Apache 2.0，采用该许可证标识。安装后保留原始说明于 `docs/SKILL.upstream.md`，本机 `SKILL.md` 适配 Codex 的元数据和本项目的本地运行约定。17 份脚本、模板和参考资料逐文件核对，与原版本一致。[锁定源码](https://github.com/th3ee9ine/wechat-claw-skill/tree/566d36c3caa9509d202934544d0171235a069239)

输入为已审核的文章 JSON。项目的 WeWrite 和编辑准则负责选题、证据和正文。wechat-claw 校验标题、摘要和段落结构，并按模板生成 HTML 和配图计划。公众号视频、素材和秀米导入仍用项目的现有交接工具。

用项目 Python 运行，`<skill-directory>` 为本机的 `wechat-mp-writer` 目录。

```powershell
python -X utf8 <skill-directory>/scripts/run_pipeline.py article.json --output-dir build --dry-run
```

在 Windows 用 Python 3.13 执行 `deep-analysis` 样例通过。产物含 HTML 和补全的 JSON，账号相关 ID 均为空。上游外部生成、上传、建草稿和发布需要额外脚本，本项目按人工交接流程使用本地结果。上游的封面媒体 ID 警告只适用于账号草稿。
