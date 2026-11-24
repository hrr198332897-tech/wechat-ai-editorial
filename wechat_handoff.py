"""Build a portable local review page for the WeChat article editor."""

import argparse
from base64 import b64encode
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from string import Template
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from wewrite.toolkit.converter import WeChatConverter, make_paste_safe
from wewrite.toolkit.theme import load_theme


TEMPLATE = Path(__file__).resolve().parent / ".agents/skills/wechat-ai-workflow/assets/wechat-review.html"
IMAGE_FORMATS = {
    ".jpg": ("jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("jpeg", b"\xff\xd8\xff"),
    ".png": ("png", b"\x89PNG\r\n\x1a\n"),
    ".gif": ("gif", b"GIF8"),
}


class HandoffConverter(WeChatConverter):
    # The pinned upstream converter removes every "# " line, including code comments.
    def _strip_h1(self, text):
        return text.partition("\n")[2]

    # Spacing belongs to the approved manuscript. Asset filenames must also match exactly.
    def _fix_cjk_spacing(self, text):
        return text


def image_data(folder, source, *, cover=False):
    uri = urlsplit(source)
    relative = Path(unquote(source))
    if not source or uri.scheme or uri.netloc or relative.anchor:
        raise ValueError(f"图片需使用稿件目录内的相对路径：{source}")
    path = (folder / relative).resolve()
    if not path.is_relative_to(folder):
        raise ValueError(f"图片需使用稿件目录内的相对路径：{source}")
    if not path.is_file():
        raise ValueError(f"找不到图片：{source}")
    image_format = IMAGE_FORMATS.get(path.suffix.lower())
    if image_format is None or (cover and image_format[0] == "gif"):
        raise ValueError(f"图片格式需为 JPG、PNG，正文也可使用 GIF：{source}")
    name, signature = image_format
    payload = path.read_bytes()
    if not payload.startswith(signature):
        raise ValueError(f"图片内容与扩展名不一致：{source}")
    return f"data:image/{name};base64,{b64encode(payload).decode('ascii')}"


def export(article, output, summary, author, cover, source_url):
    if not summary.strip() or len(summary.splitlines()) != 1 or len(author.splitlines()) > 1:
        raise ValueError("摘要须非空，摘要和作者均为单行文字")
    if source_url:
        address = urlsplit(source_url)
        if address.scheme not in ("https", "http") or not address.hostname or address.username:
            raise ValueError("原文链接需为公开 HTTP 或 HTTPS 地址")

    raw = article.read_bytes()
    markdown = raw.decode("utf-8-sig").lstrip()
    heading = markdown.partition("\n")[0]
    if not heading.startswith("# ") or not heading[2:].strip():
        raise ValueError("第一段需为 Markdown 一级标题")
    theme = load_theme("professional-clean")
    theme._raw_data["aigc_footer"] = False
    result = HandoffConverter(theme=theme).convert(markdown)
    body = BeautifulSoup(make_paste_safe(result.html), "html.parser")
    if not body.get_text(strip=True) and not body.find("img"):
        raise ValueError("正文为空")
    if body.find("h1"):
        raise ValueError("正文只能使用二级及以下标题")
    if body.select("script, style, iframe, object, embed, form, input, video, audio, link, meta, base, svg, math"):
        raise ValueError("正文包含不适合图文粘贴的交互元素")
    for element in body.find_all():
        if any(attr.startswith("on") or attr in ("srcset", "background", "srcdoc") for attr in element.attrs):
            raise ValueError("正文包含不适合图文粘贴的交互属性")
    for anchor in body.find_all("a"):
        anchor.unwrap()

    folder = article.resolve().parent
    images = []
    for image in body.select("img"):
        source = image.get("src", "")
        images.append(source)
        image["src"] = image_data(folder, source)
    for paragraph in body.find_all("p", recursive=False):
        spacing = "12px" if paragraph.find("img") else "25px"
        paragraph["style"] = f"{paragraph.get('style', '')};margin:0 0 {spacing}"

    cover_data = image_data(folder, cover, cover=True)
    preview = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        title=escape(result.title), summary=escape(summary), author=escape(author),
        source_url=escape(source_url), cover_data=cover_data,
        cover_name=escape(Path(cover).name), body=str(body),
    ).encode("utf-8")
    metadata = {
        "title": result.title,
        "summary": summary,
        "author": author,
        "source_url": source_url,
        "cover": cover,
        "images": images,
        "article_sha256": sha256(raw).hexdigest(),
        "preview_sha256": sha256(preview).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "review.html").write_bytes(preview)
    (output / "handoff.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="打包本地公众号审稿页与富文本复制")
    parser.add_argument("article", type=Path)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--cover", required=True, help="相对于稿件目录的 JPG 或 PNG 文件")
    parser.add_argument("--source-url", default="", help="填入公众号原文链接栏的公开网址")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        export(args.article, args.out, args.summary, args.author, args.cover, args.source_url)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(args.out / "review.html")
    print(args.out / "handoff.json")


if __name__ == "__main__":
    main()
