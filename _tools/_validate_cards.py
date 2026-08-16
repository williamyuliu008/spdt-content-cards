# -*- coding: utf-8 -*-
"""
_validate_cards.py — 知识卡片 v1.0 规范校验器（试产用）
按规范 §7 质量硬指标 20 项 + §11 自检 10 项 + 与 _62_concepts.json 交叉核对。
用法: python3 _validate_cards.py [cards目录]
退出码: 0=全过  1=有错误  2=有警告(无错误)
"""
import json, os, re, sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\4_data\knowledge_cards\历史\cards")
CONCEPTS_PATH = Path(r"D:\4_data\knowledge_cards\00-项目文档\_62_concepts.json")

CARD_TYPE_ENUM = {"STRATEGY", "CASE_STUDY", "METHODOLOGY", "KNOWLEDGE", "BIG_PICTURE", "PARADOX"}
CHAIN_ROLE_ENUM = {"BACKGROUND", "TRIGGER", "PROCESS", "COUNTER", "PATTERN", "EVENT"}
CHAIN_FIELDS = ["chain_id", "chain_title", "subject", "domain", "lines", "module",
                "topic", "is_main_line", "total_cards", "generated_at", "generated_by",
                "status", "open_questions_count", "exam_questions_count"]
MAIN_FIELDS = ["card_id", "card_type", "chain_role", "maturity", "front", "back_core",
               "back_detail", "concepts", "tags", "sources", "exam_questions",
               "open_questions", "confidence"]
SUB_FIELDS = ["card_id", "card_type", "chain_role", "maturity", "front", "back_core",
              "back_detail", "concepts", "tags", "sources", "parent_card", "confidence"]
REL_TIME_HARD = ["同一时期", "与此同时", "不久后", "同时期", "同时代"]
REL_TIME_SOFT = ["同时"]
CONTENT_PREFIX = "#content/"
BANNED_FILENAME_CHARS = set("：；，。！？（）《》【】、")

errors, warns = [], []

def clen(s):
    return len(re.sub(r"\s", "", s))

def add_err(msg): errors.append(msg)
def add_warn(msg): warns.append(msg)

def scan_text(text, where):
    for w in REL_TIME_HARD:
        if w in text:
            add_err(f"[时间相对表述] {where} 含禁止词 '{w}'")
    for w in REL_TIME_SOFT:
        if w in text:
            add_warn(f"[时间相对表述·软] {where} 含 '{w}'，请人工确认非时间相对表述")

def check_enums(card, where):
    if card.get("card_type") not in CARD_TYPE_ENUM:
        add_err(f"[card_type] {where} 非法: {card.get('card_type')}")
    if card.get("chain_role") not in CHAIN_ROLE_ENUM:
        add_err(f"[chain_role] {where} 非法: {card.get('chain_role')}")
    if card.get("maturity") != "RAW":
        add_err(f"[maturity] {where} 应为 RAW: {card.get('maturity')}")
    if card.get("confidence") not in {"high", "medium", "low"}:
        add_err(f"[confidence] {where} 非法: {card.get('confidence')}")

