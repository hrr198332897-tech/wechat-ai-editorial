import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from rapidfuzz import fuzz

from models import Item


SHANGHAI = timezone(timedelta(hours=8))
PRIMARY = {"official", "repository", "research", "government", "policy"}
TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid", "trk", "f_link_type", "flow_extra"}
RELEASE = r"\b(?:release[sd]?|launch(?:ed|es)?|introduc\w*|debut\w*|available)\b|发布|上线|开放|推出"
VERSION = r"\bv?\d+\.\d+(?:\.\d+)?(?:[-.]?(?:rc|beta|alpha)\.?\d*)?\b"
MODEL = (
    r"(?:gemini|gpt|claude|qwen|deepseek|kimi|glm|llama|seedance|seedream|seed|o[134]|gemma)"
    r"[-\s]*(?:opus|sonnet|haiku|v|k|r)?[-\s]*\d+(?:\.\d+){0,2}"
    r"(?:[-\s]*(?:opus|sonnet|haiku|flash[-\s]*lite|flash|pro|ultra|mini|max|nano|lite|turbo|preview|thinking)\b)*"
    r"(?:[-\s]*\d+(?:\.\d+)?[bm](?:[-\s]*a\d+(?:\.\d+)?[bm])?\b)?"
)


def canonical(url):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING]
    path = parts.path.rstrip("/") or "/"
    fragment = parts.fragment if re.search(r"changelog|release-note|announcement", path, re.I) else ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(sorted(query)), fragment))


