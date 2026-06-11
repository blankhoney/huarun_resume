from huarun_app.schemas import SafetyLabel


RED_KEYWORDS = (
    "加量",
    "减量",
    "停药",
    "停掉",
    "换药",
    "混着吃",
    "一起吃",
    "合并用药",
    "胸痛",
    "呼吸困难",
    "喘不上气",
    "过敏",
    "严重过敏",
    "过敏性休克",
    "自杀",
)

RED_PATTERNS = (
    ("判断", "是不是"),
    ("能不能", "继续吃"),
    ("还能", "继续吃"),
    ("可以", "继续吃"),
)

YELLOW_KEYWORDS = (
    "副作用",
    "不舒服",
    "胃疼",
    "胃痛",
    "恶心",
    "头晕",
    "皮疹",
    "发热",
    "腹泻",
    "不良反应",
)


def classify_question(question: str) -> SafetyLabel:
    normalized = question.strip().lower()
    if any(keyword.lower() in normalized for keyword in RED_KEYWORDS):
        return "red"
    if any(all(part.lower() in normalized for part in pattern) for pattern in RED_PATTERNS):
        return "red"
    if any(keyword.lower() in normalized for keyword in YELLOW_KEYWORDS):
        return "yellow"
    return "green"


def should_refuse(label: SafetyLabel) -> bool:
    return label == "red"