def check_card(card, where, is_main, main_card_id=None):
    fields = MAIN_FIELDS if is_main else SUB_FIELDS
    missing = [f for f in fields if f not in card]
    if missing:
        add_err(f"[字段缺失] {where} 缺: {missing}")
        return
    check_enums(card, where)
    # front
    n = clen(card["front"])
    if not (30 <= n <= 100):
        add_err(f"[front长度] {where} {n}字 (需30~100)")
    if not card["front"].endswith("？"):
        add_err(f"[front问号] {where} 未以问号结尾")
    # back_core
    n = clen(card["back_core"])
    if not (150 <= n <= 250):
        add_err(f"[back_core长度] {where} {n}字 (需150~250)")
    # back_detail
    n = clen(card["back_detail"])
    lo, hi = (800, 1200) if is_main else (200, 350)
    if not (lo <= n <= hi):
        add_err(f"[back_detail长度] {where} {n}字 (需{lo}~{hi})")
    # concepts
    n = len(card["concepts"])
    lo, hi = (5, 8) if is_main else (3, 5)
    if not (lo <= n <= hi):
        add_err(f"[concepts数] {where} {n}个 (需{lo}~{hi})")
    # tags
    tags = card["tags"]
    if not any(t == "#domain/历史" for t in tags):
        add_err(f"[tags] {where} 缺 #domain/历史")
    if not any(t.startswith(CONTENT_PREFIX) for t in tags):
        add_err(f"[tags] {where} 缺 #content/...")
    if not any(t.startswith("#考频/") for t in tags):
        add_err(f"[tags] {where} 缺 #考频/...")
    if not any(t.startswith("#朝代/") for t in tags):
        add_err(f"[tags] {where} 缺 #朝代/...")
    # sources
    srcs = card["sources"]
    if not (3 <= len(srcs) <= 8 if is_main else 1 <= len(srcs) <= 3):
        add_err(f"[sources数] {where} {len(srcs)}条 (需{'3~8' if is_main else '1~3'})")
    if not any(s.get("type") == "academic" for s in srcs):
        add_err(f"[sources] {where} 无 type=academic 条目")
    for s in srcs:
        if "type" not in s or "source" not in s or "detail" not in s or "url" not in s:
            add_err(f"[sources字段] {where} 条目缺 type/source/detail/url 字段: {s}")
    # 主卡 exam/open
    if is_main:
        eq = card["exam_questions"]
        if not (5 <= len(eq) <= 6):
            add_err(f"[exam题数] {where} {len(eq)}道 (需5~6)")
        types = [q.get("type") for q in eq]
        for need in ["单选", "配对", "图表排序", "材料解析", "开放论述"]:
            if need not in types:
                add_err(f"[题型缺失] {where} 缺 '{need}' 题")
        for q in eq:
            if "开放" in str(q.get("type", "")):
                ans = str(q.get("answer", ""))
                if not ("1~3" in ans and "4~6" in ans and "7~8" in ans):
                    add_err(f"[三层给分] {where} 开放题缺三层给分: {q.get('id')}")
        oq = card["open_questions"]
        if not (5 <= len(oq) <= 10):
            add_err(f"[open题数] {where} {len(oq)}条 (需5~10)")
        for i, o in enumerate(oq, 1):
            if clen(o) > 50:
                add_err(f"[open超长] {where} 存疑#{i} 超过50字 ({clen(o)}字)")
        # confidence 算法核对 (§4.8)
        algo = "high" if len(oq) == 0 else ("medium" if len(oq) <= 3 else "low")
        if card["confidence"] != algo:
            add_warn(f"[confidence] {where} 自评 {card['confidence']} 与§4.8算法({len(oq)}条→{algo})不一致")
    else:
        if card.get("parent_card") != main_card_id:
            add_err(f"[parent_card] {where} = {card.get('parent_card')}, 主卡 = {main_card_id}")
    # 概念必须出现在正文 (§4.4 软检查)
    text = card["back_core"] + card["back_detail"]
    for c in card["concepts"]:
        if c not in text:
            add_warn(f"[概念-正文] {where} 概念 '{c}' 未在 back_core/back_detail 出现")
    # 时间表述扫描
    scan_text(card["front"] + card["back_core"] + card["back_detail"], where)

