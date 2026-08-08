"""
SPDT-004 知识卡片入库器 + registry.json 生成器

功能：
  1. 扫描 core/ 目录，收集所有 cards.json
  2. 验证每张卡片的基本格式
  3. 生成 / 更新 core/_meta/registry.json（card_id → 元数据映射）
  4. 生成 / 更新 core/_meta/tag_dictionary.json（标签词典）

用法：
    # 扫描全库并重建 registry
    python import_card.py --scan

    # 导入单张新卡片（交互式）
    python import_card.py --add

    # 检查某批次卡片的格式合规性
    python import_card.py --check core/历史/古史_v4/cards.json
"""

import json
import sys
import os
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
CORE_ROOT = Path(__file__).parent.parent / "core"
META_DIR = CORE_ROOT / "_meta"
REGISTRY_PATH = META_DIR / "registry.json"
TAG_DICT_PATH = META_DIR / "tag_dictionary.json"


# ── 格式校验规则 ──────────────────────────────────────────────────

def validate_card(card: dict, card_id: str) -> list:
    """返回错误列表。空列表 = 通过。"""
    errors = []

    if not card.get("card_id"):
        errors.append("缺少 card_id 字段")

    if card.get("type") not in ("node", "strategy_cause", "strategy_impact",
                                 "strategy_turning", "chain"):
        errors.append(f"type 非法：{card.get('type')}")

    back = card.get("back", "")
    if len(back) < 30:
        errors.append(f"back 长度不足30字（当前{len(back)}字）")
    if back.count("因为") > 1 or back.count("所以") > 1:
        errors.append(f"back 可能违反原子性（多个因果连词）")

    return errors


def get_cardinality(card: dict) -> str:
    """判断卡片价值等级（materials 降权机制）。"""
    m = card.get("materials", {})
    if isinstance(m, dict):
        has_quote = bool(m.get("quote"))
        has_scene = bool(m.get("scene"))
    else:
        has_quote = has_scene = False

    if has_quote and has_scene:
        return "核心卡"
    elif has_quote or has_scene:
        return "标准卡"
    else:
        return "辅助卡"


def scan_core() -> tuple[list, dict]:
    """
    扫描 core/ 目录，返回 (全部卡片列表, 每批次元数据).
    """
    all_cards = []
    batch_meta = {}

    for cards_file in CORE_ROOT.rglob("cards.json"):
        # 跳过 _meta 目录
        if "_meta" in cards_file.parts:
            continue

        batch_dir = cards_file.parent
        metadata_file = batch_dir / "metadata.yaml"

        # 读批次元数据（纯文本解析，避免 yaml 依赖）
        batch_meta_raw = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.rstrip()
                        if ": " in line and not line.startswith(" "):
                            key, _, val = line.partition(": ")
                            batch_meta_raw[key.strip()] = val.strip().strip('"').strip("'")
            except Exception:
                pass

        # 读卡片
        with open(cards_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, dict):
                cards = raw.get("cards", raw.get("materials_cards", []))
            else:
                cards = raw

        for card in cards:
            card["_file"] = str(cards_file.relative_to(CORE_ROOT))
            card["_batch"] = batch_dir.name
            card["_cardinality"] = get_cardinality(card)
            all_cards.append(card)

        batch_meta[str(batch_dir.relative_to(CORE_ROOT))] = {
            "batch_id": batch_meta_raw.get("batch_id", batch_dir.name),
            "card_count": len(cards),
            "schema_version": batch_meta_raw.get("schema_version", "?"),
            "domain": batch_meta_raw.get("domain", ""),
            "generated_at": batch_meta_raw.get("generated_at", ""),
            "note": batch_meta_raw.get("note", ""),
        }

    return all_cards, batch_meta


def build_registry(cards: list) -> dict:
    """构建 registry.json。"""
    index = {}
    domains = {}
    by_type = {}
    cardinality_stats = {"核心卡": 0, "标准卡": 0, "辅助卡": 0}

    for card in cards:
        cid = card.get("card_id", "")
        if not cid:
            continue

        concepts = card.get("concepts", [])
        tags = card.get("tags", [])
        ctype = card.get("type", "")
        cardinality = card.get("_cardinality", "辅助卡")

        # 索引
        index[cid] = {
            "file": card.get("_file", ""),
            "batch": card.get("_batch", ""),
            "type": ctype,
            "concepts": concepts,
            "tags": tags,
            "version": card.get("metadata", {}).get("version", "v1.0") if isinstance(card.get("metadata"), dict) else "v1.0",
            "cardinality": cardinality,
            "inferred": card.get("metadata", {}).get("inferred", False) if isinstance(card.get("metadata"), dict) else False,
        }

        # 统计：领域
        for t in tags:
            if t.startswith("#domain/"):
                d = t.replace("#domain/", "")
                domains[d] = domains.get(d, 0) + 1

        # 统计：类型
        by_type[ctype] = by_type.get(ctype, 0) + 1

        # 统计：价值等级
        cardinality_stats[cardinality] += 1

    return {
        "updated_at": TODAY,
        "total_cards": len(index),
        "domains": domains,
        "by_type": by_type,
        "cardinality_stats": cardinality_stats,
        "index": index,
    }


