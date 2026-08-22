# -*- coding: utf-8 -*-
"""
ru_cardpkg_convert.py — SPDT-Content-Cards → rujing CardPackage 转换器
v6.0 (2026-08-18) 产品级升级：
  - 主卡 back_detail 升级为 chain.article（链长文）
  - 主卡 exam_questions 升级为 chain.self_test（链级自测题）
  - card 字段扩展：sources / exam_questions / parent_card / confidence
  - chain_meta 扩展：article / self_test / version / update_log
  - chain_meta 扩展：domain / lines / module / topic / is_main_line / status
  - package.chain_meta[] 数组（让 importCardPackage 一次读 chain_meta）
  - card_type / chain_role / subject 映射保持不变
  - 兼容旧版本：narrative 字段保留（旧 4 幕剧本）

用法:
  python ru_cardpkg_convert.py --card-dir 历史/cards/2026-08-16_监察谏议制度
  python ru_cardpkg_convert.py --card-dir 地理/cards/2026-08-16_热力环流与风 --output D:/tmp/rujing_xxx.json
"""
import sys, io, json, argparse, re
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 字段映射表
# ============================================================

# card_type 映射（rujing 端只认 NODE/STRATEGY/CHAIN）
CARD_TYPE_MAP = {
    "KNOWLEDGE": "NODE",
    "STRATEGY": "STRATEGY",
    "CHAIN": "CHAIN",
    "CASE_STUDY": "STRATEGY",
    "METHODOLOGY": "STRATEGY",
    "BIG_PICTURE": "CHAIN",
    "PARADOX": "STRATEGY",
}

# chain_role 映射（rujing 用 RESULT 代替 EVENT）
CHAIN_ROLE_MAP = {
    "EVENT": "RESULT",
    "BACKGROUND": "BACKGROUND",
    "TRIGGER": "TRIGGER",
    "PROCESS": "PROCESS",
    "COUNTER": "COUNTER",
    "PATTERN": "PATTERN",
}

# Subject 映射（autoclaw 用英文，rujing 用中文）
SUBJECT_MAP = {
    "HISTORY": "历史",
    "GEOGRAPHY": "地理",
    "POLITICS": "政治",
    "GUWEN": "古诗文",
    "CALLIGRAPHY": "书法",
    "ENGLISH": "英语",
    "BIOLOGY": "生物",
    "CHEMISTRY": "化学",
    "PHYSICS": "物理",
}

# ChainType 映射
CHAIN_TYPE_MAP = {
    "因果链": "因果链",
    "时序链": "时序链",
    "对比链": "对比链",
    "要素链": "要素链",
    "理论运用链": "理论运用链",
    "PATTERN": "规律链",
    "PROCESS": "时序链",
    "BIG_PICTURE": "理论运用链",
    "STRATEGY": "因果链",
}

# confidence 映射
CONFIDENCE_MAP = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def normalize_card_type(t: str) -> str:
    return CARD_TYPE_MAP.get(t, "NODE")


def normalize_chain_role(r: str) -> str:
    return CHAIN_ROLE_MAP.get(r, "PROCESS")


def normalize_subject(s: str) -> str:
    return SUBJECT_MAP.get(s, s)


def normalize_chain_type(t: str) -> str:
    return CHAIN_TYPE_MAP.get(t, "因果链")


def normalize_chain_id(cid: str) -> str:
    """去掉 'history/' 'geography/' 等前缀"""
    prefixes = ["history/", "geography/", "politics/", "guwen/", "calligraphy/",
                "english/", "biology/", "chemistry/", "physics/"]
    for p in prefixes:
        if cid.startswith(p):
            return cid[len(p):]
    return cid


def convert_one_card(card_json: dict, chain_id_short: str, chain_title: str, is_main: bool = False) -> dict:
    """转换 1 张卡（主卡或子卡）→ rujing Card
    v6.0: 增加 sources / exam_questions / parent_card / confidence
    """
    card = {
        "card_id": card_json["card_id"],
        "chain_id": chain_id_short,
        "chain_title": chain_title,
        "card_type": normalize_card_type(card_json.get("card_type", "KNOWLEDGE")),
        "chain_role": normalize_chain_role(card_json.get("chain_role", "PROCESS")),
        "front": card_json.get("front", ""),
        "back_core": card_json.get("back_core", ""),
        "back_detail": card_json.get("back_detail", ""),
        "maturity": "RAW",
        "tags": card_json.get("tags", []),
        # v6.0 新增
        "sources": card_json.get("sources", []),
        "confidence": CONFIDENCE_MAP.get(card_json.get("confidence", "medium"), "medium"),
    }
    # parent_card 仅子卡有
    if not is_main and "parent_card" in card_json:
        card["parent_card"] = card_json["parent_card"]
    else:
        card["parent_card"] = ""
    # 主卡有 exam_questions
    if is_main and "exam_questions" in card_json:
        card["exam_questions"] = card_json["exam_questions"]
    else:
        card["exam_questions"] = []
    return card


