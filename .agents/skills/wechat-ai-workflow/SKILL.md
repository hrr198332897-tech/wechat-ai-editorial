---
name: wechat-ai-workflow
description: 用于信号之外的 AI 资讯选题、核查、公众号成稿、配图、审稿、草稿交接及跨 Agent 接续。也适用于只改标题、正文或图片，或从已有稿件继续。
---

# 信号之外公众号工作流

每次新稿或续稿先调用 `$wechat-ai-workflow`。没有 Skill 发现功能时直接读本文件。动稿前依次打开 [执行手册](references/runbook.md#每篇执行顺序)、[编辑准则](references/editorial.md)、[写作训练](references/writing-training.md)和最新[编辑反馈](../../../EDITORIAL-HISTORY.md)。接续时再读当前稿件的 `run.md`、正文和核查记录。把本篇适用的偏好、用户已定的题目或路线、正在进行的阶段写入制作记录。

按执行手册顺序推进，依[各阶段反馈规则](references/runbook.md#各阶段怎样听取意见)落实用户意见。每篇验证至少一项实际改进。每轮已落实的反馈、修改和优化都执行 [GitHub 同步](references/runbook.md#每轮同步到-github)，完成后读回远端提交。

## 从用户要求选起点

- 用户要找今日热点时，先采集核查，给三张选题简卡，由用户选一条再写。默认范围是北京时间最近三个自然日，含当天截至采集时。
- 用户明确选题并要求写作时，在开稿检查中记录该题已选定，再进入事实核查。已有同一选题卡就读回。已有稿件时按稿件目录和进度记录续做。
- 单独改稿、起标题、换图、检查或交接时，只做指定环节及其必要核对。收到新反馈后在现稿落实，保留旧稿和版本记录。
- 用户要求自主训练写作、找准公众号定位或从范文学习时，从[定位与写作训练](references/writing-training.md)起步。用现有样稿做对照，记录取舍和一次换题材试写。

## 工具索引

- 选题与证据用 [wewrite-topic](../wewrite-topic/SKILL.md)、`radar.py` 和定向搜索。
- 正文用 [wewrite-write](../wewrite-write/SKILL.md)，结合[训练样本](references/training-patterns.md)、`generate_article` 和 `gzh-content-skill`。
- 标题用 [ai-title-generator](../ai-title-generator/SKILL.md) 的公众号档。验证版式时可用 [wechat-claw](../../../WECHAT-CLAW.md)。
- 终审用 [wewrite-review](../wewrite-review/SKILL.md) 和本机 `wechat-article-pipeline` 的审稿规范。交付按[微信或秀米路线](references/runbook.md#交接到微信或秀米)。

正文以稿件目录中的 `article.md` 为准。正文的一级标题在交接时作为独立字段，摘要、作者、封面、阅读原文也各自保留。运营者最终审看并发布。只有本次获得的授权才允许账号写入，自动化的最远步骤是创建或修改已明确指定的草稿。

## 工具来源与兼容

- WeWrite 固定 4.2.0。使用仓库虚拟环境和 [本地设置](../../../WEWRITE.md)。本地写作使用 `--mode draft --visual-mode none`，接续时绑定明确任务 ID。
- [generate_article 原始模板](https://github.com/gzlliyu/generate_article/blob/ff6179856139d737732920bf88dd9e60170f8d9f/generate_article.py) 由当前 Agent 按模板执行。运行上游 Python 涉及已授权的模型配置时才执行。
- [gzh-content-skill 锁定版](https://github.com/songlitong521-oss/gzh-content-skill/tree/680f12c5033d3cced7a1a0b39c68df1f545f6af3) 撰稿参考 `write_style.md`、`writer.md`。仓库内 [ai-title-generator](https://github.com/HeyClioo/ai-title-generator/tree/301bffcf0cfa6171b66b30ab445d2624cda3d1d6) 为 MIT 许可，无运行时依赖。
- [wechat-article-pipeline v1.9.7 锁定版](https://github.com/jhwreal/wechat-article-pipeline-skill/tree/71ca7086ef22f556e4bb22f31f6a5a5b58fccbcc/wechat-article-pipeline) 提供审核、配图和交付规范。原生 Windows 实测其上游打包脚本缺少 `fcntl`，微信富文本交接使用仓库的 `wechat_handoff.py`。
