# GitHub 开源先例调研

核对日期为 2026 年 11 月 20 日。先检查本机环境，再在 GitHub 搜索新闻聚合、RSS、去重、AI 摘要与自动化项目，并复核候选的源码文档和许可证。下表的活跃度日期是当时公开 GitHub 元数据中的最后推送时间，可能包含文档与依赖变更。部署评估以仓库文档为依据。实际运行的部分见下方验证记录。

| 模块 | 先例与维护状态 | 技术特点和部署取舍 | 第一阶段采用 |
| --- | --- | --- | --- |
| RSS 与 Atom | [feedparser](https://github.com/kurtmckee/feedparser)，[BSD 两条款式许可证](https://github.com/kurtmckee/feedparser/blob/main/LICENSE)，2026-11-02 有推送 | Python 库，解析多种订阅格式，提取条目日期、链接与摘要。作为 pip 依赖即可运行。 | 直接复用解析器。项目保留请求超时、取数错误和来源归属规则。 |
| 聚合与监测 | [FreshRSS](https://github.com/FreshRSS/FreshRSS)，AGPL-3.0，2026-11-20 有推送。 [RSSHub](https://github.com/DIYgod/RSSHub)，AGPL-3.0，2026-11-20 有推送。 | FreshRSS 是可自托管的 PHP 聚合阅读器，适合多人订阅和浏览。RSSHub 的 Node 服务能为没有原生订阅的站点生成 RSS，路由随上游网站改版而变化。两者独立部署会增加服务和数据管理。 | 官方 RSS 和 Atom 能直接读取。少量无 RSS 的公开页面用针对已核验来源的提取器；有更多经验证的 RSSHub 路由时可单独接入。 |
| 热点、AI 分析与工作流 | [TrendRadar](https://github.com/sansan0/TrendRadar)，GPL-3.0，2026-11-15 有推送。 | Python、SQLite、RSS、关键词筛选、可选 AI 分析与推送，适合热点扫描。项目提供本机、Docker、GitHub Actions 部署。以其 [Python 依赖清单](https://github.com/sansan0/TrendRadar/blob/master/pyproject.toml) 和[架构文档](https://github.com/sansan0/TrendRadar/blob/master/README-EN.md)复核。 | 借鉴 RSS 配置、SQLite 持久化和按批次监控。人工审核、证据分层和稿件导出的业务逻辑由本项目自行实现。 |
| 官网公告与证据片段 | [Trafilatura](https://github.com/adbar/trafilatura)，当前 Apache-2.0；[Beautiful Soup 官方源码](https://git.launchpad.net/beautifulsoup/)，MIT，[官方文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)。 | Trafilatura 更适合广泛网页抽取，可输出正文及元数据。Beautiful Soup 使用 CSS 选择器，便于对固定公告页校对标题、日期和段落，改版时需要修改选择器。 | 先在 GitHub 核对 Trafilatura，再择 Beautiful Soup 解析当前少量已知页面。原文核查规则归项目维护。 |
| 事件去重 | [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)，MIT，2026-11-09 有推送。 [Sentence Transformers](https://github.com/huggingface/sentence-transformers)，框架 Apache-2.0，模型权重须分别核查。 | RapidFuzz 计算字符串相似度，单库可运行，适合标题与结构化线索。后者可做向量近邻并辅助跨语种匹配，有模型下载、语言效果和误合并调参成本。 | 复用 RapidFuzz，与规范链接、主体和版本、时间窗口共同判断。语义去重放到有中英标注样本后评估。 |
| 数据与审核 | [SQLite](https://github.com/sqlite/sqlite) 官方 GitHub 镜像，[公共领域](https://sqlite.org/copyright.html)。 | Python 自带 `sqlite3`，本机文件持久化，支持事务和索引，无需独立数据库服务。 | 复用数据库引擎。来源证据、事件关系、审核记录由本项目建模。 |
| 中文内容处理 | [Ollama](https://github.com/ollama/ollama)，MIT，2026-11-19 有推送。[结构化输出 API](https://github.com/ollama/ollama/blob/main/docs/api.md)支持请求方提供 JSON Schema。 | 可将公开证据交给本机模型生成中文候选内容，需要安装运行时、下载模型权重并验证机器资源、中文效果和证据对齐。运行时与模型许可分别核查。 | 本机未发现 Ollama。第一阶段用规则生成结构化中文写作底稿，不需要模型账号或密钥。未来的模型层需要能回溯原始证据。 |
| 调度 | [n8n](https://github.com/n8n-io/n8n)，2026-11-20 有推送，[Sustainable Use 和企业许可条款](https://github.com/n8n-io/n8n/blob/master/LICENSE.md)。[GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)支持手动与定时触发。 | n8n 提供图形化工作流与大量集成，需要管理运行服务，部分代码有使用限制。GitHub Actions 托管执行要求仓库与运行权限，SQLite 状态需另行持久化。 | 先使用本地手动命令。若后续需要定时采集，可用现有 [Windows 任务计划程序](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)调同一命令。审核和发布由人工完成。 |
| 公众号导出 | [doocs/md](https://github.com/doocs/md)，WTFPL，2026-11-18 有推送。 | Vue 应用将 Markdown 渲染成适合公众号复制的富文本，适用于复杂排版。秀米网页端的 Markdown、文本、HTML 入口详见[秀米验证记录](XIUMI.md)。 | 本项目自行生成轻量中间文件，把最终模板和视觉样式交给秀米。 |

## 已实际验证

- 在 Windows Python 3.13 虚拟环境中，feedparser 6.0.14 从样例 RSS 读出标题，Beautiful Soup 4.14.3 从样例 HTML 定位正文，RapidFuzz 3.14.6 为相同标题给出更高分，SQLite 3.50.4 通过事务内建表、写入和查询。
- 首轮 HTTP 探测中，OpenAI、Google DeepMind、NVIDIA、Hugging Face、arXiv、Claude Code、月之暗面 Kimi CLI 等公开 RSS/Atom 可访问。Qwen3 和 GLM-5 仓库的发布 Atom 当时返回 200 但没有条目，选择默认信源时需要核对内容和更新日期。具体采集适配器与验收批次以项目运行说明为准。
- 官方秀米编辑器实测可粘贴未保存的中文纯文本，确认了实际导入菜单、扩展名、清除粘贴格式开关以及 HTML 的等级 VIP 条件。账号登录后的文件导入、保存和公众号同步仍待验证。
- FreshRSS、RSSHub、TrendRadar、n8n、Trafilatura、Sentence Transformers 和 Ollama 的比较来自配置、项目文档及许可文件。候选工具未在本机另行部署。

当前方案复用订阅解析、网页解析、模糊匹配和事务数据库，围绕一手证据、中文选题评分、人工导出授权编写项目代码。调研中的产品级候选未覆盖这套审核要求与秀米交接，因此这部分采用本地实现。
