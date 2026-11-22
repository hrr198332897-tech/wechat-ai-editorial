---
name: wechat-ai-workflow
description: 本项目的 AI 资讯公众号工作流，包含搜热点、核查原文、写出读者爱看的稿件、去 AI 腔审稿、配图、秀米交接和反馈复用。
---

# AI 资讯公众号工作流

从项目根目录执行。每篇稿用独立目录保存，正文以 Markdown 为准。先读 [编辑准则](references/editorial.md)。只做单个环节时可从已有、已核对的产物接续。完整流程按下表交接，写作是主要质量关，成稿通过审读后进入排版。

| 环节 | 调用 | 交付 |
| --- | --- | --- |
| 1. 搜热点和素材 | 按 `wewrite-topic` 用 `radar.py`、热榜和定向搜索找线索。按用户指定时间窗收录；没有另定时间窗的日常选题用北京时间最近三个自然日（含当天截至采集时）。同步找能说明差异的官方演示、原图和可对比数据。 | 带时间和原始链接的候选、用图候选。 |
| 1a. 提取、核查和选题 | 合并同一进展，回查官方公告、原始报告、模型卡或作者资料。提取实际变化、适用条件、可比基线，标出厂商宣称和待核信息。按读者能看见或用上的变化排序，先给用户 3 个候选，等用户选定 1 个再写。 | 3 张简短选题卡。每张交代发生了什么、为什么值得读、打算怎么写和用什么画面，并附一手来源。 |
| 2. 写读者愿意看下去的稿 | 按 [写作方法](references/editorial.md#写作方法) 建立 WeWrite 的任务书和主张表。使用用户指定的 `generate_article` 原始模板，按 `gzh-content-skill` 的 `write_style.md` 和 `writer.md` 匹配文风，将语气、结构和句式要求写入任务书，再按 `wewrite-write` 起稿。先选最能兑现的爆点，再用动作、场景和同口径数字推进。 | 中文初稿，首屏有具体变化，每节有新发现，内附独立事实记录。 |
| 2a. 起标题 | 用已核实的事实卡和初稿调用 [ai-title-generator](../ai-title-generator/SKILL.md) 的 A 档，选能让读者想点开、正文首屏也能兑现的角度。数字、范围和口径随标题一起核对。 | 主标题、摘要，备选按需交付。 |
| 2b. 去 AI 感和复核 | 按 [去 AI 感](references/editorial.md#去-ai-感) 逐段改正文，再按 `wewrite-review` 和本机 `wechat-article-pipeline` 的检查说明复核。用 `wewrite content-eval` 留审稿记录。 | 定稿及审稿记录，保留关键数据的来源与限定条件。 |
| 3. 配图 | 读 `wechat-article-pipeline/references/image-production.md` 并参考其图位规划。正文优先采用可用的官方原图、图表截图和原视频，紧邻素材标出处。封面按文章核心反差设计，缩到手机列表尺寸仍能看清。官方素材缺少所需画面时，再用原创图或经核对的数据图补足。 | 封面、必要的正文图和视频、图注、原始来源或生成记录。 |
| 4. 秀米交接 | 按根目录 [XIUMI.md](../../../XIUMI.md) 运行 `xiumi_handoff.py`。一次读取成稿和配图，按图清单批量上传，再将整篇内联 HTML 交给秀米官方导入。HTML 导入不可用时改用同批生成的 Word 包。 | 标题／摘要／作者、图片清单、整篇 HTML 及 Word 包。授权范围内保存并重开，核对图片、正文和手机预览。 |
| 5. 复盘与同步 | 读根目录 `EDITORIAL-HISTORY.md`。将明确反馈记入日志，将可复用规则更新到编辑准则，并与稿件或样例一起提交。 | 有日期、有案例、有验收依据的 Git 提交。 |

## 写作、标题和配图训练

- 用户选题后，以同一组核实材料交付一套练习稿。正文单独提供，标题给一条主标题和两个不同切入角度的备选。配图交付开篇封面和支撑正文的关键图，注明图位、图注和来源。概念图、官方演示画面和数据图各自标明性质。
- 收到反馈后，直接修改被点到的标题、段落或图，保留首稿与修订稿供比较。记录用户确认的偏好，写明适用场景，再纳入下一篇的编辑准则。

## 运行约定

- 人工批准后才写正式稿。用户明确指定题目并要求撰稿时，本次撰稿已获授权。若对应选题已在 SQLite，按实际授权记录审核。探索候选和演练继续隔离。文章发布由运营者人工完成。
- 下游 Skill 以本项目授权范围运行。默认交付本地稿件和预览。秀米账号保存、第三方草稿箱和平台操作各按用户的明确指示处理。
- WeWrite 版本、安装与主题见根目录 `WEWRITE.md`。其 `--mode draft` 路径用于本地编辑。交付时写明哪些工具确实运行、哪些仅使用了提示或规则。
- [generate_article 的原始提示模板](https://github.com/gzlliyu/generate_article/blob/ff6179856139d737732920bf88dd9e60170f8d9f/generate_article.py) 接收主题、读者、篇幅、大纲和资料。默认由 Codex 按模板写。运行上游 Python 另外需要可用的模型 API 凭据和授权。
- [ai-title-generator 锁定版本](https://github.com/HeyClioo/ai-title-generator/tree/301bffcf0cfa6171b66b30ab445d2624cda3d1d6) 为 MIT 许可的提示型 Skill，随仓库提供，无运行时依赖。
- [gzh-content-skill 锁定版本](https://github.com/songlitong521-oss/gzh-content-skill/tree/680f12c5033d3cced7a1a0b39c68df1f545f6af3) 提供 `write_style.md`（风格库）和 `writer.md`（撰文步骤）。写稿只需读这两份材料。排版有需要才运行本地排版代码。
- [wechat-article-pipeline v1.9.7 锁定版本](https://github.com/jhwreal/wechat-article-pipeline-skill/tree/71ca7086ef22f556e4bb22f31f6a5a5b58fccbcc/wechat-article-pipeline) 可按上游 README 安装 `wechat-article-pipeline/`。Windows 原生 Python 当前缺少其打包脚本导入的 `fcntl`。该环境用上游写作和视觉规范，HTML 交给已验证的 GZH 排版路径。报告实际采用的路径。
