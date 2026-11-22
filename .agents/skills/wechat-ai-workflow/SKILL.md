---
name: wechat-ai-workflow
description: 用于本项目的 AI 资讯公众号工作流，包括找热点、核查一手来源、写作、配图、秀米交接及把用户反馈写回仓库。
---

# AI 资讯公众号工作流

从项目根目录执行。每篇稿用独立目录保存，正文以 Markdown 为准。先读 [编辑准则](references/editorial.md)。只做单个环节时可从已有、已核对的产物接续。

| 环节 | 调用 | 交付 |
| --- | --- | --- |
| 1. 选题和搜素材 | 读同仓库 `.agents/skills/wewrite-topic/SKILL.md`。用 `radar.py` 找候选，回查官方发布、原始报告或作者资料。热点平台用于发现线索。同步寻找能说明差异的对比图、演示和可用原始素材。 | 一句话切入角度、选题卡、主张和出处、用图候选。 |
| 2. 写作和审稿 | 读 `wewrite-write` 与 `wewrite-review` 的项目内 Skill。写稿可使用用户点名的 `generate_article` 原始提示模板。另读本机 `wechat-article-pipeline` 的写作、检查说明，选用其适用环节。 | 中文标题、摘要、正文及独立核查记录。 |
| 2a. 起标题 | 有核对过的正文或事实卡后，调用同仓库的 [ai-title-generator](../ai-title-generator/SKILL.md) 的 A 档。科技热点可用其高密度数字与反差路径。留一个主标题，备选按需交付。 | 一条正文能兑现的标题；适用窗口和数字口径在首屏交代。 |
| 3. 配图 | 读 `wechat-article-pipeline/references/image-production.md` 并参考其图位规划。原创场景图用 Codex 的 `imagegen` Skill，数字用经核对的数据制图。先决定每个图位解释什么，再产图。 | 封面、必要的正文图、图注、素材来源或生成记录。 |
| 4. 秀米交接 | 按根目录 [XIUMI.md](../../../XIUMI.md) 运行 `xiumi_handoff.py`。一次读取成稿和配图，按图清单批量上传，再将整篇内联 HTML 交给秀米官方导入。HTML 导入不可用时改用同批生成的 Word 包。 | 标题／摘要／作者、图片清单、整篇 HTML 及 Word 包。授权范围内保存并重开，核对图片、正文和手机预览。 |
| 5. 复盘与同步 | 读根目录 `EDITORIAL-HISTORY.md`。将明确反馈记入日志，将可复用规则更新到编辑准则，并与稿件或样例一起提交。 | 有日期、有案例、有验收依据的 Git 提交。 |

## 运行约定

- 人工批准后才写正式稿。用户明确指定题目并要求撰稿时，本次撰稿已获授权。若对应选题已在 SQLite，按实际授权记录审核。探索候选和演练继续隔离。文章发布由运营者人工完成。
- 下游 Skill 以本项目授权范围运行。默认交付本地稿件和预览。秀米账号保存、第三方草稿箱和平台操作各按用户的明确指示处理。
- WeWrite 版本、安装与主题见根目录 `WEWRITE.md`。其 `--mode draft` 路径用于本地编辑。交付时写明哪些工具确实运行、哪些仅使用了提示或规则。
- [generate_article 的原始提示模板](https://github.com/gzlliyu/generate_article/blob/ff6179856139d737732920bf88dd9e60170f8d9f/generate_article.py) 接收主题、读者、篇幅、大纲和资料。默认由 Codex 按模板写。运行上游 Python 另外需要可用的模型 API 凭据和授权。
- [ai-title-generator 锁定版本](https://github.com/HeyClioo/ai-title-generator/tree/301bffcf0cfa6171b66b30ab445d2624cda3d1d6) 为 MIT 许可的提示型 Skill，随仓库提供，无运行时依赖。
- [gzh-content-skill 锁定版本](https://github.com/songlitong521-oss/gzh-content-skill/tree/680f12c5033d3cced7a1a0b39c68df1f545f6af3) 可下载固定提交。读对应文件后仅运行本地排版所需代码。浏览器登录、草稿和发布路径独立。
- [wechat-article-pipeline v1.9.7 锁定版本](https://github.com/jhwreal/wechat-article-pipeline-skill/tree/71ca7086ef22f556e4bb22f31f6a5a5b58fccbcc/wechat-article-pipeline) 可按上游 README 安装 `wechat-article-pipeline/`。Windows 原生 Python 当前缺少其打包脚本导入的 `fcntl`。该环境用上游写作和视觉规范，HTML 交给已验证的 GZH 排版路径。报告实际采用的路径。
