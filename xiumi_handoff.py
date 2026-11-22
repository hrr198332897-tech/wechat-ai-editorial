"""Package Markdown once for Xiumi's native HTML or Word import."""

import argparse
import base64
from html import escape
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown
from bs4 import BeautifulSoup, NavigableString
from docx import Document
from docx.image.exceptions import InvalidImageStreamError, UnexpectedEndOfFileError, UnrecognizedImageError
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


INLINE_STYLES = {
    "p": "margin:0 0 16px;color:#232c36;font-size:16px;line-height:1.85;text-align:left;overflow-wrap:anywhere;",
    "a": "color:#176272;text-decoration:underline;",
    "blockquote": "margin:0 0 16px;padding:12px 16px;background:#f0f7f7;border-left:3px solid #176272;",
    "img": "display:block;width:100%;max-width:100%;height:auto;border-radius:8px;",
    "pre": "white-space:pre-wrap;overflow-wrap:anywhere;",
}
HEADINGS = {"h2", "h3", "h4", "h5", "h6"}
HTML_TAGS = HEADINGS | set(INLINE_STYLES) | {"strong", "b", "em", "i", "code", "ul", "ol", "li", "br", "hr"}


def append_text(paragraph, node, *, bold=False, italic=False):
    if isinstance(node, NavigableString):
        run = paragraph.add_run(str(node))
        run.bold = bold
        run.italic = italic
        return
    if node.name == "img":
        raise ValueError("正文图片需要独占一个 Markdown 段落")
    if node.name == "br":
        paragraph.add_run().add_break()
        return
    for child in node.children:
        append_text(
            paragraph, child,
            bold=bold or node.name in {"strong", "b"},
            italic=italic or node.name in {"em", "i"},
        )
    if node.name == "a":
        url = node.get("href", "")
        host = urlsplit(url)
        if host.scheme in {"http", "https"} and host.netloc and url != node.get_text():
            paragraph.add_run(f"（{url}）")


def picture_path(article_folder, src):
    path = (article_folder / unquote(src)).resolve()
    if not src or urlsplit(src).scheme or not path.is_relative_to(article_folder):
        raise ValueError(f"正文图片需使用稿件目录内的相对路径：{src}")
    if not path.is_file():
        raise ValueError(f"找不到正文图片：{src}")
    return path


def add_picture(doc, node, article_folder):
    src = node.get("src", "")
    path = picture_path(article_folder, src)
    try:
        shape = doc.add_picture(str(path), width=Inches(5.6))
    except (InvalidImageStreamError, UnexpectedEndOfFileError, UnrecognizedImageError) as error:
        raise ValueError(f"正文图片无法读取：{src}") from error
    shape._inline.docPr.set("descr", node.get("alt", ""))


def hosted_mapping(mapping_path, images):
    mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    if not isinstance(mapping, dict):
        raise ValueError("图片地址映射需为 JSON 对象")
    for url in mapping.values():
        if not isinstance(url, str) or urlsplit(url).netloc.lower() != "img.xiumi.us" or urlsplit(url).scheme != "https":
            raise ValueError("图片地址需使用本次上传得到的 HTTPS 秀米图床链接")
    if set(images) != set(mapping):
        raise ValueError("图片映射需与正文图片路径逐项对应")
    return mapping


def render_html(body_html, image_sources):
    parsed = BeautifulSoup(body_html, "html.parser")
    for tag in parsed.find_all():
        if tag.name not in HTML_TAGS:
            raise ValueError(f"暂不支持的 HTML 元素：{tag.name}")
        attrs = {}
        if tag.name == "img":
            attrs = {"src": image_sources[tag.get("src", "")], "alt": tag.get("alt", "")}
        elif tag.name == "a":
            href = tag.get("href", "")
            if urlsplit(href).scheme in {"http", "https"} and urlsplit(href).netloc:
                attrs["href"] = href
        if tag.name in INLINE_STYLES:
            attrs["style"] = INLINE_STYLES[tag.name]
        if tag.name in HEADINGS:
            attrs["style"] = "margin:26px 0 14px;color:#194756;font-size:19px;line-height:1.5;font-weight:bold;"
        tag.attrs = attrs
    return '<section style="margin:0 auto;max-width:680px;">' + str(parsed) + "</section>"


