"""
CAFA楷书 materials 层补全脚本

3张卡片均为"楷书影响链 strategy_impact"，来自 CAFA 书法校考古汉语/书法史论
"""

import json
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()

MATERIALS_DATA = {
    "CAFA_impact_01": {
        "quote": "达其情性，形其哀乐。（孙过庭《书谱》）——唐楷的法度严谨，倒逼行书在'法'与'意'之间寻找平衡。",
        "scene": "唐代书法史脉络：楷书（法度确立）→ 行书（法意平衡）→ 草书（性情抒发）→ 宋代尚意（辩证超越）。",
        "data": "CAFA书法校考：楷书影响链；唐楷→行书→尚意书风演变关系。"
    },
    "CAFA_impact_02": {
        "quote": "心正笔正。（颜真卿）；书品即人品。（刘熙载《艺概》）",
        "scene": "历代忠烈书风传承脉络：颜真卿（唐）→ 苏轼（宋）→ 文天祥（宋）→ 傅山（明）→ 刘鹗（清）。颜体始终与忠烈人格绑定。",
        "data": "CAFA书法校考：忠烈书风链；宋代苏轼评颜体；清代刘熙载以颜体为正气象征。"
    },
    "CAFA_impact_03": {
        "quote": "尚意书风：苏轼'我书意造本无法'，米芾'意足我自足，放笔一戏空明月'。",
        "scene": "宋代书坛。苏轼、米芾等书家在反叛唐楷规范的过程中，开创尚意书风。",
        "data": "CAFA书法校考：唐楷→尚意辩证关系；苏轼、米芾为尚意代表书家。"
    }
}


def enrich_cafa():
    cards_path = Path("core/书法/CAFA楷书/cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    updated = 0
    for card in cards:
        cid = card.get("card_id", "")
        if cid in MATERIALS_DATA:
            mat = MATERIALS_DATA[cid]
            if "materials" not in card or not isinstance(card.get("materials"), dict):
                card["materials"] = {}
            card["materials"]["quote"] = mat["quote"]
            card["materials"]["scene"] = mat["scene"]
            card["materials"]["data"] = mat["data"]

            if "metadata" not in card or not isinstance(card.get("metadata"), dict):
                card["metadata"] = {}
            if isinstance(card.get("metadata"), dict):
                card["metadata"]["version"] = "v1.1"
                card["metadata"]["updated_at"] = TODAY
                card["metadata"]["note"] = "materials 层补全（2026-08-08），来源：书法史论+CAFA书法校考"
                if "changelog" not in card["metadata"]:
                    card["metadata"]["changelog"] = []
                card["metadata"]["changelog"].append({
                    "version": "v1.1",
                    "date": TODAY,
                    "change": "补全 materials.quote / scene / data"
                })
            updated += 1
            print(f"  [{cid}] ✅ materials 已补全")
        else:
            print(f"  [{cid}] ⚠️ 无对应数据（跳过）")

    with open(cards_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\n完成：{updated}/3 张卡片已补全")
    print(f"文件已更新：{cards_path}")


if __name__ == "__main__":
    enrich_cafa()
