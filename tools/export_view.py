"""
SPDT-004 场景视图导出器

支持导出：
  --scenario writing    写作素材池（跨包聚合，保留完整 v1.3 格式）
  --scenario exam       考点卡包（精简字段，back ≤ 100字，适配记忆软件）
  --scenario graph      知识图谱数据（节点+边，适配 Gephi/Cytoscape）

用法：
    # 写作聚合包（按概念筛选）
    python export_view.py --scenario writing --concepts "安史之乱,颜真卿" --out views/writing_ansm.json

    # 考点卡包（按考频标签筛选）
    python export_view.py --scenario exam --tags "考频" --out views/exam_ansm.json

    # 知识图谱数据
    python export_view.py --scenario graph --out views/knowledge_graph/graph_data.json

    # materials 覆盖率统计
    python export_view.py --scenario stats --out views/stats.json
"""

import json
import sys
from pathlib import Path
from datetime import date
from collections import defaultdict

TODAY = date.today().isoformat()
CORE_ROOT = Path(__file__).parent.parent / "core"


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
                card["_mat"] = m if isinstance(m, dict) else {"quote": "", "scene": "", "data": ""}
                cards.append(card)
    return cards


def filter_cards(cards: list, concepts: list | None, tags: list | None) -> list:
    """按 concepts[] 或 tags[] 筛选卡片。"""
    if not concepts and not tags:
        return cards

    result = []
    for c in cards:
        if concepts:
            card_concepts = [x.lower() for x in c.get("concepts", [])]
            if not any(x.lower() in card_concepts for x in concepts):
                continue
        if tags:
            card_tags = [x.lstrip("#").lower() for x in c.get("tags", [])]
            if not any(x.lower() in card_tags for x in tags):
                continue
        result.append(c)
    return result


def cardinality(c: dict) -> str:
    """判断卡片价值等级。"""
    m = c.get("_mat", {})
    has_quote = bool(m.get("quote"))
    has_scene = bool(m.get("scene"))
    if has_quote and has_scene:
        return "核心卡"
    elif has_quote or has_scene:
        return "标准卡"
    return "辅助卡"


def materials_stats(cards: list) -> dict:
    """materials 覆盖率统计。"""
    total = len(cards)
    if total == 0:
        return {}

    stats = defaultdict(int)
    for c in cards:
        stats[cardinality(c)] += 1

    mat_fields = defaultdict(int)
    for c in cards:
        m = c.get("_mat", {})
        if m.get("quote"): mat_fields["quote"] += 1
        if m.get("scene"): mat_fields["scene"] += 1
        if m.get("data"): mat_fields["data"] += 1

    by_type = defaultdict(lambda: defaultdict(int))
    for c in cards:
        by_type[c.get("type", "")][cardinality(c)] += 1

    return {
        "total": total,
        "cardinality": dict(stats),
        "materials_fields": dict(mat_fields),
        "by_type": {k: dict(v) for k, v in by_type.items()},
        "coverage_pct": {
            "core": round(stats.get("核心卡", 0) / total * 100, 1),
            "has_any": round(
                (stats.get("核心卡", 0) + stats.get("标准卡", 0)) / total * 100, 1
            ),
        }
    }


# ── 导出器 ──────────────────────────────────────────────────────────

def export_writing(cards: list, concepts: list | None, tags: list | None) -> dict:
    """写作素材池导出。保留完整 v1.3 格式，按 chain_id 排序。"""
    filtered = filter_cards(cards, concepts, tags)

    # 按 chain_id 排序
    def chain_sort_key(c):
        chain = c.get("metadata", {}).get("chain_id", "") if isinstance(c.get("metadata"), dict) else ""
        if chain:
            return (0, chain)
        return (1, c.get("_batch", ""), c.get("card_id", ""))

    filtered.sort(key=chain_sort_key)

    # 精简输出（去掉内部字段）
    output_cards = []
    for c in filtered:
        m = c.get("_mat", {})
        meta = c.get("metadata", {})
        output_cards.append({
            "card_id": c.get("card_id", ""),
            "type": c.get("type", ""),
            "front": c.get("front", ""),
            "back": c.get("back", ""),
            "concepts": c.get("concepts", []),
            "tags": c.get("tags", []),
            "sources": c.get("sources", []),
            "materials": {
                "quote": m.get("quote", ""),
                "scene": m.get("scene", ""),
                "data": m.get("data", ""),
            },
            "metadata": {
                "chain_id": meta.get("chain_id", "") if isinstance(meta, dict) else "",
                "version": meta.get("version", "v1.0") if isinstance(meta, dict) else "v1.0",
                "cardinality": cardinality(c),
            } if isinstance(meta, dict) else {"cardinality": cardinality(c)},
        })

    # 统计
    stats = materials_stats(filtered)
    concepts_found = set()
    batches_found = set()
    for c in filtered:
        concepts_found.update(c.get("concepts", []))
        batches_found.add(c.get("_batch", ""))

    return {
        "scenario": "writing_pool",
        "exported_at": TODAY,
        "total_cards": len(filtered),
        "filter_concepts": concepts or [],
        "filter_tags": tags or [],
        "batches": sorted(batches_found),
        "materials_stats": stats,
        "unique_concepts": sorted(concepts_found),
        "cards": output_cards,
    }


