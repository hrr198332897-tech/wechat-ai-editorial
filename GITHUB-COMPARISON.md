# 与这套公众号情报工作流相近的 GitHub 项目

2026 年 11 月 20 日，在验收报告完成后检索 GitHub。以 AI 信源覆盖、事件去重、证据可追溯、中文编辑、人审门槛和秀米交接为比较条件。维护日期采用 GitHub 的最近推送时间并换算为北京时间，许可证核对 GitHub 元数据或仓库文件。

有相近项目。**AIHOT** 与情报监测和事件归并最接近，**WeWrite** 与公众号编辑最接近，**AI Topic Radar** 与中文选题池最接近。这批候选中未找到经验证同时覆盖一手核查、决定是否写的人工关卡和秀米交接的单一项目。

| 候选 | 相似点和可复用处 | 架构、许可与维护 | 实际核对与采用判断 |
| --- | --- | --- | --- |
| [AIHOT](https://github.com/KKKKhazix/AIHOT) | 官方、准官方、媒体分级，多源事件归并、相关后续、修正和报告。值得参考「同一事件、后续进展、不同事件」的判定及二次复核 | MIT。TypeScript、Node.js 24、PostgreSQL、API/worker/web、Docker Compose 与模型服务。最近推送 11 月 20 日 | 实测线上站点、OpenAPI 和最新日报 JSON 可读，仓库包含事件归并和编辑目录。本机未部署五容器方案。第一阶段保留本地方案，未来可借鉴归并方法。线上 API 的内容使用条款独立于代码许可证，外部商业使用或公开批量复制需要按其条款另行处理。[部署指南](https://github.com/KKKKhazix/AIHOT/blob/main/docs/deploy.md) · [事件源码](https://github.com/KKKKhazix/AIHOT/tree/main/packages/backend/src/events) · [线上用法](https://aihot.news/agent) |
| [WeWrite](https://github.com/imraywang/wewrite) | 公众号选题、主张与证据关联、中文出稿、审稿和本地 HTML。写作简报和审稿量规可用于提高标题与首屏质量 | MIT。Python CLI 加可单独使用的 Agent Skills，写作需要 Agent 会话。最近推送 11 月 16 日 | 读到实际的证据记录实现、审稿规范和样稿。写作资料可复用，公众号草稿接口需要授权，当前保留项目自己的批准与秀米文件交接。未安装或调用其草稿接口。[来源记录](https://github.com/imraywang/wewrite/blob/main/src/wewrite/sources.py) · [审稿规范](https://github.com/imraywang/wewrite/blob/main/skills/wewrite-review/SKILL.md) |
| [AI Topic Radar](https://github.com/Conradgui/AI-TREND-RADAR) | 从官方网站、GitHub、论文及社区生成带分数、行动和证据的中文选题池；适合对照信源等级和报告结构 | TypeScript、pnpm、LLM Key，可用 Actions。最近推送 11 月 20 日。未在当前仓库树发现明确许可文件，GitHub 也未识别许可证 | 实际读取 11 月 20 日的 `topic-pool.json`，包含候选、来源状态和告警。现阶段参考公开输出设计，代码复用有待许可确认。[当日样例](https://github.com/Conradgui/AI-TREND-RADAR/blob/main/digests/2026-11-20/topic-pool.json) |
| [ai-news-brief](https://github.com/frankzch/ai-news-brief) | 多源采集、重要性打分、双语摘要，SimHash 初筛与 pgvector 语义去重。适合在积累跨语言漏合并样例后对照 | MIT。Python、PostgreSQL/pgvector 与模型 Key。最近推送 10 月 12 日 | 实测 InBrief 中文站可打开，仓库有去重实现。自部署和共享内容库未验证。暂不为第一阶段增加数据库及模型依赖。[去重源码](https://github.com/frankzch/ai-news-brief/blob/main/src/lsh_dedup.py) · [运行站点](https://inbrief.info/zh/) |
| [ai-daily-news](https://github.com/Alionkissadeer/ai-daily-news) | RSS/X 采集，按 URL、标题、摘要三层去重，中文日报和 Markdown，支持将草稿交给公众号后台 | MIT。Python、LLM Key，可选 Docker 和 Actions。最近推送 5 月 5 日 | 核对代码目录、工作流和中文文档。具备日报先例，文档中的微信路径会在配置凭证后调用草稿接口，本地未执行。可参考发布器的可插拔边界。[中文说明](https://github.com/Alionkissadeer/ai-daily-news/blob/main/README.zh.md) |
| [ai-wechat-digest-mvp](https://github.com/SUCHA-main/ai-wechat-digest-mvp) | RSS、个人偏好、无密钥 Mock、Markdown、可选推送。适合对照最小化部署 | MIT。Node.js 22.5+、SQLite、Express，可选 Ollama。最近推送 7 月 16 日 | 核对 Mock 配置、摘要、数据库和推送模块。文档说明去重按 URL，跨报道归并和一手证据门槛需补做。未本地部署。[中文说明](https://github.com/SUCHA-main/ai-wechat-digest-mvp/blob/master/README_CN.md) |

## 对三条分工的结论

- **采集**。已通过验收的本地采集保持当前架构。下一批人工审过的重复样例可记录「同一事件」「后续进展」「不同事件」，再用 AIHOT 的分组路径做基准。采用新代码前先在隔离环境比对误合并率。
- **文字编辑**。先参考 WeWrite 的「读者问题 → 主张 → 一手证据 → 建议行动」，以及「准确、观点、有用、合声、好读」的审稿维度。实际标题可从已证实的功能切入，例如「Seedream 5.5 的 RGBA 输出，怎么接到后期合成？」。导语交代要验证的具体工作步骤，正文再回答适用条件和测试结果。
- **秀米**。采用已核实的官方 Markdown 入口和纯文本粘贴，保留 HTML 备选。WeWrite 的微信草稿链路与秀米的第三方回调分别属于不同交接方式，当前都没有接到运行流程。账号内兼容性验收见 [秀米交接说明](XIUMI.md)。
