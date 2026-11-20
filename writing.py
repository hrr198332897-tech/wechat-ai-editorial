"""Turn a candidate and its evidence into editable Chinese article copy."""
import re
from dataclasses import dataclass

from models import Item


@dataclass(frozen=True)
class Profile:
    hook: str
    question: str
    baseline: str
    developer: str
    business: str
    reader: str
    figure: str


PROFILES = {
    "模型发布": Profile(
        "已经开放什么，用在哪类任务上？",
        "把发布公告拆成能力、访问方式和使用限制",
        "在同一任务上对照前版，记录模型版本、费用和失败样本",
        "用一条现有任务试跑，记录输入限制、输出与返回错误",
        "核对地区、套餐、数据条款与单位任务成本，再决定是否试点",
        "先按自己的账号检查入口，用同一份素材比较前后效果",
        "用一张自制卡片并列展示模型入口、适用任务和使用限制",
    ),
    "工具更新": Profile(
        "升级前先看这次改了哪一步",
        "以现有工作流为例，定位会受影响的那一步",
        "对照前版发行记录，用相同配置跑一次旧版和新版",
        "检查变更记录、配置兼容和失败回退方式",
        "选一条日常任务比较耗时、人工改动与升级风险",
        "先查当前版本，确认自己用得到对应功能再尝试",
        "画一张自制的升级前后操作流程图",
    ),
    "技术研究": Profile(
        "实验回答了什么，还有哪些问题要复现？",
        "从研究问题和实验设置入手，逐项交代对照和复现条件",
        "在同一数据集、指标和硬件预算下比较作者方法与论文基线",
        "检查代码、权重、数据与复现说明是否发布",
        "用与实际场景相近的样本，核对部署成本和外部有效性",
        "先看研究回答的问题有没有对应的可用产品入口",
        "自绘实验设置、指标和基线关系图，并标明数据出处",
    ),
    "真实应用": Profile(
        "这次应用替代了工作流里的哪一步？",
        "把案例拆成输入、AI 处理和人工复核，标出可量化结果",
        "比较同团队同类任务引入 AI 前后的质量、耗时和返工",
        "梳理系统输入、失败样本和人工接管点",
        "区分试点与生产，核实样本范围、节省工时和额外成本",
        "沿用一个熟悉场景判断自己实际能省下哪些操作",
        "根据公开事实自己绘制工作流，标出可核实的人工环节",
    ),
    "算力与基建": Profile(
        "这项基础设施变化会影响哪笔部署成本？",
        "把硬件、服务范围和测算条件连到具体部署场景",
        "在同一模型、精度、批量和负载下对照吞吐与单位任务成本",
        "检查框架、驱动、精度和硬件兼容要求",
        "把价格、可用区、吞吐及容量约束放在同一张测算表",
        "核对性能变化是否已经反映到自己所用服务的费用或响应时间",
        "自绘从算力规格到单位任务成本的换算表，标上测算条件",
    ),
    "政策": Profile(
        "何时生效，哪些主体需要关注？",
        "按条款原文区分适用范围、落实时间与执行主体",
        "逐条对照前版文件，记录延续条款、改动条款和生效节点",
        "从条款中提取产品角色、功能边界与留档要求",
        "以正式原文核实适用主体、执行节点与内部责任分工",
        "找出政策对具体使用场景的影响及正式查询入口",
        "自制生效时间线并注明对应条文和发布机关",
    ),
    "开源项目": Profile(
        "动手前先查安装门槛和许可证",
        "从仓库、可运行示例和许可证判断项目能解决什么",
        "按同一输入跑仓库示例及已有工具，记录安装和结果差异",
        "检查最小示例、依赖锁定、版本与许可证文件",
        "核实项目维护与商业使用条件，准备替换或回退方案",
        "先看有无可用体验入口，以及运行要多少资源",
        "以自行运行的示例截图展示输入、输出和所用版本",
    ),
    "产业动态": Profile(
        "这项变动会先影响哪些产品或用户？",
        "从公开披露确认参与方、执行范围和用户可见变化",
        "对照原来的产品入口、服务范围或合作安排，标出有出处的变动",
        "关注接口、服务迁移和开发计划是否公布",
        "核对合同义务、上线范围和可能的替代方案",
        "确认现有账号、使用方式或费用是否真的发生变化",
        "用自绘时间线展示官方披露与公开执行节点",
    ),
}


@dataclass(frozen=True)
class Feature:
    label: str
    pattern: str
    hook: str
    check: str


