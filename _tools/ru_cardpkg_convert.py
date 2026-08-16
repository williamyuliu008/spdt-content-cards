# -*- coding: utf-8 -*-
"""
ru_cardpkg_convert.py — SPDT-Content-Cards → rujing CardPackage 转换器
- 输入: spdt-content-cards 1 套卡片（chain.json + main.json + K*.json）
- 输出: rujing CardPackage JSON（v3 格式）
- 字段映射:
  - card_type: KNOWLEDGE → NODE / STRATEGY 透传 / 其他 → STRATEGY 或 CHAIN
  - chain_role: EVENT → RESULT / 其他透传
  - chain_id: 去掉 "history/" 前缀

用法:
  python ru_cardpkg_convert.py --card-dir 历史/cards/2026-08-16_监察谏议制度
  python ru_cardpkg_convert.py --card-dir 历史/cards/2026-08-16_监察谏议制度 --output D:/tmp/rujing_xxx.json
"""
import sys, io, json, argparse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 字段映射表
# ============================================================

# card_type 映射（rujing 端只认 NODE/STRATEGY/CHAIN）
CARD_TYPE_MAP = {
    "KNOWLEDGE": "NODE",         # 子卡（单点）→ 节点
    "STRATEGY": "STRATEGY",      # 主卡（叙事+策略）→ 心法
    "CHAIN": "CHAIN",
    "CASE_STUDY": "STRATEGY",    # 案例 → 心法
    "METHODOLOGY": "STRATEGY",   # 方法论 → 心法
    "BIG_PICTURE": "CHAIN",      # 宏观 → 链
    "PARADOX": "STRATEGY",       # 悖论 → 心法
}

# chain_role 映射（rujing 用 RESULT 代替 EVENT）
CHAIN_ROLE_MAP = {
    "EVENT": "RESULT",           # autoclaw 的 EVENT → rujing 的 RESULT
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
}

# ChainType 映射（rujing 5 个枚举）
CHAIN_TYPE_MAP = {
    "因果链": "因果链",
    "时序链": "时序链",
    "对比链": "对比链",
    "要素链": "要素链",
    "理论运用链": "理论运用链",
    "PATTERN": "规律链",  # autoclaw 没指定时默认
    "PROCESS": "时序链",  # 演进链 → 时序链
    "BIG_PICTURE": "理论运用链",
    "STRATEGY": "因果链",  # 战略链 → 因果链
}


def normalize_card_type(t: str) -> str:
    """autoclaw v1.0 6 值 → rujing 3 值"""
    return CARD_TYPE_MAP.get(t, "NODE")  # 未知默认 NODE


def normalize_chain_role(r: str) -> str:
    """autoclaw 6 值 → rujing 6 值（EVENT → RESULT）"""
    return CHAIN_ROLE_MAP.get(r, "PROCESS")  # 未知默认 PROCESS


def normalize_subject(s: str) -> str:
    """英文 → 中文"""
    return SUBJECT_MAP.get(s, s)


def normalize_chain_type(t: str) -> str:
    """中英文混合 → rujing 5 值"""
    return CHAIN_TYPE_MAP.get(t, "因果链")


def normalize_chain_id(cid: str) -> str:
    """去掉 'history/' 前缀等"""
    if cid.startswith("history/"):
        return cid[len("history/"):]
    return cid


def convert_one_card(card_json: dict, chain_id_short: str, chain_title: str) -> dict:
    """转换 1 张卡（主卡或子卡）→ rujing Card"""
    return {
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
    }


def convert_chain_to_cardpackage(chain_dir: Path) -> dict:
    """读 chain_dir 下的所有 JSON，转为 rujing CardPackage"""
    # 读 chain.json
    chain = json.loads((chain_dir / "chain.json").read_text(encoding="utf-8-sig"))
    # 读 main.json
    main_card = json.loads((chain_dir / "main.json").read_text(encoding="utf-8-sig"))
    # 读 K*.json
    sub_cards = []
    for f in sorted(chain_dir.iterdir()):
        if re.fullmatch(r"K\d{2}\.json", f.name):
            sub = json.loads(f.read_text(encoding="utf-8-sig"))
            sub_cards.append(sub)

    chain_id_full = chain["chain_id"]
    chain_id_short = normalize_chain_id(chain_id_full)
    chain_title = chain["chain_title"]
    subject_zh = normalize_subject(chain.get("subject", "HISTORY"))
    chain_type = normalize_chain_type(chain.get("chain_type", "因果链"))

    # 主卡 → strategy_cards
    main_rujing = convert_one_card(main_card, chain_id_short, chain_title)

    # 子卡 → node_cards
    sub_rujing = [convert_one_card(s, chain_id_short, chain_title) for s in sub_cards]

    # 构造 CardPackage
    pkg = {
        "version": "v3",
        "series": f"SPDT-Content-Cards / {subject_zh}",
        "total_chains": 1,
        "total_cards": 1 + len(sub_rujing),
        "node_cards": sub_rujing,
        "strategy_cards": [main_rujing],
    }

    # 附：链元数据（用于 importChainMeta）
    chain_meta = {
        "chain_id": chain_id_short,
        "chain_title": chain_title,
        "chain_type": chain_type,
        "subject": subject_zh,
        "narrative": main_card.get("back_detail", ""),  # 主卡叙事 = 链叙事
        "related_chains": [],
        "tags": main_card.get("tags", []),
        "card_count": 1 + len(sub_rujing),
    }

    return {"package": pkg, "chain_meta": chain_meta, "chain_id_short": chain_id_short}


import re  # 放在这里避免顶部未用警告


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

    # 同时输出 chain_meta（用于 importChainMeta）
    meta_path = out_path.parent / f"chain_meta_{card_dir.name}.json"
    # 链元数据格式：数组（兼容 v1 裸数组格式）
    meta_path.write_text(json.dumps([chain_meta], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[链元数据] {meta_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
