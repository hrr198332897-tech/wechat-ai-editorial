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