FEATURES = (
    Feature("透明 PNG", r"transparent (?:backgrounds? (?:in|for) )?png|(?:原生 |支持 )?透明\s*PNG|PNG\s*透明背景",
            "透明 PNG 怎么接到现有出图流程？", "用同一素材查看输出文件是否保留透明通道"),
    Feature("RGBA 输出", r"(?:native )?rgba (?:image )?(?:output|export)|(?:原生\s*)?RGBA\s*(?:图片|图像)?\s*(?:生成|输出|导出)",
            "RGBA 输出怎么接到后期合成？", "用同一张图检查透明通道和合成兼容性"),
    Feature("分层导出", r"(?:exports?|outputs?|produces?|supports?) (?:[\w -]{0,35} )?(?:separate|multiple|editable) layers|分层导出|拆分图层|输出.{0,12}图层",
            "分层导出能省掉哪些返工？", "导出同一素材，核对各图层能否独立编辑"),
    Feature("视频首尾帧", r"first[- ]and[- ]last[- ]frame|first and last frames|首尾帧",
            "首尾帧控制适合哪种视频任务？", "用同一组首尾帧复测时长、过渡与输出限制"),
    Feature("模型权重", r"(?:model )?weights (?:are |now )?available (?:for download|on hugging face)|(?:released?|download) (?:the )?(?:model )?weights|权重.{0,12}(?:可下载|已开放|已发布)",
            "权重怎么获取，本地跑要准备什么？", "核对实际下载入口、权重格式、许可和最低资源要求"),
    Feature("上下文缓存", r"context cach(?:e|ing)|prompt cach(?:e|ing)|上下文缓存|提示词缓存",
            "上下文缓存在哪类重复任务里值得测试？", "对照同一负载的缓存命中、过期规则与计费"),
    Feature("工具调用", r"tool calls?|tool calling|function calls?|function calling|工具调用|函数调用",
            "工具调用要在哪条现有流程里试？", "以同一工具定义核对调用成功率、参数错误与失败回退"),
    Feature("多模态输入", r"multimodal inputs?|(?:accepts?|supports?) (?:both )?(?:image and text|text and image|video input)|多模态输入|图片输入|视频输入",
            "多模态输入能接到哪些手头任务里？", "用一份实际素材核对输入格式、大小及输出质量"),
    Feature("计费调整", r"(?:updates?|changed?|new|cuts?|lower) (?:its |the )?pricing|(?:pricing|prices) (?:changes?|updates?|cuts?)|调(?:整|低|高)价格|价格调整|计费(?:更新|调整)",
            "计费哪里变了，换算成单次任务是多少？", "核对套餐、计费单位、生效条件和同任务费用"),
    Feature("公开 API", r"public api|available (?:via|through|in|on) (?:the )?(?:\w+ ){0,3}api|开放\s*API|API\s*(?:已)?上线",
            "公开 API 怎么接入，先核对这三项", "逐一核对访问资格、接口限制与单位任务费用"),
)

_CAUTION = re.compile(
    r"\b(?:will|would|could|might|may|plan(?:s|ned)?|upcoming|not|no|without|previously|"
    r"unsupported|requested|suggested|coming soon|roadmap|hopes?)\b|"
    r"将支持|将推出|尚未|暂无|未支持|不支持|不包含|计划|拟于|预计|未来|即将|考虑|曾(?:经)?支持",
    re.I,
)
_ADDITION = re.compile(r"\b(?:adds?|added|introduces?|introduced) (?:new )?support (?:for|to)\b|首次支持|新增(?:原生|支持)?", re.I)
_REMOVAL = re.compile(r"\b(?:remove[sd]?|deprecat\w+|drops?|stop(?:s|ped) supporting)\b|移除|停止支持|废弃", re.I)
_VERSION = re.compile(r"(?<![\w.])v\d+(?:\.\d+){1,3}(?:[-.]?(?:alpha|beta|rc)[-.]?\d*)?(?![\w.])", re.I)
_MODEL = re.compile(
    r"(?<!\w)(?:GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Kimi|GLM|Doubao|Seedance|Seedream|Gemma|"
    r"Mistral|Grok|Codex)[ -]?(?:[A-Za-z]{1,12}[- ])?\d+(?:\.\d+){0,2}"
    r"(?:[- ](?:Pro|Flash|Max|Ultra|Mini|Opus|Sonnet|Haiku|Thinking|Turbo|Lite|[0-9]+[Bb]))?\b",
    re.I,
)


def _clean(value: str) -> str:
    return " ".join(str(value or "").split())


def _subject(primary: Item, subject: str) -> str:
    name = _clean(subject or primary.subject)
    model = _MODEL.search(primary.title)
    if model and (not name or model.group(0).casefold().startswith(name.casefold())):
        name = model.group(0)
    name = name or _clean(primary.source) or "本次更新"
    version = _VERSION.search(primary.title)
    if primary.kind == "repository" and version and version.group().casefold() not in name.casefold():
        name += f" {version.group()}"
    return name[:56].rstrip()


def _feature(evidence_text: str, category: str) -> tuple[Feature | None, bool]:
    if category in {"技术研究", "政策", "产业动态", "算力与基建"}:
        return None, False
    sentences = [
        segment for segment in re.split(r"[。！？!?；;]+|(?<!\d)\.\s+|\.\s+(?=[A-Z])|\n", evidence_text)
        if segment.strip() and not _CAUTION.search(segment)
    ]
    for feature in FEATURES:
        for segment in sentences:
            match = re.search(feature.pattern, segment, flags=re.I)
            if match:
                prefix = segment[max(0, match.start() - 80):match.start()]
                added = bool(_ADDITION.search(prefix)) and not _REMOVAL.search(segment)
                return feature, added
    return None, False


