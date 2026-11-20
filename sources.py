import calendar
import gzip
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from http.client import HTTPException
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen

import feedparser
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from models import Item


MAX_BYTES = 4_000_000
DATE_IN_TEXT = re.compile(r"\b([A-Z][a-z]{2,8} \d{1,2}, \d{4})\b")
VERSION = re.compile(r"(?<![\w.])v?(\d+(?:\.\d+){1,3})(?![\w.])", re.I)
SIGN_IN = re.compile(r"^(?:sign in|log in|access denied|just a moment|page not found)\b", re.I)
UNWANTED_EXCERPT = re.compile(
    r"^(?:what.s (?:new|changed)|skip to|share$|read more$|on this page|copy markdown|your browser does not support)", re.I,
)
EVIDENCE_CUE = re.compile(
    r"\b(?:api|sdk|available|availability|access|released?|rollout|supports?|pricing|"
    r"benchmark|multimodal|context|repository|version|upgrade|download|weights?|tokens?|"
    r"inference|latency|cost|capabilities|preview|webRTC|OCR|file input|URL Reading|\bweb search)\b|发布|上线|支持|可用|下载|基准|推理|"
    r"评测|开源|接口|费用|资费|吞吐|延迟|可访问|版本|更新|适用|生效", re.I,
)
NETWORK_ERRORS = (HTTPError, URLError, OSError, ValueError, EOFError, HTTPException)


def _https(url):
    parts = urlsplit(url)
    return parts.scheme == "https" and bool(parts.hostname) and not (parts.username or parts.password)


def _allowed(url, hosts):
    host = urlsplit(url).hostname or ""
    return _https(url) and any(
        host == trusted.lower() or host.endswith("." + trusted.lower())
        for trusted in hosts
    )


def fetch(url):
    """Read a bounded public HTTPS response without supplying credentials."""
    if not _https(url):
        raise ValueError("来源地址需使用 HTTPS")
    request = Request(
        urldefrag(url)[0],
        headers={"User-Agent": "AIEditorialMonitor/1.0",
                 "Accept": "application/json, application/rss+xml, application/atom+xml, text/html, */*",
                 "Accept-Encoding": "gzip"},
    )
    with urlopen(request, timeout=9) as response:
        final = response.geturl()
        if not _https(final):
            raise ValueError("来源发生非 HTTPS 跳转")
        headers = dict(response.headers.items())
        content = response.read(MAX_BYTES + 1)
    if content.startswith(b"\x1f\x8b") and len(content) <= MAX_BYTES:
        with gzip.GzipFile(fileobj=BytesIO(content)) as zipped:
            content = zipped.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("响应超过 4 MB")
    return final, headers, content