def build_chain_meta(chain: dict, main_card: dict, sub_cards: list, subject_zh: str,
                     chain_id_short: str, chain_title: str, chain_type: str) -> dict:
    """构造 v6.0 chain_meta
    - article: 主卡 back_detail 升级（链长文 1000-5000 字）
    - self_test: 主卡 exam_questions 升级（链级自测题）
    - version: 1.0.0 (首次导入)
    - update_log: 单条首次导入记录
    - domain / lines / module / topic / is_main_line / status: 从 chain.json 读
    """
    now_iso = "2026-08-18"  # 占位，rujing 端用 Date.now() 重写
    return {
        "chain_id": chain_id_short,
        "chain_title": chain_title,
        "chain_type": chain_type,
        "subject": subject_zh,
        # 兼容旧版 narrative 字段（如果有）
        "narrative": "",
        "related_chains": [],
        "tags": main_card.get("tags", []),
        "card_count": 1 + len(sub_cards),
        # v6.0 新增
        "article": main_card.get("back_detail", ""),
        "self_test": main_card.get("exam_questions", []),
        "version": "1.0.0",
        "update_log": [
            {
                "version": "1.0.0",
                "date": now_iso,
                "summary": "v6.0 首次导入",
                "author": "autoclaw"
            }
        ],
        "domain": chain.get("domain", subject_zh),  # 默认 = subject
        "lines": chain.get("lines", []),
        "module": chain.get("module", ""),
        "topic": chain.get("topic", ""),
        "is_main_line": chain.get("is_main_line", False),
        "status": chain.get("status", "trial_production"),
    }


def convert_chain_to_cardpackage(chain_dir: Path) -> dict:
    """读 chain_dir 下的所有 JSON，转为 rujing CardPackage (v6.0)"""
    chain = json.loads((chain_dir / "chain.json").read_text(encoding="utf-8-sig"))
    main_card = json.loads((chain_dir / "main.json").read_text(encoding="utf-8-sig"))
    sub_cards = []
    for f in sorted(chain_dir.iterdir()):
        if re.fullmatch(r"K\d{2}\.json", f.name):
            sub = json.loads(f.read_text(encoding="utf-8-sig"))
            sub_cards.append(sub)

    chain_id_full = chain["chain_id"]
    chain_id_short = normalize_chain_id(chain_id_full)
    chain_title = chain["chain_title"]
    subject_raw = chain.get("subject", "HISTORY")

    # 学科推断：spdt-content-cards 仓库 autoclaw 试产卡按父目录归类
    chain_dir_name = chain_dir.name
    if chain_dir_name.startswith("2026-08-16_"):
        parent_dir_name = chain_dir.parent.parent.name if chain_dir.parent.parent.exists() else ""
        if parent_dir_name == "地理":
            subject_zh = "地理"
        elif parent_dir_name == "政治":
            subject_zh = "政治"
        elif parent_dir_name == "历史":
            subject_zh = "历史"  # 历史学科 v6.0 也按真实学科
        else:
            subject_zh = "专题系列"
    else:
        subject_zh = normalize_subject(subject_raw)

    chain_type = normalize_chain_type(chain.get("chain_type", "因果链"))

    # 主卡 → strategy_cards (is_main=True)
    main_rujing = convert_one_card(main_card, chain_id_short, chain_title, is_main=True)
    # 子卡 → node_cards
    sub_rujing = [convert_one_card(s, chain_id_short, chain_title, is_main=False) for s in sub_cards]

    # 构造 v6.0 chain_meta
    chain_meta = build_chain_meta(chain, main_card, sub_cards, subject_zh,
                                   chain_id_short, chain_title, chain_type)

    # 构造 CardPackage
    pkg = {
        "version": "v6.0",
        "series": f"SPDT-Content-Cards / {subject_zh} / {chain_title}",
        "total_chains": 1,
        "total_cards": 1 + len(sub_rujing),
        "node_cards": sub_rujing,
        "strategy_cards": [main_rujing],
        # v6.0 新增：链元数据数组（让 importCardPackage 一次读）
        "chain_meta": [chain_meta],
    }

    return {"package": pkg, "chain_meta": chain_meta, "chain_id_short": chain_id_short}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-dir", required=True, help="套卡目录路径")
    parser.add_argument("--output", default=None, help="输出 JSON 路径（默认 /tmp/rujing_<concept>.json）")
    args = parser.parse_args()

    card_dir = Path(args.card_dir)
    if not card_dir.exists():
        print(f"❌ 目录不存在: {card_dir}")
        return 1

    print(f"[转换] 读 {card_dir}")
    result = convert_chain_to_cardpackage(card_dir)
    pkg = result["package"]
    chain_meta = result["chain_meta"]

    # 输出路径
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path("/tmp") / f"rujing_{card_dir.name}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[输出] {out_path} ({out_path.stat().st_size} 字节)")
    print(f"[统计] 主卡: 1 / 子卡: {len(pkg['node_cards'])} / 链: {pkg['total_chains']}")
    print(f"[链元数据] {chain_meta['chain_id']} / {chain_meta['subject']} / {chain_meta['chain_type']}")
    print(f"[v6.0] article={len(chain_meta['article'])} 字 / self_test={len(chain_meta['self_test'])} 题 / version={chain_meta['version']}")
    print(f"[v6.0] domain={chain_meta['domain']} / lines={chain_meta['lines']} / module={chain_meta['module']} / topic={chain_meta['topic']}")

    # 同时输出 chain_meta（用于 importChainMeta）
    meta_path = out_path.parent / f"chain_meta_{card_dir.name}.json"
    meta_path.write_text(json.dumps([chain_meta], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[链元数据] {meta_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
