"""
SPDT-004 知识卡片格式迁移脚本
迁移：v1.2（card_id + type + tags + front + back）
    → v1.3（+ concepts[] + sources[] + materials{} + metadata{}）

用法：
    python migrate_cards_v1v2_to_v1v3.py <输入文件.json> [--out <输出文件.json>]

示例：
    python migrate_cards_v1v2_to_v1v3.py ep01_颜真卿_cards.json
    python migrate_cards_v1v2_to_v1v3.py 古史_v4_全18链_标签版.json --out 古史_v4_全18链_v1.3.json

迁移规则：
    1. concepts[]      → 若缺失，初始化为空[]（旧格式无此字段，概念提取需人工审核）
    2. sources[]       → 若缺失，初始化为空[]（建议人工补充来源信息）
    3. materials{}     → 若缺失，初始化为{}；若存在 materials.scene（字符串），保留
    4. metadata{}      → 若缺失，初始化为 {version: 'v1.0', created_at: 今日, updated_at: 今日}
    5. materials.scene → 若原值为字符串（旧格式），迁移到 materials.scene（字符串字段）
                          注意：v1.3 的 materials.scene 仍是字符串，无需解构

⚠️  重要：自动提取的 concepts[] 仅作占位符，须经人工审核后使用。
"""

import json
import sys
import os
import re
from datetime import date
from pathlib import Path

TODAY = date.today().isoformat()

# ── 概念粗提取词典 ────────────────────────────────────────────────
# key: tag 前缀 / 关键词 → value: 对应 concepts[] 候选
# 用于从现有 tags[] 中提取 concepts[] 的启发式规则
# 手动维护：每次发现新模式后补充
CONCEPT_EXTRACT_RULES = {
    # 领域 → 直接作为 concept
    "安史之乱": "安史之乱",
    "藩镇": "藩镇割据",
    "颜真卿": "颜真卿",
    "颜杲卿": "颜杲卿",
    "颜季明": "颜季明",
    "祭侄文稿": "祭侄文稿",
    "颜体": "颜体",
    "篆籀气": "篆籀笔法",
    "屋漏痕": "屋漏痕",
    "书品即人品": "书品即人品",
    "忠烈": "忠烈书风",
    "唐代书法": "唐代书法",
    "唐代": "唐朝",
    "唐": "唐朝",
    "平原郡": "平原郡",
    "常山": "常山之难",
    "科举": "科举制度",
    "九品中正": "九品中正制",
    "门阀": "门阀士族",
    "士族": "门阀士族",
    "两税法": "两税法",
    "均田制": "均田制",
    "府兵": "府兵制",
    "安禄山": "安禄山",
    "玄宗": "唐玄宗",
    "杨贵妃": "杨贵妃",
    "李林甫": "李林甫",
    "高力士": "高力士",
    "制度背景": "制度",
    "决策": "决策",
    "影响": "影响",
    "战争": "战争",
    "政治": "政治",
    "地理": "地理",
    "书法": "书法",
    "技法": "技法",
}

# tags 中直接作为 concepts 的前缀模式（去掉 # 和 / 后取最后一段）
DIRECT_CONCEPT_PATTERNS = [
    "安史之乱", "藩镇割据", "藩镇", "颜真卿", "颜杲卿", "颜季明",
    "祭侄文稿", "篆籀气", "屋漏痕", "书品即人品", "常山之难",
]


def rough_extract_concepts(tags: list) -> list:
    """从 tags[] 中启发式提取 concepts[]。不完美，需人工审核。"""
    concepts = set()

    for tag in tags:
        # 去掉 # 前缀
        tag_clean = tag.lstrip("#")

        # 匹配已知规则
        for keyword, concept in CONCEPT_EXTRACT_RULES.items():
            if keyword in tag_clean:
                concepts.add(concept)

        # 直接模式：取最后一段（最具体的概念）
        parts = tag_clean.split("/")
        if parts:
            last = parts[-1].strip()
            # 排除常见泛标签
            if last and last not in ("历史", "唐", "书法", "影响", "决策", "战争",
                                     "政治", "地理", "技法", "考频", "content",
                                     "domain", "strategy", "narrative", "新",
                                     "旧", "人", "物", "事件"):
                concepts.add(last)

    return sorted(list(concepts))


