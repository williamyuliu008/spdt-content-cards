"""
SPDT-004 标签一致性审计 + 缺口检测报告生成器

功能：
  1. 扫描全库，统计标签分布，检测同义异标
  2. 缺口检测：按 chain 扫描，标记 materials 层为空的卡片
  3. 输出审计报告（JSON + 可读摘要）

用法：
    python tag_audit.py [--out <report.json>]
"""

import json
import sys
from pathlib import Path
from datetime import date
from collections import defaultdict

TODAY = date.today().isoformat()
CORE_ROOT = Path(__file__).parent.parent / "core"
OUT_PATH = Path(__file__).parent.parent / "reports" / "tag_audit_report.json"


# ── 同义词词典（手工维护，发现新模式后补充）───────────────────────
# key = 标准词，value = 变体列表
SYNONYM_DICT = {
    "唐朝": ["唐", "唐代"],
    "安史之乱": ["安史"],
    "藩镇割据": ["藩镇"],
    "常山之难": ["常山"],
    "篆籀笔法": ["篆籀气"],
    "颜体": ["颜楷"],
    "decision_point": ["decision", "抉择点"],
}


def scan_all_cards():
    """扫描 core/ 返回全部卡片列表。"""
    cards = []
    for cards_file in CORE_ROOT.rglob("cards.json"):
        if "_meta" in cards_file.parts:
            continue
        with open(cards_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, dict):
                c = raw.get("cards", raw.get("materials_cards", []))
            else:
                c = raw
            for card in c:
                card["_file"] = str(cards_file.relative_to(CORE_ROOT))
                card["_batch"] = cards_file.parent.name
                m = card.get("materials", {})
                if isinstance(m, dict):
                    card["_mat"] = m
                else:
                    card["_mat"] = {"quote": "", "scene": "", "data": ""}
                meta = card.get("metadata", {})
                card["_inferred"] = meta.get("inferred", False) if isinstance(meta, dict) else False
                cards.append(card)
    return cards


def audit_tags(cards: list) -> dict:
    """标签审计：词频统计 + 同义异标检测。"""
    tag_freq = defaultdict(int)
    concept_freq = defaultdict(int)
    for c in cards:
        for t in c.get("tags", []):
            tag_freq[t.lstrip("#")] += 1
        for co in c.get("concepts", []):
            concept_freq[co] += 1

    # 检测同义异标
    synonym_issues = []
    for std, variants in SYNONYM_DICT.items():
        found = [v for v in variants if v in tag_freq or std in tag_freq]
        if len(found) > 1:
            synonym_issues.append({
                "standard": std,
                "variants": found,
                "suggestion": f"建议统一为「{std}」",
                "affected_cards": []
            })
            # 找受影响的卡片
            for card in cards:
                for t in card.get("tags", []):
                    if t.lstrip("#") in variants and t.lstrip("#") != std:
                        synonym_issues[-1]["affected_cards"].append({
                            "card_id": card.get("card_id", ""),
                            "batch": card.get("_batch", ""),
                            "bad_tag": t.lstrip("#")
                        })

    # 标签覆盖率
    tagged_cards = sum(1 for c in cards if c.get("concepts"))
    tagged_pct = tagged_cards / len(cards) * 100 if cards else 0

    return {
        "total_unique_tags": len(tag_freq),
        "total_unique_concepts": len(concept_freq),
        "top_tags": sorted(tag_freq.items(), key=lambda x: -x[1])[:20],
        "top_concepts": sorted(concept_freq.items(), key=lambda x: -x[1])[:20],
        "tagged_card_count": tagged_cards,
        "tagged_card_pct": round(tagged_pct, 1),
        "synonym_issues": synonym_issues,
    }