def export_exam(cards: list, concepts: list | None, tags: list | None) -> dict:
    """考点卡包导出。精简字段，back ≤ 100字，适配记忆软件。"""
    filtered = filter_cards(cards, concepts, tags)

    # 提取考频标签
    def extract_frequency(card: dict) -> str:
        for t in card.get("tags", []):
            if "考频" in t or "frequency" in t.lower():
                # 提取星数
                stars = [c for c in t if c in "⭐★☆"]
                if stars:
                    return "".join(stars)
                return "中"
        return "低"

    def trim_back(text: str, limit: int = 100) -> str:
        """截断 back 到指定字数，保留完整句子。"""
        if len(text) <= limit:
            return text
        # 找最后一个可断句的位置
        for sep in "。！？；":
            idx = text[:limit].rfind(sep)
            if idx > limit * 0.6:
                return text[:idx + 1]
        return text[:limit] + "…"

    exam_cards = []
    for c in filtered:
        exam_cards.append({
            "front": c.get("front", ""),
            "back": trim_back(c.get("back", "")),
            "concepts": c.get("concepts", []),
            "tags": [t for t in c.get("tags", []) if "考频" in t or "#考频" in t],
            "frequency": extract_frequency(c),
            "type": c.get("type", ""),
            "source_batch": c.get("_batch", ""),
            "cardinality": cardinality(c),
        })

    return {
        "scenario": "exam_cards",
        "exported_at": TODAY,
        "total_cards": len(exam_cards),
        "filter_concepts": concepts or [],
        "filter_tags": tags or [],
        "card_count": len(exam_cards),
        "cards": exam_cards,
    }


