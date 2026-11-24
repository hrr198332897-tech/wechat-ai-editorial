# AI 全球情报与公众号选题工作流

这个工作流采集海内外 AI 一手来源，回查原文，合并重复事件，生成中文选题卡。选题批准后完成写作、审稿、配图和公众号交接，最后由运营者在公众号编辑页修改、预览和发布。

## 在 Codex 中调用

从私有 GitHub 仓库克隆项目后，在仓库根目录开启新对话。可以说「用 $wechat-ai-workflow 跑今天的公众号，从最近三个自然日找三个选题」，或「用 $wechat-ai-workflow 接手这份稿件，做到公众号终审交接」。其他 Agent 从同一目录读 `AGENTS.md`、工作流入口和该稿的继续记录，也能执行同一流程。 [流程入口](.agents/skills/wechat-ai-workflow/SKILL.md) · [交接手册](.agents/skills/wechat-ai-workflow/references/runbook.md) · [编辑准则](.agents/skills/wechat-ai-workflow/references/editorial.md) · [反馈与恢复](EDITORIAL-HISTORY.md)

可在本地从终稿重建 [英伟达公众号交接样例](examples/nvidia-2026-11-24/run.md)。秀米验收记录见 [Anthropic 制作记录](examples/anthropic-ipo-2026-11-20/production-notes.md)。

## 安装和首跑

需要 Python 3.11 或更高版本及可访问所配置信源的网络。Windows 下，在此文件所在的目录打开 PowerShell。

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -X utf8 radar.py run
```

以下命令用 `python` 表示虚拟环境中的 Python。你可以继续使用上面的完整路径，也可在已激活的虚拟环境中运行。macOS/Linux 上的虚拟环境解释器为 `.venv/bin/python`。

## 日常用法

| 操作 | 命令 |
|---|---|
| 手动采集，默认最近 21 天、每源最多 7 条 | `python -X utf8 radar.py run` |
| 查看采集结果、信源失败及条目数 | `python -X utf8 radar.py status` |
| 查看高价值选题 | `python -X utf8 radar.py list` |
| 只看国内待审选题 | `python -X utf8 radar.py list --region 国内 --status pending` |
| 查阅历史及 C、D 级记录 | `python -X utf8 radar.py list --grade all` |
| 查看选题卡及链接 | `python -X utf8 radar.py card 12` |
| 导出一张选题卡供审阅 | `python -X utf8 radar.py card 12 --out data/topic-12.md` |
| 标记继续调查 | `python -X utf8 radar.py review 12 research --note "需核对地区限制"` |
| 根据人工结论批准 | `python -X utf8 radar.py review 12 approved --note "已核对版本和访问条件"` |
| 导出获批选题 | `python -X utf8 radar.py export 12` |

把示例里的 `12` 换成列表中的选题 ID。每轮新出现或证据有实质变化的 A/B 级选题会写入 `data/reports/run-*.md`，可以直接打开文件检查标题、原文和待核项。审核状态还支持 `rejected` 和 `pending`。通过人工回查也可在审核备注中记录测试条件、现用价格、原始文档以及决定采用的标题角度。

## 等级和证据

- **A** 需要可匹配的一手证据、近期明确事件、具体技术或应用信号，且达到 26/30 分及重大进展规则。
- **B** 需要相同的来源门槛和具体信号，且达到 20/30 分。论文和仓库条目仍须看实验或可用性证据。
- **C** 保留已找到一手出处的普通信息、低信号发现和较旧记录。
- **D** 保存被过滤条目的诊断记录，便于排查采集和评分，提醒列表只显示 A/B。

卡片会显示六维分值、证据原文、核查时间、来源声明和待核项。评分是编辑优先级。厂商声明和论文作者结果保留原始归属，性能对比在核对同版本、同配置和同口径后才能下结论。一手页校验主要验证来源、标题与可用文本。

## 导出和公众号交接

批准后，`exports/topic-<ID>/` 包含选题卡 `card.md`、结构化证据 `card.json`、底稿 `draft.md`、`draft.txt`、浏览器预览 `draft.html`、内联样式片段 `xiumi-fragment.html` 以及配图建议和权利记录 `images.md`。

先读底稿、补齐待核项，再用本地 WeWrite 起稿和审稿。成稿及配图齐备后，`wechat_handoff.py` 生成自带图文的审稿页，可一次复制正文，标题、作者、摘要、原文链接与封面单独交接。官方接口已授权并配置时可创建公众号草稿，再回读确认。 [WeWrite 与公众号交接](WEWRITE.md)

选择秀米排版时，`xiumi_handoff.py` 生成元数据、图片清单、预览和图文 Word。有 HTML 导入权限的账号可批量传图后整篇导入。保存后重开核对正文和图片。 [秀米交接步骤](XIUMI.md)

## 信源和维护

- `sources.json` 是信源清单。新增来源前先核对官方归属、最新条目、页面抓取条件与响应内容，再记录 GitHub 先例。公开网页改版时先看 `status`，修正该源后重试。
- 需要扩大测试时间窗时使用 `run --days 45 --limit 10`。旧事件可以通过 `list --grade all` 查找。源的条目顺序、采集窗口和每源上限会影响覆盖。
- SQLite 数据默认在 `data/editorial.sqlite`。备份前先结束正在执行的命令。要做隔离测试，把 `--db other.sqlite` 放在子命令前，同时设置 `run --report-dir ...` 或 `export --out ...`。
- 要定时采集，可在 Windows 任务计划程序配置同一个绝对解释器和脚本路径，参数为 `-X utf8 <脚本路径> run`，通过本地报告读取结果。
- 使用 `python -X utf8 -m unittest -v` 运行本地回归测试。完整在线流程依赖实际信源网络。

延伸资料见 [架构与扩展](ARCHITECTURE.md)、[GitHub 开源调研](RESEARCH.md) 和 [采集项目部署评估](SOURCE-DEPLOYMENT.md)。