def _text(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""


def _plain(value):
    if "<" in value and ">" in value:
        return _text(BeautifulSoup(value, "html.parser"))
    return " ".join(value.split())


def _cut(value, maximum):
    return value if len(value) <= maximum else value[:maximum - 1].rstrip() + "…"


def _date(value, region):
    if not value:
        return ""
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        for fmt in ("%b %d, %Y", "%B %d, %Y"):
            try:
                result = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            return ""
    if result.tzinfo is None:
        offset = 8 if region == "国内" else 0
        result = result.replace(tzinfo=timezone(timedelta(hours=offset)))
    return result.astimezone(timezone.utc).isoformat()


def _new(source, title, url, published, summary):
    subject = source.get("subject", "")
    return Item(source["name"], source["region"], source["kind"], subject,
                _cut(title, 300), url, published, _cut(summary, 920))


def extract_feed(source, final_url, headers, raw):
    """Read RSS or Atom, preferring publication time to update time."""
    result = feedparser.parse(raw, response_headers={
        "content-location": final_url,
        "content-type": next((v for k, v in headers.items() if k.lower() == "content-type"), "application/xml"),
    })
    if not result.version and not result.entries:
        raise ValueError("响应中没有可识别的 RSS 或 Atom")
    items = []
    for entry in result.entries:
        if source["kind"] == "research" and entry.get("arxiv_announce_type", "new") != "new":
            continue
        title = _plain(entry.get("title", ""))
        if source.get("include") and not re.search(source["include"], title, re.I):
            continue
        url = urljoin(final_url, entry.get("link", "")) if entry.get("link") else ""
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = (datetime.fromtimestamp(calendar.timegm(stamp), timezone.utc).isoformat()
                     if stamp else "")
        content = entry.get("summary") or next((n.value for n in entry.get("content", [])), "")
        if source.get("stable_only") and re.search(
            r"(?:[-.]nightly|[-.]preview|[-.]alpha|[-.]beta|[-.]rc)(?:[.\d-]|$)", url, re.I
        ):
            continue
        if title and _https(url):
            items.append(_new(source, title, url, published, _plain(content)))
    return items


def _newsroom(source, url, soup):
    items = []
    for time in soup.select("main time, article time"):
        for card in list(time.parents)[:6]:
            heading = card.select_one("h2, h3")
            if not heading:
                continue
            link = heading.find_parent("a", href=True) or heading.find("a", href=True)
            if not link:
                link = next((a for a in card.select("a[href]")
                             if _text(a) == _text(heading)), None)
            if not link:
                continue
            detail = urljoin(url, link["href"])
            published = _date(time.get("datetime") or _text(time), source["region"])
            if published and detail != url and _https(detail):
                description = card.select_one("p:not(:has(a))")
                items.append(_new(source, _text(heading), detail, published, _text(description)))
                break
    return items


def _deepseek(source, url, soup, reader):
    items = []
    for link in soup.select("a[href]"):
        suffix = re.search(r"/news/(?:new|news)(\d{6})/?$", link["href"])
        if not suffix:
            continue
        detail = urljoin(url, link["href"])
        final, _, raw = reader(detail)
        if not _allowed(final, source["hosts"]):
            continue
        day = suffix.group(1)
        published = _date(f"20{day[:2]}-{day[2:4]}-{day[4:]}", source["region"])
        record = BeautifulSoup(raw, "html.parser").select_one("article")
        title = _text(record.select_one("h1")) if record else ""
        if title and published:
            items.append(_new(source, title, final, published, _text(record.select_one("p"))))
    return items


def _policies(source, url, soup):
    items = []
    for link in soup.select("h5 a[href]"):
        match = re.search(r"/(\d{4})-(\d\d)/(\d\d)/c_\d+\.htm", link["href"])
        if not match:
            continue
        title = _text(link)
        if not re.search(r"人工智能|智能体|大模型|生成式|算力|算法|深度合成|信息化", title):
            continue
        published = _date("-".join(match.groups()), source["region"])
        items.append(_new(source, title, urljoin(url, link["href"]), published, ""))
    return items


def _volcengine(source, url, soup):
    items = []
    for row in soup.select("article tr"):
        columns = [_text(cell) for cell in row.find_all("td", recursive=False)]
        if len(columns) < 3 or not columns[1].lower().startswith("doubao-"):
            continue
        heading = row.find_previous("h2")
        month = re.search(r"\b(20\d{2})(\d{2})\b", _text(heading))
        day = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", columns[0])
        if not (month and day) or int(month[2]) != int(day[1]):
            continue
        published = _date(f"{month[1]}-{int(day[1]):02}-{int(day[2]):02}", source["region"])
        detail = f"{url}#{heading.get('id', '')}:~:text={quote(columns[1], safe='')}"
        items.append(_new(source, f"{columns[1]} 在火山方舟 Agent Plan 上线", detail,
                          published, columns[2]))
    return items


def _zcode(source, url, soup):
    items = []
    for heading in soup.select("h2"):
        title = _text(heading)
        if not re.fullmatch(r"Release v\d+(?:\.\d+)+", title):
            continue
        section = heading.parent.parent
        date = DATE_IN_TEXT.search(_text(section))
        if not date:
            continue
        detail = f"{url}#:~:text={quote(title, safe='')}"
        items.append(_new(source, f"ZCode {title}", detail, _date(date[1], source["region"]),
                          _text(section.select_one("article"))))
    return items


def _api_rows(soup):
    for badge in soup.select('main div[class^="_Badge_"]'):
        day = re.fullmatch(r"([A-Z][a-z]{2}) (\d{1,2})", _text(badge))
        if not day:
            continue
        row = badge.parent.parent
        heading = row.find_previous("h3")
        month = re.fullmatch(r"[A-Za-z]+, (20\d{2})", _text(heading))
        body = row.select_one('div[class*="_ChangelogMarkdown_"]')
        first = _text(body.select_one("p")) if body else ""
        if not (month and first):
            continue
        published = _date(f"{day[1]} {day[2]}, {month[1]}", "海外")
        title = f"OpenAI API 更新：{_cut(re.split(r'(?<=[.!?]) +', first)[0], 115)}"
        yield title, published, body, first[:70].rstrip()


def _api_changelog(source, url, soup):
    return [
        _new(source, title, f"{url}#:~:text={quote(marker, safe='')}", published, _text(body))
        for title, published, body, marker in _api_rows(soup)
    ]


def _discover(source, now, days, reader):
    start = (now - timedelta(days=days)).date().isoformat()
    query = urlencode({"q": f"topic:llm created:>={start} stars:>=100 archived:false fork:false",
                       "sort": "stars", "order": "desc", "per_page": 20})
    target = source["url"] + "?" + query
    _, _, payload = reader(target)
    result = json.loads(payload)
    if "items" not in result:
        raise ValueError("GitHub 搜索响应缺少 items")
    items = []
    for repo in result["items"]:
        license_id = (repo.get("license") or {}).get("spdx_id")
        if repo.get("fork") or not license_id or license_id == "NOASSERTION":
            continue
        title = repo.get("full_name", "")
        link = repo.get("html_url", "")
        if title and _allowed(link, source["hosts"]):
            description = repo.get("description") or ""
            summary = f"{description} GitHub 检出的许可证标识为 {license_id}。"
            items.append(_new(source, title, link, _date(repo.get("created_at"), source["region"]),
                              summary))
    return items


def _title_score(expected, actual):
    normalize = lambda value: " ".join(re.findall(r"[\w.]+", unicodedata.normalize("NFKC", value).casefold()))
    needle, title = normalize(expected), normalize(actual)
    if "." in needle:
        needle, title = needle.rstrip("."), title.rstrip(".")
    if not needle or not title or SIGN_IN.search(title):
        return 0
    if re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w|\.\d)", title):
        return 100
    a, b = set(VERSION.findall(needle)), set(VERSION.findall(title))
    if a and b and not a.intersection(b):
        return 0
    return fuzz.ratio(needle, title)