def main():
    if len(sys.argv) > 1:
        base = Path(sys.argv[1])
    else:
        base = BASE
    concepts = json.loads(CONCEPTS_PATH.read_text(encoding="utf-8-sig"))
    cmap = {c["id"]: c for c in concepts}
    sets = sorted(d for d in base.iterdir() if d.is_dir())
    if not sets:
        add_err(f"cards 目录下无套卡目录: {base}")
    for sdir in sets:
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})_(.+)", sdir.name)
        if not m:
            add_err(f"[目录名] {sdir.name} 不符合 YYYY-MM-DD_概念名")
            continue
        date_part, cname = m.group(1), m.group(2)
        files = sorted(f.name for f in sdir.iterdir())
        # 目录内非预期文件
        allowed = {"chain.json", "main.json"} | {f"K{i:02d}.json" for i in range(1, 11)}
        unexpected = [f for f in files if f not in allowed]
        if unexpected:
            add_err(f"[目录结构] {sdir.name} 含非预期文件: {unexpected}")
        ks = sorted(f for f in files if re.fullmatch(r"K\d{2}\.json", f))
        if not (6 <= len(ks) <= 10):
            add_err(f"[子卡数] {sdir.name} K卡 {len(ks)} 张 (需6~10)")
        # BOM 检查
        for f in sdir.iterdir():
            if f.read_bytes()[:3] == b"\xef\xbb\xbf":
                add_err(f"[BOM] {f.name} 含 UTF-8 BOM")
        # JSON 合法性 + 字段
        try:
            chain = json.loads((sdir / "chain.json").read_text(encoding="utf-8"))
        except Exception as e:
            add_err(f"[JSON] {sdir.name}/chain.json 解析失败: {e}")
            continue
        try:
            main = json.loads((sdir / "main.json").read_text(encoding="utf-8"))
        except Exception as e:
            add_err(f"[JSON] {sdir.name}/main.json 解析失败: {e}")
            continue
        missing = [f for f in CHAIN_FIELDS if f not in chain]
        if missing:
            add_err(f"[chain字段] {sdir.name} 缺: {missing}")
        # chain 与概念清单交叉核对
        cm = re.fullmatch(r"history/H-M(\d)-(\d+)-(.+)", chain.get("chain_id", ""))
        if not cm:
            add_err(f"[chain_id格式] {sdir.name}: {chain.get('chain_id')}")
        else:
            mod, cid, cnm = int(cm.group(1)), int(cm.group(2)), cm.group(3)
            if cnm != cname:
                add_err(f"[概念名] {sdir.name} 目录名'{cname}' ≠ chain_id概念'{cnm}'")
            cc = cmap.get(cid)
            if cc is None:
                add_err(f"[概念清单] id={cid} 不在 _62_concepts.json")
            else:
                if cc["name"] != cname:
                    add_err(f"[概念名] {sdir.name} ≠ 清单 name '{cc['name']}'")
                if cc["lines"] != chain.get("lines"):
                    add_err(f"[lines] {sdir.name} chain={chain.get('lines')} ≠ 清单 {cc['lines']}")
                if cc["star"] != chain.get("is_main_line"):
                    add_err(f"[is_main_line] {sdir.name} {chain.get('is_main_line')} ≠ 清单star {cc['star']}")
                if cc["module"] != chain.get("module"):
                    add_err(f"[module] {sdir.name} '{chain.get('module')}' ≠ 清单 '{cc['module']}'")
                if cc["topic"] != chain.get("topic"):
                    add_err(f"[topic] {sdir.name} '{chain.get('topic')}' ≠ 清单 '{cc['topic']}'")
                expect_cid = f"H-M{mod}-{cid}-MAIN-001"
                if main.get("card_id") != expect_cid:
                    add_err(f"[card_id] 主卡 {main.get('card_id')} ≠ 期望 {expect_cid}")
        if chain.get("total_cards") != len(ks):
            add_err(f"[total_cards] {sdir.name} chain={chain.get('total_cards')} ≠ 实际K卡 {len(ks)}")
        if chain.get("open_questions_count") != len(main.get("open_questions", [])):
            add_err(f"[open_questions_count] {sdir.name} chain={chain.get('open_questions_count')} ≠ 实际 {len(main.get('open_questions', []))}")
        if chain.get("exam_questions_count") != len(main.get("exam_questions", [])):
            add_err(f"[exam_questions_count] {sdir.name} chain={chain.get('exam_questions_count')} ≠ 实际 {len(main.get('exam_questions', []))}")
        if chain.get("subject") != "HISTORY":
            add_err(f"[subject] {sdir.name}: {chain.get('subject')}")
        if chain.get("status") != "trial_production":
            add_err(f"[status] {sdir.name}: {chain.get('status')}")
        if chain.get("generated_at") != date_part:
            add_err(f"[generated_at] {sdir.name}: {chain.get('generated_at')} ≠ 目录日期 {date_part}")
        check_card(main, f"{sdir.name}/main.json", True)
        for k in ks:
            try:
                sub = json.loads((sdir / k).read_text(encoding="utf-8"))
            except Exception as e:
                add_err(f"[JSON] {sdir.name}/{k} 解析失败: {e}")
                continue
            check_card(sub, f"{sdir.name}/{k}", False, main.get("card_id"))
            if not re.fullmatch(r"H-M\d+-\d+-K\d{2}-001", sub.get("card_id", "")):
                add_err(f"[card_id格式] {sdir.name}/{k}: {sub.get('card_id')}")
            if f"K{k[1:3]}" not in sub.get("card_id", ""):
                add_err(f"[card_id-K序号] {sdir.name}/{k}: {sub.get('card_id')}")
        # 文件名合法字符
        for f in files:
            bad = [ch for ch in f if ch in BANNED_FILENAME_CHARS]
            if bad:
                add_err(f"[文件名] {sdir.name}/{f} 含中文标点: {bad}")

    print("=" * 60)
    print(f"校验范围: {base}")
    print(f"套卡数: {len(sets)} | 错误: {len(errors)} | 警告: {len(warns)}")
    print("=" * 60)
    for e in errors:
        print("[ERR] " + e)
    for w in warns:
        print("[WARN] " + w)
    if not errors and not warns:
        print("PASS: 全部通过（20 项硬指标 + 交叉核对）")
    print("=" * 60)
    sys.exit(1 if errors else (2 if warns else 0))

if __name__ == "__main__":
    main()