def export_graph(cards: list, concepts: list | None, tags: list | None) -> dict:
    """知识图谱数据导出。适配 Gephi（nodes.csv + edges.csv）或 Cytoscape JSON。"""
    filtered = filter_cards(cards, concepts, tags)

    nodes = []
    edges = []
    node_ids = set()

    # 节点：每张卡片
    for c in filtered:
        cid = c.get("card_id", "")
        ctype = c.get("type", "")
        concepts_list = c.get("concepts", [])
        batch = c.get("_batch", "")

        # 概念节点
        for concept in concepts_list:
            concept_id = f"C:{concept}"
            if concept_id not in node_ids:
                nodes.append({
                    "id": concept_id,
                    "label": concept,
                    "type": "concept",
                    "batch": "",
                })
                node_ids.add(concept_id)

            edges.append({
                "source": cid,
                "target": concept_id,
                "type": "card_has_concept",
                "weight": 1,
            })

        # 卡片节点
        if cid not in node_ids:
            nodes.append({
                "id": cid,
                "label": c.get("front", "")[:30] or cid,
                "type": ctype,
                "batch": batch,
                "cardinality": cardinality(c),
            })
            node_ids.add(cid)

    # 边：同一 chain 内的卡片连接
    chain_cards = defaultdict(list)
    for c in filtered:
        chain_id = c.get("metadata", {}).get("chain_id", "") if isinstance(c.get("metadata"), dict) else ""
        if chain_id:
            chain_cards[chain_id].append(c.get("card_id", ""))

    for chain_id, card_ids in chain_cards.items():
        for i in range(len(card_ids) - 1):
            edges.append({
                "source": card_ids[i],
                "target": card_ids[i + 1],
                "type": "chain_next",
                "weight": 1,
            })

    return {
        "scenario": "knowledge_graph",
        "exported_at": TODAY,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def export_stats(cards: list) -> dict:
    """全库 materials 覆盖率统计报告。"""
    stats = materials_stats(cards)

    # 按批次统计
    by_batch = defaultdict(lambda: {"total": 0, "核心卡": 0, "标准卡": 0, "辅助卡": 0})
    for c in cards:
        b = c.get("_batch", "")
        by_batch[b]["total"] += 1
        by_batch[b][cardinality(c)] += 1

    # 按类型统计
    by_type = defaultdict(lambda: {"total": 0, "核心卡": 0, "标准卡": 0, "辅助卡": 0})
    for c in cards:
        t = c.get("type", "")
        by_type[t]["total"] += 1
        by_type[t][cardinality(c)] += 1

    return {
        "scenario": "stats",
        "generated_at": TODAY,
        "total_cards": len(cards),
        "overall": stats,
        "by_batch": dict(by_batch),
        "by_type": dict(by_type),
    }


def export_anki_tsv(cards: list, concepts: list | None, tags: list | None) -> dict:
    """
    Anki TSV 格式导出。

    Anki 导入格式（TSV，UTF-8，制表符分隔）：
      第一列 = Front
      第二列 = Back
      第三列+ = Tags（多个标签用空格分隔）

    用法：File → Import → 选择 .tsv 文件，选择 "Allow HTML in fields"

    如果 --out 以 .tsv 结尾，直接输出 TSV 文件（而非 JSON）。
    """
    filtered = filter_cards(cards, concepts, tags)

    def trim_back(text: str, limit: int = 100) -> str:
        if len(text) <= limit:
            return text
        for sep in "。！？；":
            idx = text[:limit].rfind(sep)
            if idx > limit * 0.6:
                return text[:idx + 1]
        return text[:limit] + "…"

    def make_tags(c: dict) -> str:
        """合并 tags + concepts + type + batch，用空格分隔，Anki 接受 HTML。"""
        parts = []
        for t in c.get("tags", []):
            parts.append(t.lstrip("#").replace("/", "_"))
        for co in c.get("concepts", []):
            parts.append(f"concept:{co}")
        parts.append(f"type:{c.get('type', '')}")
        parts.append(f"batch:{c.get('_batch', '')}")
        freq_tags = [t for t in c.get("tags", []) if "考频" in t]
        parts.extend([t.lstrip("#").replace("/", "_") for t in freq_tags])
        return " ".join(parts)

    rows = []
    for c in filtered:
        front = c.get("front", "").replace("\t", " ")
        back = trim_back(c.get("back", "")).replace("\t", " ")
        tag_str = make_tags(c)
        rows.append(f"{front}\t{back}\t{tag_str}")

    return {
        "scenario": "anki_tsv",
        "exported_at": TODAY,
        "total_cards": len(rows),
        "filter_concepts": concepts or [],
        "filter_tags": tags or [],
        "tsv_rows": rows,
    }


# ── CLI ─────────────────────────────────────────────────────────────

SCENARIOS = {
    "writing": export_writing,
    "exam": export_exam,
    "anki": export_anki_tsv,
    "graph": export_graph,
    "stats": export_stats,
}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True,
                        choices=["writing", "exam", "anki", "graph", "stats"],
                        help="导出场景：writing=写作素材池, exam=考点卡包, graph=知识图谱, stats=统计报告")
    parser.add_argument("--concepts", help="逗号分隔的概念列表")
    parser.add_argument("--tags", help="逗号分隔的标签列表")
    parser.add_argument("--out", required=True, help="输出文件路径")
    parser.add_argument("--core", default=str(CORE_ROOT))
    args = parser.parse_args()

    # 解析筛选参数
    concepts = [x.strip() for x in args.concepts.split(",")] if args.concepts else None
    tags = [x.strip() for x in args.tags.split(",")] if args.tags else None

    print(f"扫描 core/：{args.core}")
    cards = scan_all_cards()
    print(f"全库共 {len(cards)} 张卡片")

    # 筛选
    if concepts or tags:
        filtered = filter_cards(cards, concepts, tags)
        print(f"筛选后：{len(filtered)} 张（concepts={concepts}, tags={tags}）")
    else:
        filtered = cards

    # 导出
    if args.scenario == "stats":
        result = export_stats(filtered)
    elif args.scenario == "writing":
        result = export_writing(filtered, concepts, tags)
    elif args.scenario == "exam":
        result = export_exam(filtered, concepts, tags)
    elif args.scenario == "anki":
        result = export_anki_tsv(filtered, concepts, tags)
    elif args.scenario == "graph":
        result = export_graph(filtered, concepts, tags)

    # 写入
    out_path = Path(args.out)
    out_path.parent.mkdir(exist_ok=True, parents=True)

    if args.scenario == "anki" and str(out_path).endswith(".tsv"):
        # TSV 格式直接写（UTF-8 无 BOM，Anki 兼容）
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(result.get("tsv_rows", [])))
        print(f"已导出 TSV：{out_path}（{result['total_cards']} 张卡片）")
        print(f"  导入提示：Anki → File → Import → 选择此文件 → 勾选 'Allow HTML in fields'")
        return

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已导出：{out_path}")
    print(f"  场景：{result.get('scenario', 'stats')}")
    print(f"  卡片数：{result.get('total_cards', result.get('card_count', len(result.get('cards', []))))}")

    if "materials_stats" in result:
        ms = result["materials_stats"]
        print(f"  materials 覆盖率：{ms['coverage_pct']['has_any']}%（核心卡 {ms['coverage_pct']['core']}%）")


if __name__ == "__main__":
    main()