def _version_content(item, soup):
    """Resolve the individual record on official changelog pages."""
    parts = urlsplit(item.url)
    text_fragment = ":~:text="
    if text_fragment not in parts.fragment:
        return None, ""
    target = unquote(parts.fragment.split(text_fragment, 1)[1])
    if parts.hostname == "developers.openai.com":
        for title, _, body, marker in _api_rows(soup):
            if marker == target:
                return body, title
        return None, ""
    if parts.path.endswith("/changelog"):
        for heading in soup.select("h2"):
            if _text(heading) == target:
                return heading.parent.parent.select_one("article"), f"ZCode {target}"
    anchor = parts.fragment.split(text_fragment, 1)[0]
    for row in soup.select("article tr"):
        columns = row.find_all("td", recursive=False)
        if len(columns) > 2 and _text(columns[1]) == target:
            heading = row.find_previous("h2")
            if heading and heading.get("id") == anchor:
                return columns[2], f"{target} 在火山方舟 Agent Plan 上线"
    return None, ""


def _verified_url(item, final):
    fragment = urlsplit(item.url).fragment
    return final.split("#", 1)[0] + ("#" + fragment if fragment else "")


def _page_content(item, final, soup):
    if ":~:text=" in urlsplit(item.url).fragment:
        area, title = _version_content(item, soup)
        return area, [title]
    if "/releases/tag/" in urlsplit(final).path and urlsplit(final).hostname == "github.com":
        tag = unquote(urlsplit(final).path.split("/releases/tag/", 1)[1])
        return soup.select_one(".markdown-body"), [tag, _text(soup.select_one("main h1"))]
    title_values = []
    for meta in soup.select('meta[property="og:title"], meta[name="citation_title"]'):
        title_values.append(meta.get("content", ""))
    title_values.extend(_text(heading) for heading in soup.select("h1, title")[:6])
    choices = [
        "blockquote.abstract", ".article-content", "#articleContent", "#pro", ".TRS_Editor",
        "main article", "article", "main", '[role="main"]',
    ]
    area = next((node for selector in choices if (node := soup.select_one(selector))), None)
    if area is None and soup.find("body"):
        area = soup.body
    return area, title_values


