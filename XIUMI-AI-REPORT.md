# 秀米 AI 接入搜索与实测

2026 年 11 月 20 日。按用户提供的 GitHub `xiumi` 主题搜索，按最近更新排序的页面本轮显示 16 个公开仓库。结合「AI 直接接入秀米」这条线索，重点核对了 MCP、Codex 草稿助手和 AI 排版导入插件。 [GitHub xiumi 主题页](https://github.com/topics/xiumi?o=desc&s=updated)

## GitHub 候选

| 候选 | 接入方式 | 本轮判断 |
| --- | --- | --- |
| [xiumi-connector](https://github.com/egg-0831/xiumi-connector) | MIT，Node.js CLI 和本地 MCP。AI 客户端可以直接调用模板及内容操作，账号操作使用秀米登录凭据。主题页显示 11 月 17 日更新 | **与「AI 可直接接入」最吻合。** 在隔离目录运行 3.1.0（提交 `ff77f310`）的 6 项 MCP 协议测试，全部通过，实际列出 34 个工具。项目使用社区维护的非官方接口。仅验证了本地协议，账号写入、跨版本稳定性和素材许可未实测。 |
| [ll-xiumi](https://github.com/zongmoseu/ll-xiumi) | AI Skill 读 Word、Markdown 或纯文本并生成导入 JSON，Chrome/Edge 插件在秀米登录后导入正文和图片。主题页显示 10 月 19 日更新 | **如果记得的是「AI 排完版直接喂给秀米」，这项最像。** 项目说明导入核心来自 CC0 上游，仓库整体许可尚未核实。读取了实现说明，未安装浏览器扩展。 |
| [xiumi-codex](https://github.com/ppepperkok-hue/xiumi-codex) | MIT，Node.js CLI，复用经过人工登录的本地浏览器。支持改稿、传图、保存和重新读取，仓库说明没有发布命令。主题页显示 11 月 2 日更新 | 对草稿编辑最有针对性。需要受控浏览器，仓库记录的实测账号有会员权限。可作为后续对照，账号实测待授权。 |
| [xiumi-mcp](https://github.com/steven-jzt/xiumi-mcp) | MIT，TypeScript、Playwright/CDP，AI 通过 MCP 访问秀米模板及原生编辑模型。主题页显示 11 月 5 日更新 | 可以参考组件槽位和排版流程。依赖浏览器登录和前端内部结构，本轮只核对仓库文档。 |
| [xiumi-creator / xiumiagent](https://github.com/ZMJJKK123-hub/xiumi-creator) | Python 终端 Agent，调用 OpenAI 兼容模型，再通过本地 Edge 排版、插图和保存草稿 | 如果记得的是「直接配置 LLM 的终端程序」，这项最接近。需要模型服务配置和秀米登录，仓库整体许可尚未核实，本轮未安装或调用模型。 [PyPI 软件包](https://pypi.org/project/xiumiagent/) |

主题页里没有找到完全同名的「S秀米」。`ll-xiumi` 的两个字母是小写 L。若目标是 Codex 直接操作秀米，优先测试秀米域名提供的 MCP。

## 官方域名 MCP 验证

直接对 `https://xiumi.us/mcp` 发起未授权的 MCP 初始化，请求返回 **HTTP 401**，并提供 OAuth 受保护资源元数据地址。资源元数据和授权服务器元数据均返回 **HTTP 200**，可确认端点、授权码流程和 PKCE S256。公开页面和未授权请求不能验证该账号能调用的具体工具、权限、套餐限制或保存行为。GitHub 的 `xiumi-connector` 是另一套本地社区实现。 [秀米 MCP 资源元数据](https://xiumi.us/.well-known/oauth-protected-resource/mcp) · [秀米 OAuth 元数据](https://xiumi.us/.well-known/oauth-authorization-server) · [两套通道的社区说明](https://github.com/egg-0831/xiumi-connector/blob/main/references/official-mcp-and-ai-layout.md)

## 本轮实际运行

| 测试 | 结果 |
| --- | --- |
| 情报采集 | 用独立 SQLite 重跑最近 21 天。22 个信源中 18 个取得窗口内条目，52 条记录中 46 条通过一手页面匹配。合并两组重复后，共 50 个事件，A 级 5、B 级 12。正式选题库保持原审核状态。 |
| 秀米 Markdown | 在未登录的官方网页导入虚拟测试文件，并导入项目 Seedream 5.5 样稿。正文、中文段落与小标题可见。虚拟文件中的 Markdown 链接原样显示为文字，因此实际样稿改用可核查的明文 URL。 |
| 标题与摘要 | 导入 Markdown 后标题、摘要字段为空。分别填写真实样稿标题和摘要并读回，确认内容正确。 |
| 本地写作和预览 | 已部署的 WeWrite 可提供样稿正文、审稿记录和 HTML 预览。秀米交接目录把标题和摘要与正文分开，便于编辑。 |
| 云端保存和公众号同步 | 等账号与授权齐备后再做。先确认账号权限和 OAuth 工具，再建立一篇独立私有测试稿，重开核对内容，最后验证公众号草稿箱和手机预览。正式发送由运营者确认。 |

[秀米网页编辑器](https://xiumi.us/studio/v5/paper) · [可导入正文样稿](examples/topic-29/xiumi/body.md) · [标题与摘要](examples/topic-29/xiumi/title-summary.txt) · [WeWrite 预览](examples/topic-29/wewrite/preview.html)