def detect_gaps(cards: list) -> dict:
    """缺口检测：materials 层为空 / inferred 标注缺失。"""
    gaps = {
        "materials_empty": [],      # materials 全部为空
        "materials_partial": [],     # materials 部分为空
        "inferred_missing": [],     # 推断内容未标注 inferred
        "sources_empty": [],        # 无来源
        "chain_gaps": defaultdict(list),  # chain_id → 空 materials 的卡片
    }

    for c in cards:
        cid = c.get("card_id", "")
        ctype = c.get("type", "")
        batch = c.get("_batch", "")
        back = c.get("back", "")
        mat = c.get("_mat", {})
        sources = c.get("sources", [])

        has_quote = bool(mat.get("quote"))
        has_scene = bool(mat.get("scene"))
        has_data = bool(mat.get("data"))

        entry = {
            "card_id": cid,
            "type": ctype,
            "batch": batch,
            "front": c.get("front", ""),
            "has_quote": has_quote,
            "has_scene": has_scene,
            "has_data": has_data,
        }

        if ctype in ("node", "strategy_cause", "strategy_impact"):
            if not has_quote and not has_scene and not has_data:
                gaps["materials_empty"].append(entry)
            elif not has_quote or not has_scene:
                gaps["materials_partial"].append(entry)
        elif not has_quote and not has_scene and not has_data:
            gaps["materials_partial"].append(entry)

        # 来源为空
        if not sources or all(s.get("type") == "ai_generated" for s in sources):
            gaps["sources_empty"].append({
                "card_id": cid,
                "type": ctype,
                "batch": batch,
                "is_ai_generated": sources and sources[0].get("type") == "ai_generated"
            })

        # inferred 缺失检测（back 包含推断性词汇但未标注）
        inferral_signals = ["可能", "据说", "传说", "推测", "估计", "推断"]
        has_inferral_signal = any(s in back for s in inferral_signals)
        if has_inferral_signal and not c.get("_inferred", False):
            gaps["inferred_missing"].append({
                "card_id": cid,
                "type": ctype,
                "batch": batch,
                "signal": [s for s in inferral_signals if s in back]
            })

    # 按 chain 汇总
    chain_map = defaultdict(list)
    for c in cards:
        chain_id = c.get("metadata", {}).get("chain_id", "") if isinstance(c.get("metadata"), dict) else ""
        if chain_id:
            mat = c.get("_mat", {})
            if not (mat.get("quote") or mat.get("scene") or mat.get("data")):
                chain_map[chain_id].append(c.get("card_id", ""))

    return {
        "materials_empty_count": len(gaps["materials_empty"]),
        "materials_partial_count": len(gaps["materials_partial"]),
        "materials_empty": gaps["materials_empty"][:20],
        "materials_partial": gaps["materials_partial"][:20],
        "sources_empty_count": len(gaps["sources_empty"]),
        "sources_empty": gaps["sources_empty"][:20],
        "inferred_missing_count": len(gaps["inferred_missing"]),
        "inferred_missing": gaps["inferred_missing"][:15],
        "chains_with_gaps": {k: v for k, v in chain_map.items() if v},
    }


def generate_summary(audit: dict, gaps: dict) -> str:
    """生成可读摘要文本。"""
    lines = [
        f"标签审计报告 · {TODAY}",
        "=" * 40,
        f"总卡片数：{audit['tagged_card_count']} 张",
        f"唯一标签：{audit['total_unique_tags']} 个",
        f"唯一概念：{audit['total_unique_concepts']} 个",
        f"标签填充率：{audit['tagged_card_pct']}%",
        "",
        "── 缺口统计 ──",
        f"materials 完全为空：{gaps['materials_empty_count']} 张",
        f"materials 部分为空：{gaps['materials_partial_count']} 张",
        f"无来源引用：{gaps['sources_empty_count']} 张",
        f"推断内容未标注 inferred：{gaps['inferred_missing_count']} 张",
        "",
        "── 同义异标问题 ──",
    ]
    if audit["synonym_issues"]:
        for issue in audit["synonym_issues"]:
            lines.append(f"  · 「{issue['standard']}」有 {len(issue['variants'])} 种写法：{issue['variants']}")
    else:
        lines.append("  无发现 ✅")

    lines.append("")
    lines.append("── Top 10 标签 ──")
    for tag, cnt in audit["top_tags"][:10]:
        lines.append(f"  #{tag} × {cnt}")

    lines.append("")
    lines.append("── Top 10 概念 ──")
    for co, cnt in audit["top_concepts"][:10]:
        lines.append(f"  {co} × {cnt}")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args()

    print("扫描全库……")
    cards = scan_all_cards()
    print(f"共 {len(cards)} 张卡片")

    print("标签审计……")
    audit = audit_tags(cards)
    print(f"  唯一标签：{audit['total_unique_tags']}，唯一概念：{audit['total_unique_concepts']}")
    print(f"  同义异标：{len(audit['synonym_issues'])} 条")

    print("缺口检测……")
    gaps = detect_gaps(cards)

    # 生成摘要
    summary = generate_summary(audit, gaps)
    print("\n" + summary)

    # 写入 JSON 报告
    report = {
        "generated_at": TODAY,
        "total_cards": len(cards),
        "tag_audit": audit,
        "gap_detection": gaps,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已写入：{out_path}")

    # 写入纯文本摘要
    txt_path = out_path.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(summary)
    print(f"摘要已写入：{txt_path}")


if __name__ == "__main__":
    main()