def _evidence_paragraphs(area, item):
    if area is None:
        return []
    candidates = []
    for node in area.select("p, li, blockquote")[:85]:
        if node.find_parent(["nav", "footer", "aside"]):
            continue
        if node.name in {"li", "blockquote"} and node.find("p"):
            continue
        paragraph = re.sub(r"^Abstract:\s*", "", _text(node), flags=re.I)
        if len(paragraph) < 32 or UNWANTED_EXCERPT.match(paragraph):
            continue
        if _title_score(item.title, paragraph) > 92 and len(paragraph) < len(item.title) + 28:
            continue
        candidates.append(paragraph)
    if not candidates and area.name in {"td", "p", "blockquote", "body-content"}:
        candidates.append(re.sub(r"^Abstract:\s*", "", _text(area), flags=re.I))
    if not candidates:
        return []
    identities = re.findall(
        r"\b[\w-]+ +\d+(?:\.\d+){0,3}(?: (?:Flash|Neon|Hydrogen|Pro))?\b",
        item.title, re.I,
    )

    def relevance(paragraph):
        cues = {cue.casefold() for cue in EVIDENCE_CUE.findall(paragraph)}
        mentions = any(identity.casefold() in paragraph.casefold() for identity in identities)
        features = paragraph.casefold().startswith(("feat(", "feat:"))
        return min(4, len(cues)) + 3 * mentions + 2 * features + bool(re.search(r"\d", paragraph))
    # Inspect the opening section for the main evidence. A later supporting passage
    # can supply specifications or deployment details without obscuring the lead.
    leading = max(enumerate(candidates[:8]), key=lambda row: (relevance(row[1]), -row[0]))[1]
    related = sorted((p for p in dict.fromkeys(candidates[1:20]) if p != leading),
                     key=relevance, reverse=True)
    return [leading] + related[:2]


def verify(item, hosts, *, reader=None):
    """Check an original URL's source ownership, title and visible article evidence."""
    evidence = {"matched": False, "url": item.url, "title": "", "excerpt": "",
                "checked_at": datetime.now(timezone.utc).isoformat(), "reason": ""}
    if not _allowed(item.url, hosts):
        return {**evidence, "reason": "原始链接不在该来源允许的 HTTPS 域名范围内"}
    reader = reader or fetch
    try:
        final, _, body = reader(item.url)
    except NETWORK_ERRORS as error:
        return {**evidence, "reason": f"原始页面暂不可读（{error}）"}
    if not _allowed(final, hosts):
        return {**evidence, "reason": "跳转目标超出该来源允许的域名"}
    final = _verified_url(item, final)
    soup = BeautifulSoup(body, "html.parser")
    area, titles = _page_content(item, final, soup)
    title = max(titles, key=lambda value: _title_score(item.title, value), default="")
    paragraphs = _evidence_paragraphs(area, item)
    excerpt = paragraphs[0] if paragraphs else ""
    if _title_score(item.title, title) < 79 or len(excerpt) < 24:
        return {**evidence, "url": final, "title": _cut(title, 300),
                "reason": "未找到与采集标题匹配且有实质内容的页面"}
    # Repository discovery checks the linked repository identity and description only.
    reason = ("已核对仓库页面和标识，采用价值及许可证适用性需单独核查"
              if item.kind == "discovery" else "已核对原始页面标题和正文，摘录保留原始归属")
    return {**evidence, "matched": True, "url": final, "title": _cut(title, 300),
            "excerpt": _cut(excerpt, 300), "reason": reason,
            "detail_paragraphs": [_cut(text, 200) for text in paragraphs[1:]]}


