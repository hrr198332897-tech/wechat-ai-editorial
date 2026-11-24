# 公众号编辑

- 本项目的统一入口是 [wechat-ai-workflow](.agents/skills/wechat-ai-workflow/SKILL.md)。任何 Agent 从仓库根目录接手，先读入口，再按 [交接手册](.agents/skills/wechat-ai-workflow/references/runbook.md) 定位稿件目录和已验收的阶段。仅处理复盘时，读取对应案例、反馈记录和编辑准则。
- 使用 `radar.py` 查看选题与核查材料。在 SQLite 中确认选题为 `approved` 后，才能把实际选题交给 WeWrite 撰稿或审稿。验收演练用 `examples/` 中已有的隔离样稿。
- 使用项目的 `.venv`，将 `WEWRITE_HOME` 设置为项目目录下的 `data/wewrite`。按需要读取 `.agents/skills/wewrite-write/SKILL.md` 和 `.agents/skills/wewrite-review/SKILL.md`，用 `run start --mode draft --visual-mode none` 启动本地写作任务。
- 从 `card.json` 提取原始出处和已审核的证据。按具体主张判断核查状态。厂商声明注明归属，旧版差异、性能提升和实际体验需要相应证据。
- 使用项目本地的 `professional-clean` 预览主题覆盖。预览前确认自带的实测页脚已禁用，在 Markdown 中准确写明 AI 辅助程度和本篇的核查状态。迁移后的配置方式见 `WEWRITE.md`。
- 写作完成后默认交付公众号可复制图文和独立字段。按用户选择进入秀米，或在已有授权与官方接口配置时创建公众号草稿。最后由运营者在公众号编辑页核稿、预览和发布。只有收到相应指示才进入涉及外部账号、模型密钥或外部写入的操作。
- 新的采集项目先完成隔离评估，记录信源、误合并和一手出处。有关三个候选的验证和部署条件见 `SOURCE-DEPLOYMENT.md`。
