# WeWrite 本地写作部署

项目使用 PyPI 的 WeWrite 4.2.0 和同版本 GitHub 标签的写作、审稿与风格三个模块。CLI 位于本项目的 `.venv`，安装的技能位于 `.agents/skills/`。采用固定版本来保持 CLI 和技能的命令、状态文件一致。 [官方版本](https://github.com/imraywang/wewrite/releases/tag/v4.2.0) · [PyPI 软件包](https://pypi.org/project/wewrite/4.2.0/)

## 直接使用

在项目目录打开 PowerShell。

```powershell
$env:WEWRITE_HOME = Join-Path (Get-Location) 'data/wewrite'
$env:PYTHONUTF8 = '1'
& .\.venv\Scripts\wewrite.exe --version
```

在以本项目为工作目录的 Codex 对话中，可以直接说「用 WeWrite 写第 29 号已批准选题，提供标题、摘要、成稿和审稿记录，交给我在秀米排版」。把 29 换成已批准的正式选题 ID。Codex 会按本项目的操作说明读取 WeWrite 模块，用选题卡原始出处建立主张清单，撰稿后用 WeWrite 审稿，并输出本地文件。可按实际文章校准风格；目前使用任务导向的科技写作，优先说明可用条件、复测方法与证据边界。

独立生成本地 HTML 时，用下面的命令。秀米优先导入成稿 Markdown，HTML 可在浏览器预览。WeWrite 将标题作为单独字段输出，预览正文中的外部链接变成可核对的参考链接文字。

```powershell
& .\.venv\Scripts\wewrite.exe preview .\examples\topic-29\wewrite\article.md --output .\data\wewrite-preview.html --no-open
```

迁移到其他机器时，保留项目里的技能目录，用 Python 3.11+ 创建 `.venv`，运行该环境的 `python -m pip install -r requirements-wewrite.txt`。写作任务的输入、证据和审稿状态存放在 `data/wewrite`，可按需要备份。 [秀米交接说明](XIUMI.md)

## 迁移后还原本地预览设置

上游默认页脚声称作者做过实测。本项目在专用状态目录用同名主题覆盖该页脚，正文按实际核查情况写明 AI 辅助和证据状态。首次迁移时执行一次。

```powershell
$env:WEWRITE_HOME = Join-Path (Get-Location) 'data/wewrite'
@'
from importlib.resources import files
from pathlib import Path
from wewrite.paths import user_themes_dir

theme = files("wewrite.toolkit").joinpath("themes", "professional-clean.yaml")
target = Path(user_themes_dir()) / "professional-clean.yaml"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("aigc_footer: false\n" + theme.read_text(encoding="utf-8"), encoding="utf-8")
'@ | & .\.venv\Scripts\python.exe -X utf8 -
```

## 本地实测

使用上轮已隔离批准的豆包样稿。Codex 执笔，WeWrite CLI 建立写作任务和主张的证据登记，根据编辑判断生成审稿 JSON，并生成中文 HTML 预览。写作任务的发布权限为关闭。导出的文章给出了验证透明通道的方法，实际产品复测仍需具备相应账号和素材。

[写作样稿](examples/topic-29/wewrite/article.md) · [审稿记录](examples/topic-29/wewrite/review.json) · [HTML 预览](examples/topic-29/wewrite/preview.html)

## 交给运营者在公众号编辑页终审

正式使用时，通过微信官方草稿接口提交标题、作者、摘要、正文和封面。运营者打开公众号后台的草稿箱，在文章编辑页修改、预览并自行发布。这个环节可跳过秀米。

- 一次性接通由公众号管理员处理。确认账号拥有草稿和素材接口权限，按平台后台配置出口 IP 白名单及本机 WeWrite 的公众号 AppID、AppSecret。凭据存本地配置，作者字段用运营者指定的署名。 [官方草稿接口](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html)
- 复用已安装的 WeWrite 4.2.0。该版本的 `wewrite publish <article.md> --cover <cover.jpg> --author <署名> --digest <摘要>` 把本地正文图片上传至微信、以永久素材保存封面，再调用 `draft/add` 创建草稿。用返回的稿件 ID 调用 `draft/get` 核对标题、摘要和正文图。打开相同草稿后检查封面裁切、段距和手机预览。 [WeWrite v4.2.0](https://github.com/imraywang/wewrite/releases/tag/v4.2.0)
- 2026-11-24 用新版英伟达稿、四张正文图和封面，在 Windows 模拟了从取凭据到稿件回读的链路。接口使用模拟返回。已安装的另一套稿件脚本在该机原生 Windows 因缺少 `fcntl` 无法启动。
- 账号接口未接通时，用 `wechat_handoff.py` 生成可在浏览器打开的公众号审稿页。一次复制富文本正文，标题、作者、摘要和原文链接有独立复制按钮，封面可以单独下载。 [可重建样例](examples/nvidia-2026-11-24/run.md)
- 4.2.0 的草稿命令可提交封面素材，当前没有「原文链接」参数。使用此命令时，把已核实的公开链接随审稿页交给运营者，在最终编辑页补入并点开核对。封面和正文首图分别检查，封面以裁切预览为准。