def _version(item):
    if item.kind == "repository":
        value = re.search(r"/releases/tag/v?(\d+(?:\.\d+){1,3})/?$", item.url, re.I)
    elif item.subject == "ZCode":
        value = VERSION.search(item.title)
    else:
        return None
    return tuple(int(part) for part in value[1].split(".")) if value else None


def _attach_previous(verified, candidates, hosts, reader):
    versions = [(item, version) for item in candidates if (version := _version(item))]
    if not versions:
        return
    ensure = lru_cache(maxsize=None)(lambda item: verify(item, hosts, reader=reader))
    for item, evidence in verified:
        current = _version(item)
        if not evidence["matched"] or not current:
            continue
        older = [(candidate, version) for candidate, version in versions
                 if version < current and candidate.published <= item.published and candidate.published]
        if not older:
            continue
        prior = max(older, key=lambda row: row[1])[0]
        previous = ensure(prior)
        if previous["matched"]:
            evidence["previous"] = {key: previous[key] for key in ("url", "title", "excerpt")}
            evidence["previous"]["published"] = prior.published


def _source_items(source, now, days, limit):
    url = source["url"]
    opener = lru_cache(maxsize=40)(fetch)
    reader = lambda value: opener(urldefrag(value)[0])
    health = {"source": source["name"], "region": source["region"], "kind": source["kind"],
              "url": url, "status": "ok", "fetched": 0, "selected": 0, "verified": 0,
              "message": "", "latest": ""}
    hosts = source.get("hosts", [urlsplit(url).hostname])
    try:
        kind = source.get("type", "feed")
        if kind == "github":
            items = _discover(source, now, days, reader)
        else:
            final, headers, raw = reader(url)
            if kind == "feed":
                items = extract_feed(source, final, headers, raw)
            else:
                soup = BeautifulSoup(raw, "html.parser")
                if kind == "deepseek":
                    items = _deepseek(source, final, soup, reader)
                else:
                    extract = {"newsroom": _newsroom, "policies": _policies,
                               "volcengine": _volcengine, "zcode": _zcode,
                               "api_changelog": _api_changelog}[kind]
                    items = extract(source, final, soup)
    except NETWORK_ERRORS as error:
        health.update(status="error", message=str(error))
        return [], health
    by_url = {item.url: item for item in items}
    candidates = sorted(by_url.values(), key=lambda item: item.published, reverse=True)
    health.update(fetched=len(candidates), latest=candidates[0].published if candidates else "")
    if not candidates:
        health.update(status="empty", message="来源没有可解析的事件")
        return [], health
    cutoff = now - timedelta(days=days)
    eligible = [item for item in candidates if item.published
                and cutoff <= datetime.fromisoformat(item.published) <= now]
    if not eligible:
        health.update(status="stale", message="采集窗口内没有带有效发布时间的条目")
        return [], health
    selected = eligible[:min(limit, source.get("limit", limit))]
    batch = [(item, verify(item, hosts, reader=reader)) for item in selected]
    _attach_previous(batch, candidates, hosts, reader)
    count = sum(evidence["matched"] for _, evidence in batch)
    if count < len(batch):
        health["message"] = f"{len(batch) - count} 条原始页面待核查"
    health.update(selected=len(batch), verified=count)
    return batch, health


def collect(config_path, now, days, limit):
    """Collect and verify concurrently, returning both candidates and source health."""
    if days < 1 or limit < 1 or now.tzinfo is None:
        raise ValueError("时间窗口、每来源上限需大于零，运行时间需带时区")
    settings = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    if not isinstance(settings, list) or not settings:
        raise ValueError("来源配置需要包含至少一项")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda source: _source_items(source, now, days, limit), settings))
    return [entry for batch, _ in results for entry in batch], [health for _, health in results]