def build_tag_dictionary(cards: list) -> dict:
    """构建 tag_dictionary.json（检测同义异标）。"""
    # 收集所有 tags 和 concepts
    all_tags = {}
    all_concepts = {}

    for card in cards:
        for t in card.get("tags", []):
            t_clean = t.lstrip("#")
            all_tags[t_clean] = all_tags.get(t_clean, 0) + 1

        for c in card.get("concepts", []):
            all_concepts[c] = all_concepts.get(c, 0) + 1

    # 常见同义标签组（手工维护，检测异标）
    synonyms = {
        "唐朝": ["唐", "唐代"],
        "决策": ["decision", "decision_point"],
        "藩镇割据": ["藩镇"],
        "常山之难": ["常山"],
        "篆籀笔法": ["篆籀气"],
    }

    suggestions = []
    for std, variants in synonyms.items():
        found = [v for v in variants if v in all_tags or std in all_tags]
        if len(found) > 1:
            suggestions.append({
                "standard": std,
                "variants_found": found,
                "suggestion": f"统一为「{std}」"
            })

    return {
        "updated_at": TODAY,
        "total_unique_tags": len(all_tags),
        "total_unique_concepts": len(all_concepts),
        "top_tags": sorted(all_tags.items(), key=lambda x: -x[1])[:30],
        "synonym_suggestions": suggestions,
    }


def run_scan():
    """执行全库扫描并重建 registry。"""
    META_DIR.mkdir(exist_ok=True)

    print(f"扫描 core/ 目录：{CORE_ROOT}")
    cards, batch_meta = scan_core()
    print(f"共发现 {len(cards)} 张卡片，{len(batch_meta)} 个批次")

    # 格式检查
    errors = []
    for card in cards:
        cid = card.get("card_id", f"<missing at {card.get('_file')}>")
        errs = validate_card(card, cid)
        if errs:
            errors.append({"card_id": cid, "errors": errs})

    if errors:
        print(f"\n格式警告：{len(errors)} 张卡片有问题")
        for e in errors[:10]:
            print(f"  [{e['card_id']}] {'; '.join(e['errors'])}")
        if len(errors) > 10:
            print(f"  …还有 {len(errors)-10} 张")
    else:
        print("格式检查：全部通过 ✅")

    # 写入 registry.json
    registry = build_registry(cards)
    registry["batch_meta"] = batch_meta

    with open(REGISTRY_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"registry.json 已写入：{REGISTRY_PATH}")

    # 写入 tag_dictionary.json
    tag_dict = build_tag_dictionary(cards)
    with open(TAG_DICT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tag_dict, f, ensure_ascii=False, indent=2)
    print(f"tag_dictionary.json 已写入：{TAG_DICT_PATH}")

    # 统计摘要
    print(f"\n── 全库统计 ──")
    print(f"  总卡片数：{registry['total_cards']}")
    print(f"  按领域：{registry['domains']}")
    print(f"  按类型：{registry['by_type']}")
    print(f"  价值等级：{registry['cardinality_stats']}")
    print(f"  标签词典：{tag_dict['total_unique_tags']} 个唯一标签，{tag_dict['total_unique_concepts']} 个唯一概念")
    if tag_dict["synonym_suggestions"]:
        print(f"  同义标签建议：{len(tag_dict['synonym_suggestions'])} 条")


if __name__ == "__main__":
    if "--scan" in sys.argv:
        run_scan()
    elif "--check" in sys.argv:
        idx = sys.argv.index("--check")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not path:
            print("用法：--check <cards.json>")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            cards = json.load(f)
        errors = []
        for card in cards:
            errs = validate_card(card, card.get("card_id", ""))
            if errs:
                errors.append({"card_id": card.get("card_id", ""), "errors": errs})
        if errors:
            print(f"发现 {len(errors)} 个问题：")
            for e in errors:
                print(f"  [{e['card_id']}] {'; '.join(e['errors'])}")
        else:
            print("全部通过 ✅")
    else:
        print(__doc__)
        print("\n用法示例：")
        print("  python import_card.py --scan    # 扫描全库并重建 registry")
        print("  python import_card.py --check core/历史/古史_v4/cards.json")