def _quoted_fragment(excerpt: str) -> str:
    short = " ".join(excerpt.split()[:16])[:80].rstrip()
    return short + "…" if len(short) < len(excerpt) else short


def build_copy(
    primary: Item,
    evidence: dict,
    category: str,
    subject: str,
    note: str = "",
    *,
    include_draft: bool = True,
) -> dict:
    """Generate an attributed draft. Callers enforce the approval gate before exporting."""
    profile = PROFILES.get(category, PROFILES["产业动态"])
    name = _subject(primary, subject)
    matched = evidence.get("matched") is True and primary.kind in {"official", "repository", "research", "discovery"}
    excerpt = _clean(evidence.get("excerpt", "")) if matched and primary.kind != "discovery" else ""
    feature, added = _feature(excerpt, category)
    source = _clean(primary.source) or "所列原始来源"
    published = primary.published or ""
    date = published[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", published) else ""
    date_prefix = f"{date}，" if date else ""
    if primary.kind == "research" or category == "技术研究":
        publisher = "论文作者"
        object_label = "研究及实验设置"
    elif category == "政策":
        publisher = source
        object_label = "公开文件及适用范围"
    elif primary.kind in {"repository", "discovery"}:
        publisher = "仓库维护者"
        object_label = "发布记录及仓库材料"
    else:
        publisher = source
        object_label = "发布内容及开放范围"

    if feature:
        change = f"{publisher}的原始材料提到{feature.label}。具体使用条件可回到参考来源核对。"
        opening = f"{date_prefix}{publisher}的材料提到{feature.label}。如果你想把它用到已有流程里，可以先{feature.check}。"
    elif matched:
        title = _clean(evidence.get("title") or primary.title)[:140]
        change = f"一手页面已匹配《{title}》。具体改动按原始材料逐项核对。"
        opening = f"{date_prefix}原始材料《{title}》提供了{object_label}。本文从一个具体问题切入，{profile.question}。"
    else:
        change = "待核实一手页面、发布范围与适用条件。"
        opening = f"关于{name}的这条消息仍待核实。先找到对应发布记录和使用条件，再判断读者能据此做什么。"

    headline = f"{name}｜{feature.hook if feature else profile.hook}"
    use_case = feature.check if feature else profile.question
    previous = (evidence.get("previous") or {}) if matched else {}
    previous_title = _clean(previous.get("title", "")) if previous.get("url") else ""
    baseline = f"前版《{previous_title[:100]}》可作对照。" if previous_title else "前版比较待核实。"
    if feature and added:
        baseline = f"{publisher}将{feature.label}列为本次新增。" + (
            baseline if previous_title else ""
        )
    comparison = f"{baseline}{profile.baseline}。"
    abstract = f"{change} 这篇文章拟从读者可以检查的条件切入，{use_case}。"
    takeaways = {"开发者": profile.developer, "企业": profile.business, "普通用户": profile.reader}
    outline = [
        f"读者先看什么｜{use_case}。",
        f"一手来源说了什么｜回到{publisher}的{object_label}。",
        f"和以前怎么比｜{profile.baseline}。",
        "谁会用到｜给开发者、企业、普通用户各一个可检查的条件。",
    ]
    draft = []
    if include_draft:
        proof = change
        if excerpt:
            proof += f" {publisher}材料中的原文线索为“{_quoted_fragment(excerpt)}”。"
        if matched and (category == "技术研究" or primary.kind == "research"):
            proof += " 引用作者报告的结果时，需要注明数据集与对照组。"
        audience = "。".join(f"{reader}可以{action}" for reader, action in takeaways.items()) + "。"
        draft = [
            ("导语", opening),
            ("公告或材料确认了什么", proof),
            ("怎样和以前比较", comparison),
            ("哪些人值得进一步试", audience),
        ]

    return {
        "headline": headline,
        "alternatives": [
            f"{name}的{feature.label}，先弄清这项条件" if feature else f"{name}这次更新，读者可以从哪里核对？",
            f"{name}｜从{feature.label}入手，看看现有流程要不要调整" if feature else f"{name}｜读公告时先核对这几项",
        ],
        "angle": f"用一个读者可以复查或复现的问题组织材料，{use_case}。",
        "abstract": abstract,
        "change": change,
        "comparison": comparison,
        "takeaways": takeaways,
        "impact": takeaways,
        "outline": outline,
        "draft": draft,
        "editor_note": _clean(note),
        "image_ideas": [
            profile.figure + "。",
            f"按实际核查结果，为{name}配一张带来源说明的事实卡。",
        ],
        "image_sources": [
            "自制示意图记录所用数据、链接和制作日期。运行截图需核实界面素材与使用许可，并处理账号信息。",
            "引用官方截图或论文图表前，核实许可、署名方式和转载范围。证据链接仅供核查。",
        ],
    }