def migrate_card(card: dict) -> tuple[dict, list]:
    """
    将单张卡片从 v1.2 迁移到 v1.3。
    返回：(迁移后的卡片, 迁移说明列表)
    """
    notes = []
    card = dict(card)  # 不修改原对象

    # 1. concepts[] — 若缺失，初始化为空[]
    if "concepts" not in card:
        # 尝试从 tags 粗提取
        rough = rough_extract_concepts(card.get("tags", []))
        if rough:
            card["concepts"] = rough
            notes.append(f"[自动] 从 tags 提取 concepts：{rough}（需人工审核）")
        else:
            card["concepts"] = []
            notes.append("[需补充] concepts[] 为空，建议人工审核 back 后补充")
    else:
        notes.append("[保留] concepts[] 已存在")

    # 2. sources[] — 若缺失，初始化为空[]
    if "sources" not in card:
        card["sources"] = []
        notes.append("[需补充] sources[] 为空，建议补充来源引用")
    else:
        notes.append("[保留] sources[] 已存在")

    # 3. materials{} — 若缺失，初始化为{}
    #    旧格式中 materials 可能直接是字符串（materials.scene 的旧写法）
    #    v1.3 中 materials.scene 也是字符串字段，无需特殊解构
    if "materials" not in card:
        card["materials"] = {"quote": "", "scene": "", "data": ""}
        notes.append("[自动] 初始化空 materials{}")
    else:
        # 旧格式可能是字符串（materials.scene 的值直接放在 materials）
        # 也可能是 {"scene": "..."} 或 {"quote": "..."}
        mat = card["materials"]
        if isinstance(mat, str):
            card["materials"] = {"quote": "", "scene": mat, "data": ""}
            notes.append("[自动] materials 字符串迁移到 materials.scene")
        else:
            # 确保三个子字段都存在
            card["materials"] = {
                "quote": mat.get("quote", ""),
                "scene": mat.get("scene", ""),
                "data": mat.get("data", ""),
            }
            notes.append("[保留] materials{} 已存在")

    # 4. metadata{} — 若缺失，初始化默认值
    if "metadata" not in card:
        card["metadata"] = {
            "chain_id": "",
            "version": "v1.0",
            "inferred": False,
            "created_at": TODAY,
            "updated_at": TODAY,
            "created_by": "",
            "changelog": [],
            "note": ""
        }
        notes.append(f"[自动] 初始化 metadata{{}}，version=v1.0，created_at={TODAY}")
    else:
        # 确保所有子字段存在
        meta = card["metadata"]
        defaults = {
            "chain_id": "",
            "version": meta.get("version", "v1.0"),
            "inferred": False,
            "created_at": TODAY,
            "updated_at": TODAY,
            "created_by": "",
            "changelog": [],
            "note": ""
        }
        for k, v in defaults.items():
            if k not in meta:
                meta[k] = v
        card["metadata"] = meta
        notes.append("[保留] metadata{} 已存在，补充缺失子字段")

    return card, notes


def migrate_file(input_path: str, output_path: str | None = None) -> dict:
    """
    迁移整个卡片包文件。
    返回迁移报告。
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在：{input_path}")

    if output_path is None:
        stem = input_path.stem
        output_path = input_path.parent / f"{stem}_v1.3.json"
    else:
        output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    if not isinstance(cards, list):
        # 兼容 P1 批处理格式：{"materials_cards": [...], "report_title": "..."}
        if isinstance(cards, dict) and "materials_cards" in cards:
            cards = cards["materials_cards"]
        else:
            raise ValueError(f"卡片包应为 JSON 数组，实际为 {type(cards)}")

    migrated = []
    reports = []

    for i, card in enumerate(cards):
        migrated_card, notes = migrate_card(card)
        migrated.append(migrated_card)

        card_id = card.get("card_id", f"<第{i+1}张>")
        reports.append({
            "card_id": card_id,
            "type": card.get("type", "unknown"),
            "migration_notes": notes,
        })

    # 写入输出文件
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    # 统计
    needs_concepts_review = sum(
        1 for r in reports
        if any("需人工审核" in n or "需补充" in n for n in r["migration_notes"])
    )
    auto_migrated = len(reports) - needs_concepts_review

    return {
        "input": str(input_path),
        "output": str(output_path),
        "total_cards": len(cards),
        "auto_migrated": auto_migrated,
        "needs_review": needs_concepts_review,
        "report": reports,
        "note": "concepts[] 自动提取结果需人工审核；sources[] 建议补充来源；materials{} 空值需后续填充"
    }


def print_report(report: dict):
    print(f"\n{'='*60}")
    print(f"  迁移报告：{report['input']}")
    print(f"{'='*60}")
    print(f"  输入：{report['input']}")
    print(f"  输出：{report['output']}")
    print(f"  总卡片数：{report['total_cards']}")
    print(f"  自动完成：{report['auto_migrated']} 张")
    print(f"  需人工审核：{report['needs_review']} 张")
    print()

    needs_review = [r for r in report["report"]
                     if any("需" in n for n in r["migration_notes"])]
    if needs_review:
        print(f"  ⚠️  需人工审核的卡片（{len(needs_review)} 张）：")
        for r in needs_review[:10]:  # 最多显示10条
            print(f"    [{r['card_id']}] {r['type']}")
            for n in r["migration_notes"]:
                if "需" in n:
                    print(f"      → {n}")
        if len(needs_review) > 10:
            print(f"    …还有 {len(needs_review)-10} 张未列出")
    else:
        print("  ✅ 全部卡片迁移完成，无需人工审核")

    print()
    print(f"  迁移后文件：{report['output']}")
    print(f"  注意：concepts[] 自动提取结果仅供参考，请务必人工审核！")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None

    # 解析 --out 参数
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    report = migrate_file(input_file, output_file)
    print_report(report)
