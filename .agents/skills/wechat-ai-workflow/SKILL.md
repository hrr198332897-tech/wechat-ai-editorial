---
name: wechat-ai-workflow
description: 用于信号之外的 AI 资讯选题、核查、公众号成稿、配图、审稿、草稿交接及跨 Agent 接续。也适用于只改标题、正文或图片，或从已有稿件继续。
---

# 信号之外公众号工作流

在仓库根目录调用 `$wechat-ai-workflow`。没有 Skill 发现功能的 Agent 直接读本文件，按相对路径打开所需模块。开始前读 [执行与交接](references/runbook.md)、[编辑准则](references/editorial.md) 和最新 [编辑反馈](../../../EDITORIAL-HISTORY.md)。所有步骤可由同一个 Agent 完成，也可按下表分工。

## 从用户要求选起点

- 用户要找今日热点时，先采集核查，给三张选题简卡，由用户选一条再写。默认范围是北京时间最近三个自然日，含当天截至采集时。
- 用户明确选题并要求写作时，从该题的事实核查开始，已有同一选题卡就读回并记录已获批准的范围。已有稿件时按稿件目录和进度记录续做。
- 单独改稿、起标题、换图、检查或交接时，只做指定环节及其必要核对。收到新反馈后在现稿落实，保留旧稿和版本记录。

## 环节与交付

| 环节 | 调用与动作 | 给下一步的材料 |
| --- | --- | --- |
| 采集、核查、选题 | [wewrite-topic](../wewrite-topic/SKILL.md)、`radar.py` 和定向搜索。合并同一事件，分清原始出处、厂商说法、编辑推断和未核信息，同步找官方素材。 | 三张简卡或指定题的事实卡、原始链接和素材候选。 |
| 写作 | 读 [写作和风格](references/editorial.md#写作方法) 与 [训练样本](references/training-patterns.md)。按 `generate_article` 建结构、`gzh-content-skill` 选文风、[wewrite-write](../wewrite-write/SKILL.md) 起稿。 | 读者与角度、主张和出处、中文初稿。 |
| 标题和审稿 | [ai-title-generator](../ai-title-generator/SKILL.md) 用公众号档，核对题面承诺与首屏。按 [wewrite-review](../wewrite-review/SKILL.md)、[去 AI 感](references/editorial.md#去-ai-感) 和本机 `wechat-article-pipeline` 的审稿规范实改。 | `article.md`、标题摘要、审稿报告、独立核查资料。 |
| 素材与版式 | 依编辑准则和 `wechat-article-pipeline/references/image-production.md` 做图位规划。优先用可用的官方图表及视频。需要本地结构校验时用 [wechat-claw](../../../WECHAT-CLAW.md)。 | 封面、正文图或视频、图注、有权使用的依据及素材顺序。 |
| 交接和验收 | 默认准备微信富文本审稿页。获得目标账号授权且接口已配置时可到官方草稿箱。用户选择秀米时走 [秀米交接](../../../XIUMI.md)。各路线按 [执行与交接](references/runbook.md#交接到微信或秀米) 验收。 | 自包含审稿页、原文链接、独立封面、交接清单，或对应账号的已回读草稿。 |
| 复盘和保存 | 记录反馈、实际执行的工具和验收证据。可复用规则写回编辑准则，阶段结果写入 [历史与恢复](../../../EDITORIAL-HISTORY.md)。 | 可独立接续的稿件目录及更新后的流程。 |

正文以稿件目录中的 `article.md` 为准。正文的一级标题在交接时作为独立字段，摘要、作者、封面、阅读原文也各自保留。运营者最终审看并发布。只有本次获得的授权才允许账号写入，自动化的最远步骤是创建或修改已明确指定的草稿。

## 工具来源与兼容

- WeWrite 固定 4.2.0。使用仓库虚拟环境和 [本地设置](../../../WEWRITE.md)。本地写作使用 `--mode draft --visual-mode none`，接续时绑定明确任务 ID。
- [generate_article 原始模板](https://github.com/gzlliyu/generate_article/blob/ff6179856139d737732920bf88dd9e60170f8d9f/generate_article.py) 由当前 Agent 按模板执行。运行上游 Python 涉及已授权的模型配置时才执行。
- [gzh-content-skill 锁定版](https://github.com/songlitong521-oss/gzh-content-skill/tree/680f12c5033d3cced7a1a0b39c68df1f545f6af3) 撰稿参考 `write_style.md`、`writer.md`。仓库内 [ai-title-generator](https://github.com/HeyClioo/ai-title-generator/tree/301bffcf0cfa6171b66b30ab445d2624cda3d1d6) 为 MIT 许可，无运行时依赖。
- [wechat-article-pipeline v1.9.7 锁定版](https://github.com/jhwreal/wechat-article-pipeline-skill/tree/71ca7086ef22f556e4bb22f31f6a5a5b58fccbcc/wechat-article-pipeline) 提供审核、配图和交付规范。原生 Windows 实测其上游打包脚本缺少 `fcntl`，微信富文本交接使用仓库的 `wechat_handoff.py`。