def clean(text):
    return re.sub(r"[^\w\u3400-\u9fff]+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def date(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=SHANGHAI)


def family(title):
    if re.search(r"pricing|price cut|discount|降价|涨价|定价", title, re.I):
        return "pricing"
    if re.search(r"deprecat|retir|discontinu|sunset|停用|下线|废弃", title, re.I):
        return "retirement"
    if re.search(r"benchmark|test report|测评|跑分", title, re.I) and not re.search(RELEASE, title, re.I):
        return "evaluation"
    if re.search(RELEASE, title, re.I):
        return "release"
    return ""


def matches(left, right):
    if canonical(left.url) == canonical(right.url):
        return True
    if not left.published or not right.published or abs(date(left.published) - date(right.published)) > timedelta(days=5):
        return False
    a, b = clean(left.title), clean(right.title)
    left_versions = re.findall(VERSION, left.title.casefold())
    right_versions = re.findall(VERSION, right.title.casefold())
    if left_versions and right_versions and left_versions != right_versions:
        if [v.removeprefix("v") for v in left_versions] != [v.removeprefix("v") for v in right_versions]:
            return False
    if left.kind == right.kind == "repository":
        if clean(left.subject) != clean(right.subject):
            return False
        if bool(left_versions) != bool(right_versions):
            return False
    left_models = {clean(m).replace(" ", "") for m in re.findall(MODEL, left.title, re.I)}
    right_models = {clean(m).replace(" ", "") for m in re.findall(MODEL, right.title, re.I)}
    if left_models and right_models and left_models != right_models:
        return False
    left_family, right_family = family(left.title), family(right.title)
    if left_family and right_family and left_family != right_family:
        return False
    if left_models and left_models == right_models and left_family == right_family == "release":
        # Check the rest of the title for separate rollout channels or hardware.
        tails = [re.sub(MODEL, "", item.title, flags=re.I) for item in (left, right)]
        channels = [set(re.findall(r"\b(?:api|vertex|android|ios|workspace|cloud|enterprise|app|preview)\b",
                                   tail.lower())) for tail in tails]
        return channels[0] == channels[1]
    if a == b and len(a) >= 14:
        return True
    return min(len(a), len(b)) >= 22 and fuzz.ratio(a, b) >= 92


def classify(item, evidence):
    title = item.title.lower()
    context = f"{title} {evidence.get('excerpt', '').lower()}"
    if item.kind in {"government", "policy"} or re.search("policy|regulation|政策|管理办法|监管", title):
        return "政策"
    if item.kind == "research" or re.search(r"\b(?:study|research paper|method|framework)\b|研究论文|新方法", title):
        return "技术研究"
    if re.search(MODEL, title, re.I) and family(title) in {"release", ""} and item.kind != "repository":
        return "模型发布"
    if item.kind == "repository":
        return "工具更新" if "/releases/" in item.url else "开源项目"
    if re.search(r"\b(?:gpu|chip|inference infrastructure|data center)\b|芯片|算力|数据中心", title):
        return "算力与基建"
    if re.search(r"case study|production deployment|真实应用|案例|试点", context):
        return "真实应用"
    if re.search(r"\b(?:api|sdk|tool|agent|integration|coding|codex)\b|工具|智能体|接口", title):
        return "工具更新"
    return "产业动态"


def display_time(value):
    return date(value).astimezone(SHANGHAI).strftime("%Y-%m-%d %H:%M（北京时间）") if value else "来源未给出日期"


def rank(pair):
    item, evidence = pair
    ranks = {"government": 4, "policy": 4, "official": 4, "repository": 3, "research": 3}
    return (bool(evidence.get("matched") and item.kind in PRIMARY),
            ranks.get(item.kind, 0), bool(item.published), bool(evidence.get("excerpt")))


def assess(pairs, now):
    ordered = sorted(pairs, key=rank, reverse=True)
    primary, evidence = ordered[0]
    verified = primary.kind in PRIMARY and evidence.get("matched", False)
    category = classify(primary, evidence)
    source_text = f"{primary.title} {evidence.get('excerpt', '')}"
    specific = bool(re.search(r"\b(api|sdk|model weights?|open.source|multimodal|memory|latency|"
                              r"benchmark|gpu|inference|license)\b|模型权重|开源|多模态|推理|合规|许可证",
                              source_text, re.I))
    dated = bool(primary.published)
    age = (now - date(primary.published)).total_seconds() / 86400 if dated else 999
    public_action = bool(re.search(RELEASE, primary.title, re.I) or
                         primary.kind in {"repository", "government", "policy"})
    topical = category != "产业动态" or bool(re.search(r"\b(?:ai|llm|agent)\b|人工智能|模型", source_text, re.I))
    low_signal = bool(re.search(r"\b(?:webinar|newsletter|roadshow|stock price|initial public offering|"
                                r"sponsorship|weekly roundup|bug fixes only)\b|周报|活动回顾|报名|营销活动",
                                primary.title, re.I))
    important = category in {"模型发布", "算力与基建", "政策"} and public_action
    if category == "工具更新" and primary.kind == "repository":
        important = bool(re.search(r"\bv?\d+\.0\.0\b", primary.title))
    dimensions = {
        "技术突破": 5 if important and specific else 3 if specific and topical else 2 if topical else 0,
        "实际应用": 5 if specific and public_action else 4 if specific else 2 if topical else 0,
        "信息可靠性": 5 if verified and primary.kind in {"government", "policy"} else 4 if verified else 1,
        "行业影响": 5 if important else 3 if topical else 1,
        "中文读者参考": 5 if primary.region == "国内" and topical else 4 if specific else 2 if topical else 0,
        "新颖性": 5 if -0.5 <= age <= 3 and public_action else 4 if -0.5 <= age <= 14 else 2 if 14 < age <= 45 else 0,
    }
    score = sum(dimensions.values())
    eligible = verified and dated and -0.5 <= age <= 45 and topical and not low_signal
    grade = "D"
    if verified and not low_signal:
        grade = "C"
    if eligible and score >= 20 and specific:
        grade = "A" if score >= 26 and important else "B"
    if primary.kind == "research" and grade == "A":
        grade = "B"
    facts = [
        f"一手页面与入库条目匹配。发布主体为 {primary.source}，原题为「{primary.title}」。",
        f"来源记录时间为 {display_time(primary.published)}。",
    ] if verified else ["一手页面尚未与条目匹配。"]
    claims = ("厂商或作者的原文摘录。性能、适用范围与可用性按其公开说明处理，编辑须另行复核。"
              if verified and primary.kind not in {"government", "policy"} else
              "以政策原文为准。具体适用范围、生效时间和配套要求请逐条核读。"
              if verified else "暂无通过匹配的一手原文。")
    sources = []
    for item, proof in ordered:
        sources.append(asdict(item) | {"evidence": proof})
    previous = evidence.get("previous") or evidence.get("baseline")
    return {
        "title": primary.title, "region": primary.region, "published": primary.published,
        "grade": grade, "score": score, "dimensions": dimensions, "category": category,
        "facts": facts, "claims": claims,
        "third_party": [entry["source"] + "：" + entry["title"] for entry in sources if entry["kind"] == "media"],
        "previous": previous,
        "sources": sources,
        "reliability": "已回查并匹配一手页面" if verified else "一手证据未匹配",
    }


SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'pending', note TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL DEFAULT '', card TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS items (
    source TEXT NOT NULL, url TEXT NOT NULL, event_id INTEGER NOT NULL REFERENCES events(id),
    payload TEXT NOT NULL, evidence TEXT NOT NULL, PRIMARY KEY (source, url)
);
CREATE INDEX IF NOT EXISTS items_event ON items(event_id);
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, time TEXT NOT NULL, health TEXT NOT NULL, metrics TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events(id),
    time TEXT NOT NULL, status TEXT NOT NULL, note TEXT NOT NULL, fingerprint TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def save_run(self, now, batch, outcomes):
        metrics = {"new_items": 0, "repeated": 0, "merged": 0, "new_events": 0, "alert_ids": []}
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            groups = defaultdict(dict)
            link_index = {}
            for row in self.db.execute("SELECT * FROM items ORDER BY rowid"):
                pair = (Item(**json.loads(row["payload"])), json.loads(row["evidence"]))
                key = (row["source"], row["url"])
                groups[row["event_id"]][key] = pair
                link_index[row["url"]] = row["event_id"]
            representatives = {key: max(group.values(), key=rank)[0] for key, group in groups.items()}
            touched = set()
            for item, evidence in sorted(batch, key=rank, reverse=True):
                link = canonical(item.url)
                key = (item.source, link)
                event = link_index.get(link)
                if event is None:
                    event = next((id_ for id_, candidate in representatives.items() if matches(candidate, item)), None)
                if event is None:
                    event = self.db.execute("INSERT INTO events DEFAULT VALUES").lastrowid
                    representatives[event] = item
                    metrics["new_events"] += 1
                elif key in groups[event]:
                    metrics["repeated"] += 1
                    old_item, old_evidence = groups[event][key]
                    if old_evidence.get("matched") and not evidence.get("matched"):
                        item, evidence = old_item, old_evidence
                else:
                    metrics["merged"] += 1
                metrics["new_items"] += key not in groups[event]
                groups[event][key] = (item, evidence)
                link_index[link] = event
                self.db.execute(
                    "INSERT INTO items VALUES (?, ?, ?, ?, ?) ON CONFLICT(source,url) DO UPDATE SET "
                    "payload=excluded.payload, evidence=excluded.evidence",
                    (*key, event, json.dumps(asdict(item), ensure_ascii=False), json.dumps(evidence, ensure_ascii=False)),
                )
                touched.add(event)
            grades = Counter()
            for event in sorted(touched):
                card = assess(list(groups[event].values()), now)
                lead = card["sources"][0]
                proof = lead["evidence"]
                material = [canonical(lead["url"]), lead["title"], lead["published"], proof.get("matched"),
                            proof.get("excerpt"), card["previous"], card["grade"] in {"A", "B"}]
                fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
                before = self.db.execute("SELECT status, fingerprint FROM events WHERE id=?", (event,)).fetchone()
                if (card["grade"] in {"A", "B"} and before["fingerprint"] != fingerprint
                        and before["status"] != "rejected"):
                    metrics["alert_ids"].append(event)
                if before["status"] == "approved" and before["fingerprint"] != fingerprint:
                    note = "一手证据或提醒资格发生变化，重新待审。"
                    self.db.execute("UPDATE events SET status='pending', note=? WHERE id=?", (note, event))
                    self.db.execute("INSERT INTO reviews(event_id,time,status,note,fingerprint) VALUES (?,?,?,?,?)",
                                    (event, now.isoformat(), "pending", note, fingerprint))
                self.db.execute("UPDATE events SET fingerprint=?, card=? WHERE id=?",
                                (fingerprint, json.dumps(card, ensure_ascii=False), event))
                grades[card["grade"]] += 1
            metrics["counts"] = {grade: grades[grade] for grade in "ABCD"}
            metrics["events"] = len(touched)
            metrics["run_id"] = self.db.execute(
                "INSERT INTO runs(time,health,metrics) VALUES (?,?,?)",
                (now.isoformat(), json.dumps(outcomes, ensure_ascii=False), json.dumps(metrics)),
            ).lastrowid
        return metrics

    def list(self):
        cards = [self.card_from_row(row) for row in self.db.execute("SELECT * FROM events")]
        return sorted(cards, key=lambda card: (card["grade"], -card["score"], -card["id"]))

    def get(self, id_):
        row = self.db.execute("SELECT * FROM events WHERE id=?", (id_,)).fetchone()
        if row is None:
            raise ValueError(f"未找到选题 {id_}")
        return self.card_from_row(row)

    @staticmethod
    def card_from_row(row):
        return json.loads(row["card"]) | {
            "id": row["id"], "status": row["status"], "review_note": row["note"],
        }

    def review(self, id_, status, note):
        if status not in {"approved", "pending", "research", "rejected"}:
            raise ValueError("未知审核状态")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            card = self.get(id_)
            if status == "approved" and card["grade"] not in {"A", "B"}:
                raise ValueError("只有达到 A/B 来源及价值门槛的选题可批准")
            fingerprint = self.db.execute("SELECT fingerprint FROM events WHERE id=?", (id_,)).fetchone()[0]
            self.db.execute("UPDATE events SET status=?, note=? WHERE id=?", (status, note, id_))
            self.db.execute("INSERT INTO reviews(event_id,time,status,note,fingerprint) VALUES (?,?,?,?,?)",
                            (id_, datetime.now(timezone.utc).isoformat(), status, note, fingerprint))

    def latest_run(self):
        run = self.db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if run:
            return {"id": run["id"], "time": run["time"], "health": json.loads(run["health"]),
                    "metrics": json.loads(run["metrics"])}

    def export(self, id_, destination):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            return write_bundle(self.get(id_), destination)


def get_copy(card, *, draft=False):
    from writing import build_copy

    lead = card["sources"][0]
    data = build_copy(Item(**{field: lead[field] for field in Item.__dataclass_fields__}),
                      lead["evidence"], card["category"], lead["subject"], card["review_note"] if draft else "",
                      include_draft=draft)
    return data


def render_card(card):
    text = get_copy(card)
    lead = card["sources"][0]
    excerpt = lead["evidence"].get("excerpt") or "暂缺匹配摘录。"
    baseline = card["previous"]
    baseline_text = text.get("comparison") or (
        "暂缺可直接对比的旧版证据。先找到旧文档、版本记录或相同条件下的评测。"
    )
    if isinstance(baseline, dict) and baseline.get("url"):
        baseline_text += f"\n\n旧版出处　{baseline['url']}"
    lines = [
        f"# {card['id']} · {card['grade']} · {text['headline']}", "",
        f"原题　{card['title']}", "", f"事件时间　{display_time(card['published'])}",
        "", f"地区　{card['region']}　｜　分类　{card['category']}　｜　审核　{card['status']}",
        "", f"原始链接　{lead['url']}", "", "## 核心变化", "", text.get("change") or text["abstract"],
        "", "## 与此前相比", "", baseline_text, "", "## 一手来源已确认", "",
        *("- " + fact for fact in card["facts"]), "", "## 厂商或论文作者的说法", "",
        card["claims"], "", excerpt, "", "## 第三方观点或报道线索", "",
        *("- " + entry for entry in (card["third_party"] or ["本轮未检得第三方观点。"])),
        "", "## 待核实与风险", "",
        "按原文核对可用地区、价格、版本、许可证及测试条件。性能或实际收益须有独立证据。",
        "", "## 实际意义", "",
        *(f"- {key}　{value}" for key, value in text.get("impact", {}).items()),
        "", "## 公众号选题", "", text["angle"], "", "备选标题", "",
        *("- " + title for title in text["alternatives"]), "", "## 文章结构", "",
        *("- " + section for section in text["outline"]), "",
        f"## 证据与评分", "", f"{card['reliability']} · {card['score']}/30",
        "", " / ".join(f"{name} {value}/5" for name, value in card["dimensions"].items()), "",
    ]
    for source in card["sources"]:
        proof = source["evidence"]
        lines.append(f"- {source['source']} · {source['kind']} · {source['url']}")
        if proof.get("checked_at") or proof.get("reason"):
            lines.append(f"  {proof.get('reason', '')} {proof.get('checked_at', '')}".rstrip())
    if card["review_note"]:
        lines += ["", "## 审核备注", "", card["review_note"]]
    return "\n".join(lines) + "\n"


def write_bundle(card, destination):
    if card["status"] != "approved":
        raise ValueError("选题须经人工批准后方可导出写作素材")
    copy = get_copy(card, draft=True)
    path = Path(destination) / f"topic-{card['id']}"
    path.mkdir(parents=True, exist_ok=True)
    references = [(source["source"], source["url"]) for source in card["sources"]]
    sections = [("摘要", copy["abstract"]), *copy["draft"]]
    markdown = [f"# {copy['headline']}", ""]
    plaintext = [copy["headline"], ""]
    paragraph = 'style="margin:0 0 14px;line-height:1.75;color:#222;"'
    html = [f'<h1 style="font-size:25px;">{escape(copy["headline"])}</h1>']
    for heading, body in sections:
        markdown += [f"## {heading}", "", body, ""]
        plaintext += [heading, body, ""]
        html += [f'<h2 style="font-size:19px;">{escape(heading)}</h2>', f'<p {paragraph}>{escape(body)}</p>']
    markdown += ["## 参考来源", "", *(f"- {name}　{url}" for name, url in references)]
    plaintext += ["参考来源", *(f"{name}　{url}" for name, url in references)]
    html.append('<h2 style="font-size:19px;">参考来源</h2>')
    for name, url in references:
        if urlsplit(url).scheme in {"http", "https"}:
            html.append(f'<p {paragraph}><a href="{escape(url, quote=True)}">{escape(name)}</a>　{escape(url)}</p>')
    fragment = "\n".join(html)
    documents = {
        "card.md": render_card(card),
        "card.json": json.dumps(card | {"editorial": copy}, indent=2, ensure_ascii=False) + "\n",
        "draft.md": "\n".join(markdown) + "\n",
        "draft.txt": "\n".join(plaintext) + "\n",
        "draft.html": '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>公众号写作底稿</title>'
                      f'<body style="font-family:sans-serif;max-width:700px;margin:30px auto;padding:0 16px;">{fragment}</body></html>',
        "xiumi-fragment.html": fragment,
        "images.md": "\n".join(["# 配图建议", "", *("- " + value for value in copy["image_ideas"]),
                                  "", "## 来源与权利记录", "", *("- " + value for value in copy["image_sources"])]) + "\n",
    }
    for filename, body in documents.items():
        temporary = path / (filename + ".tmp")
        temporary.write_text(body, encoding="utf-8")
        temporary.replace(path / filename)
    return path