def export(article, output, summary, author="", mapping_path=None):
    markup = markdown.markdown(article.read_text(encoding="utf-8-sig"))
    parsed = BeautifulSoup(markup, "html.parser")
    blocks = parsed.find_all(recursive=False)
    if not blocks or blocks[0].name != "h1" or not blocks[0].get_text(strip=True):
        raise ValueError("稿件首段需包含一个一级 Markdown 标题")
    title = blocks[0].get_text(strip=True)
    if not summary.strip() or "\n" in summary or "\r" in summary:
        raise ValueError("请提供一行非空摘要")
    if len(blocks) == 1:
        raise ValueError("稿件没有正文")
    if "\n" in author or "\r" in author:
        raise ValueError("作者需为单行文字")

    article_folder = article.resolve().parent
    images = list(dict.fromkeys(img.get("src", "") for img in parsed.find_all("img")))
    mapping = hosted_mapping(mapping_path, images) if mapping_path else {}
    doc = Document()
    doc.core_properties.author = ""
    doc.core_properties.title = title
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal.font.size = Pt(11)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.paragraph_format.space_after = Pt(8)

    for node in blocks[1:]:
        children = [el for el in node.children if str(el).strip()]
        if node.name == "p" and len(children) == 1 and getattr(children[0], "name", None) == "img":
            add_picture(doc, children[0], article_folder)
        elif node.name in HEADINGS:
            append_text(doc.add_heading(level=int(node.name[1])), node)
        elif node.name in {"ul", "ol"}:
            for number, item in enumerate(node.find_all("li", recursive=False), start=1):
                marker = f"{number}. " if node.name == "ol" else "• "
                append_text(doc.add_paragraph(marker), item)
        elif node.name in {"p", "blockquote", "pre"}:
            append_text(doc.add_paragraph(), node)
        elif node.name != "hr":
            raise ValueError(f"暂不支持的正文块：{node.name}")

    body_html = "\n".join(str(node) for node in blocks[1:])
    embedded = {}
    for src in images:
        path = picture_path(article_folder, src)
        media_type = mimetypes.guess_type(path.name)[0]
        if media_type not in {"image/png", "image/jpeg", "image/gif"}:
            raise ValueError(f"请将正文图片转成 PNG、JPEG 或 GIF：{src}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        embedded[src] = f"data:{media_type};base64,{encoded}"
    preview = render_html(body_html, embedded)
    import_html = render_html(body_html, mapping) if mapping or not images else None
    if import_html is None and (output / "xiumi-import.html").exists():
        raise ValueError("输出目录已有可导入 HTML，请保留图片映射或为新版本指定另一输出目录")

    output.mkdir(parents=True, exist_ok=True)
    doc.save(output / "xiumi-import.docx")
    fields = [title, summary.strip()]
    if author.strip():
        fields.append(author.strip())
    (output / "title-summary.txt").write_text("\n\n".join(fields) + "\n", encoding="utf-8")
    (output / "xiumi-preview.html").write_text(
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{escape(title)}</title><body style="margin:0 auto;max-width:680px;padding:18px;">'
        f'<h1 style="font-size:25px;line-height:1.4;">{escape(title)}</h1>{preview}</body></html>',
        encoding="utf-8",
    )
    if import_html is not None:
        (output / "xiumi-import.html").write_text(import_html, encoding="utf-8")
    metadata = {
        "title": title,
        "summary": summary.strip(),
        "author": author.strip(),
        "html_ready": import_html is not None,
        "images": [{"source": src, "hosted_url": mapping.get(src)} for src in images],
    }
    (output / "handoff.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path, help="带有标题和本地相对图片路径的 Markdown 成稿")
    parser.add_argument("--summary", required=True, help="秀米摘要")
    parser.add_argument("--author", default="", help="已知的秀米作者名")
    parser.add_argument("--image-urls", type=Path, help="本稿图片路径到秀米图床 HTTPS 地址的 JSON 映射")
    parser.add_argument("--out", type=Path, required=True, help="交接素材输出目录")
    args = parser.parse_args()
    try:
        export(args.article, args.out, args.summary, args.author, args.image_urls)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(args.out / "xiumi-import.docx")
    print(args.out / "handoff.json")


if __name__ == "__main__":
    main()
