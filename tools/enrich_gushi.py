"""
古史_v4 materials 层补全脚本

策略：
  - materials.data  ← 从 back 末尾提取【★考点】标记（考频）
  - materials.scene ← 空（分析型卡片，无叙事场景）
  - materials.quote ← 空（分析型卡片，无直接引文）

考频格式：提取 ★ 数量，标准化为 frequency 标签
"""

import json
import re
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()


def extract_frequency(back: str) -> str:
    """从 back 末尾提取考频标记。"""
    match = re.search(r"【★{1,5}考点】", back)
    if match:
        stars = match.group()
        count = stars.count("★")
        freq_map = {5: "极高频（★★★★★）", 4: "高频（★★★★）", 3: "中频（★★★）", 2: "低频（★★）", 1: "★"}
        return freq_map.get(count, "中频")
    return "未标注"


def enrich_gushi():
    cards_path = Path("core/历史/古史_v4/cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cards = raw["cards"]
    updated = 0
    stats = {"node": 0, "strategy_cause": 0, "strategy_impact": 0, "strategy_turning": 0, "chain": 0, "no_freq": 0}

    for card in cards:
        ctype = card.get("type", "")
        back = card.get("back", "")

        # 提取考频
        freq = extract_frequency(back)
        if freq == "未标注":
            stats["no_freq"] += 1
        else:
            stats[ctype] = stats.get(ctype, 0) + 1

        # 初始化 materials
        if "materials" not in card or not isinstance(card.get("materials"), dict):
            card["materials"] = {"quote": "", "scene": "", "data": ""}

        # data 字段：考频 + 提取的量化信息
        # 从 back 中提取数字/年份
        numbers = re.findall(r"\d{4}年|\d+万|\d+亿|\d+%|\d+人", back)
        data_parts = [freq]
        if numbers:
            data_parts.append("关联数据：" + "；".join(numbers[:5]))

        card["materials"]["data"] = "；".join(data_parts)
        # 分析型卡片，scene 和 quote 留空

        # 更新 metadata
        if "metadata" not in card or not isinstance(card.get("metadata"), dict):
            card["metadata"] = {}
        if isinstance(card.get("metadata"), dict):
            if card["metadata"].get("version", "") < "v1.1":
                card["metadata"]["version"] = "v1.1"
            card["metadata"]["updated_at"] = TODAY
            if not card["metadata"].get("note"):
                card["metadata"]["note"] = "materials.data 补全（2026-08-08），来源：back中考频标记自动提取"
            if "changelog" not in card["metadata"]:
                card["metadata"]["changelog"] = []
            card["metadata"]["changelog"].append({
                "version": "v1.1",
                "date": TODAY,
                "change": "补全 materials.data（考频+量化数据）"
            })

        updated += 1

    # 写回文件
    with open(cards_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    print(f"完成：{updated} 张卡片已补全 materials.data")
    print(f"有考频标记：{sum(v for k,v in stats.items() if k != 'no_freq')} 张")
    print(f"无考频标记：{stats['no_freq']} 张")
    print(f"文件已更新：{cards_path}")


if __name__ == "__main__":
    enrich_gushi()
