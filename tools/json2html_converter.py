# -*- coding: utf-8 -*-
"""
json2html_converter.py — spdt-content-cards JSON → 学习中心 HTML DATA 转换器

将 spdt-content-cards 仓库的 JSON 卡片集（chain.json + main.json + K*.json）
转换为学习中心 HTML 的 DATA 格式（带 AI 生产 bug 清洗）。

用法:
  python json2html_converter.py --all
  python json2html_converter.py --subject 地理
  python json2html_converter.py --subject 历史 --output D:/Z_学习平台/data/generated/history_gen.js
"""
import sys, io, json, re, argparse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 配置
# ============================================================
CARDS_ROOT = Path(r"D:\B_历史\spdt-content-cards")
OUTPUT_ROOT = Path(r"D:\Z_学习平台\data\generated")

SUBJECTS = {
    "历史": {"html_key": "history",   "dir": "历史",   "headers": ["#", "考点", "核心要点", "易混辨析", "角度"]},
    "地理": {"html_key": "geography", "dir": "地理",   "headers": ["#", "考点", "核心要点", "易混辨析", "角度"]},
    "政治": {"html_key": "politics",  "dir": "政治",   "headers": ["#", "考点", "核心要点", "易混辨析", "角度"]},
    # 以下学科尚未在 spdt-content-cards 中产出 JSON
    # "古诗文": {"html_key": "guwen",   "dir": "古诗文"},
    # "英语":   {"html_key": "english", "dir": "英语"},
}

# ============================================================
# 清洗函数：修复生产 AI 的重复文本 bug
# ============================================================

def dedup_lines(text: str) -> str:
    """去重完全相同的连续行（保留首次出现）"""
    lines = text.split("\n")
    result = []
    seen_block = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue
        if stripped in seen_block:
            continue
        seen_block.add(stripped)
        result.append(line)
    return "\n".join(result)

def clean_supplement(text: str) -> str:
    """去除重复的「补充说明」行（只保留第一次出现）"""
    pattern = r"(补充说明：[^\n]+(?:\n|$))"
    matches = list(re.finditer(pattern, text))
    if len(matches) <= 1:
        return text
    first = matches[0].group(0)
    cleaned = re.sub(pattern, "", text)
    insert_pos = matches[0].start()
    cleaned = cleaned[:insert_pos] + first + cleaned[insert_pos:]
    return cleaned.strip()

def clean_front(text: str) -> str:
    """清理 K 卡 front 中重复的「这一问，考的是什么？」"""
    text = re.sub(r"这一问，考的是什么？", "", text)
    return text.strip()

def clean_concept_repetition(text: str) -> str:
    """清理 back_detail 中重复的「这里涉及的核心概念是XXX。」"""
    text = re.sub(r"这里涉及的核心概念是[^。\n]*。?", "", text)
    text = re.sub(r"理解这一点，是[掌把]握本考点的关键所在。?", "", text)
    return text.strip()

