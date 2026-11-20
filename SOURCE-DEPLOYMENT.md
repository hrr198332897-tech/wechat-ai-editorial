# 三个情报采集方案的部署评估

2026 年 11 月 20 日。以 AIHOT、AI Topic Radar 和 ai-news-brief 为本轮评估对象。每个候选用公开产物或源码做了隔离验证。当前选题数据库继续使用已验证的官方信源，避免将多个排行榜结果混为一条证据。

| 项目 | 已验证 | 正式部署前置条件 | 部署判断 |
| --- | --- | --- | --- |
| [AIHOT](https://github.com/KKKKhazix/AIHOT) | 最新日报接口返回 4 个栏目、7 条快讯和 3 条重点。离线解析 Compose 清单，确认数据库、初始化、API、worker 和 Web 五项核心服务 | Linux 或启用 WSL2/Docker 的环境，PostgreSQL，用户确认选用的模型与 API Key。若使用官方托管数据，单独核对其内容使用范围 | **优先做隔离部署。** 用官方一手和媒体各取一组已知事件，检验能否区分重复报道、后续进展和不同事件。首期把它作为发现线索和分组对照，再回到原始来源。 [官方部署说明](https://github.com/KKKKhazix/AIHOT/blob/main/docs/deploy.md) · [公开使用规则](https://aihot.news/terms) |
| [AI Topic Radar](https://github.com/Conradgui/AI-TREND-RADAR) | 11 月 20 日公开选题池包含 51 个候选、13 项信源状态，候选有评分、证据、理由和编辑切口。仓库包含日报与测试命令 | Node.js、pnpm、模型配置。GitHub 许可证接口返回 404，仓库中未核实明确许可 | 先对照公开报告的证据与选题卡结构。取得作者许可或发现明确授权后，再确定是否部署或复用代码。 [公开选题池](https://github.com/Conradgui/AI-TREND-RADAR/blob/main/digests/2026-11-20/topic-pool.json) |
| [ai-news-brief](https://github.com/frankzch/ai-news-brief) | 中文站可访问。单独测试其上游去重函数，确认对 PostgreSQL 有符号 64 位指纹 `1` 与 `-2` 返回汉明距离 1，按无符号位模式实际应为 64。该边界会误判一部分跨符号的指纹 | PostgreSQL 和 pgvector，摘要及嵌入服务的访问配置。部署前对去重函数做固定 64 位宽回归测试 | 第二顺位。先修正或隔离该逻辑，再用中英文同事件、同型号不同发布等样例衡量语义去重效果。 [去重源码](https://github.com/frankzch/ai-news-brief/blob/main/src/lsh_dedup.py) · [InBrief 中文站](https://inbrief.info/zh/) |

## 当前环境与验收方式

本机已有 Python 3.13、Node.js 24 和 pnpm。检测时没有可用的 Docker CLI、WSL 发行版或 PostgreSQL 服务。三套候选目前完成了只读及离线组件评估。涉及服务安装、数据库和外部模型时，需要先确认运行位置、模型提供方和凭证再执行。

试部署时使用独立存储。各项目处理同一批人工标注事件，记录新增的独家一手出处、误合并、漏合并、故障情况以及每轮耗时和模型费用。先看是否给公众号选题增加有效来源，再决定是否长期接入。运营使用时仍以原始公告、技术资料和人工审核为准。