def clean_back_core(text: str) -> str:
    """清理 back_core 中重复的填充句"""
    text = re.sub(r"理解这一点，是[掌把]握本考点的关键所在。?", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_card(text: str) -> str:
    """综合清洗"""
    text = clean_supplement(text)
    text = clean_concept_repetition(text)
    text = dedup_lines(text)
    return text.strip()

def extract_pitfalls(back_detail: str) -> str:
    """从 K 卡 back_detail 中提取易错点/易混辨析"""
    m = re.search(r"(?:⚠️\s*)?易错点[：:](.+?)(?:补充说明|这里涉及|$)", back_detail, re.S)
    if m:
        pitfalls = m.group(1).strip()
        pitfalls = re.sub(r"\n\s*-", "\n- ", pitfalls)
        return pitfalls
    lines = [l.strip() for l in back_detail.split("\n") if l.strip()]
    pitfall_lines = [l for l in lines if "❌" in l or "易错" in l or "注意" in l]
    if pitfall_lines:
        return "\n".join(pitfall_lines)
    return ""

def get_card_angle(tags: list) -> str:
    """从 tags 提取角度/范式标签"""
    for tag in tags:
        if tag.startswith("#content/"):
            return tag.replace("#content/", "")
        if tag.startswith("#考频/"):
            return tag.replace("#考频/", "")
    return ""

# ============================================================
# 转换核心
# ============================================================

def convert_one_concept(card_dir: Path, subject_cfg: dict) -> dict | None:
    """转换单个概念卡片集 -> HTML DATA 条目"""
    try:
        chain = json.loads((card_dir / "chain.json").read_text(encoding="utf-8-sig"))
        main_card = json.loads((card_dir / "main.json").read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"  [SKIP] {card_dir.name}: {e}")
        return None

    # 读子卡
    sub_cards = []
    for f in sorted(card_dir.iterdir()):
        if re.fullmatch(r"K\d{2}\.json", f.name):
            try:
                sub = json.loads(f.read_text(encoding="utf-8-sig"))
                sub_cards.append(sub)
            except Exception as e:
                print(f"  [WARN] {f.name}: {e}")

    # 概念名：chain_title 去括号
    concept_name = chain.get("chain_title", card_dir.name.split("_", 1)[-1] if "_" in card_dir.name else card_dir.name)
    concept_name = re.sub(r"（.*?）", "", concept_name).strip()
    # 如果目录名更简洁，用目录名
    dir_concept = card_dir.name.split("_", 1)[-1] if "_" in card_dir.name else card_dir.name
    if len(dir_concept) < len(concept_name):
        concept_name = dir_concept

    # --- body[] ---
    back_detail = main_card.get("back_detail", "")
    back_detail = clean_card(back_detail)
    paragraphs = [p.strip() for p in back_detail.split("\n\n") if p.strip()]
    body = []
    for i, p in enumerate(paragraphs):
        p = p.replace("\n", "<br>")
        body.append({"lead": i == 0, "text": p})

    # --- cards[] ---
    cards = []
    for idx, sub in enumerate(sub_cards, 1):
        front = clean_front(sub.get("front", ""))
        back_core = clean_back_core(sub.get("back_core", ""))
        sub_detail = clean_card(sub.get("back_detail", ""))
        pitfalls = extract_pitfalls(sub_detail)
        angle = get_card_angle(sub.get("tags", []))
        cards.append([str(idx), front, back_core, pitfalls, angle])

    # --- quiz[] ---
    quiz = []
    for q in main_card.get("exam_questions", []):
        qtype = f"{q.get('type', '')} · {q.get('exam_angle', '')}"
        quiz.append({
            "type": qtype,
            "body": q.get("body", ""),
            "ans": q.get("answer", "")
        })

    # --- tags / type ---
    body_type = "叙事体"
    for tag in main_card.get("tags", []):
        if tag.startswith("#content/"):
            body_type = tag.replace("#content/", "") + "体"
            break

    # --- status ---
    status = "JSON 自动转换（" + chain.get("generated_at", "") + "）"

    return {
        "concept_name": concept_name,
        "data": {
            "status": status,
            "tags": {
                "type": body_type,
                "headers": subject_cfg.get("headers", []),
                "source": "JSON 卡片自动转换"
            },
            "body": body,
            "cards": cards,
            "quiz": quiz
        }
    }

# ============================================================
# 输出 JS
# ============================================================

def js_escape(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "")
    return s

def format_body(body_list: list) -> str:
    parts = []
    for p in body_list:
        lead = "true" if p["lead"] else "false"
        parts.append(f"  {{ lead:{lead},text:'{js_escape(p['text'])}' }}")
    return ",\n".join(parts)

def format_cards(cards_list: list) -> str:
    parts = []
    for c in cards_list:
        cells = [f"'{js_escape(cell)}'" for cell in c]
        parts.append(f"  [{','.join(cells)}]")
    return ",\n".join(parts)

def format_quiz(quiz_list: list) -> str:
    parts = []
    for q in quiz_list:
        parts.append(f"  {{ type:'{js_escape(q['type'])}', body:'{js_escape(q['body'])}', ans:'{js_escape(q['ans'])}' }}")
    return ",\n".join(parts)

def generate_js(subject_zh: str, html_key: str, concepts: list, headers: list) -> str:
    """生成完整 JS 代码段"""
    lines = []
    lines.append(f"/* ---------- {subject_zh} JSON 自动转换（json2html_converter.py） ---------- */")
    lines.append(f"/* 加载顺序：在 generated 之前加载，curated 加载后会覆盖同名 key */")
    headers_json = json.dumps(headers, ensure_ascii=False)
    for c in concepts:
        cn = c["concept_name"]
        d = c["data"]
        body_type = d["tags"].get("type", "")
        source = d["tags"].get("source", "")
        lines.append(f"DATA.{html_key}['{js_escape(cn)}'] = {{")
        lines.append(f"  status:'{js_escape(d['status'])}',")
        lines.append(f"  tags:{{ type:'{js_escape(body_type)}', headers:{headers_json}, source:'{js_escape(source)}' }},")
        lines.append(f"  body:[")
        lines.append(format_body(d["body"]))
        lines.append(f"  ],")
        lines.append(f"  cards:[")
        lines.append(format_cards(d["cards"]))
        lines.append(f"  ],")
        lines.append(f"  quiz:[")
        lines.append(format_quiz(d["quiz"]))
        lines.append(f"  ]")
        lines.append(f"}};")
    return "\n".join(lines)

# ============================================================
# 入口
# ============================================================

def process_subject(subject_zh: str, output_path: Path | None = None) -> int:
    cfg = SUBJECTS[subject_zh]
    cards_dir = CARDS_ROOT / cfg["dir"] / "cards"
    if not cards_dir.exists():
        print(f"[{subject_zh}] 卡片目录不存在: {cards_dir}")
        return 0

    concept_dirs = sorted(d for d in cards_dir.iterdir() if d.is_dir())
    print(f"[{subject_zh}] 发现 {len(concept_dirs)} 个概念卡片集")

    concepts = []
    for cd in concept_dirs:
        result = convert_one_concept(cd, cfg)
        if result:
            concepts.append(result)
            print(f"  [OK] {result['concept_name']}")

    print(f"[{subject_zh}] 成功转换 {len(concepts)}/{len(concept_dirs)} 个概念")

    js_code = generate_js(subject_zh, cfg["html_key"], concepts, cfg.get("headers", []))

    if output_path is None:
        output_path = OUTPUT_ROOT / f"{cfg['html_key']}_gen.js"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(js_code, encoding="utf-8")
    print(f"[{subject_zh}] 输出: {output_path}  ({len(js_code)} 字节)")
    return len(concepts)

def main():
    parser = argparse.ArgumentParser(description="JSON 卡片 → 学习中心 HTML DATA 转换器")
    parser.add_argument("--all", action="store_true", help="转换全部已产出学科")
    parser.add_argument("--subject", choices=list(SUBJECTS.keys()), help="学科名称")
    parser.add_argument("--output", default=None, help="输出文件路径")
    args = parser.parse_args()

    if args.all:
        total = 0
        for s in SUBJECTS:
            total += process_subject(s)
        print(f"\n[完成] 共转换 {total} 条 JSON 卡片")
    elif args.subject:
        out_path = Path(args.output) if args.output else None
        process_subject(args.subject, out_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
