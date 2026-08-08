"""
墨骨山河_Ep01（颜真卿）materials 层补全脚本

来源：
  - 微剧本：墨骨山河_ep01_颜真卿.json
  - 参考史料：《旧唐书·颜真卿传》《新唐书》《祭侄文稿》原文

补全规则：
  - materials.quote    ← 人物原话 / 史料引文
  - materials.scene   ← 时间/地点/动作/对话的具象化描写
  - materials.data    ← 量化数据（兵力/人数/排名/年份）
"""

import json
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()

# ── materials 数据（从微剧本 + 史料提取）────────────────────────────

MATERIALS_DATA = {
    "EP01_NODE_001": {
        "quote": "城外安禄山使者已至第三日。兄长远在常山（颜杲卿），生死未卜。我手中不过六千士兵，何去何从？",
        "scene": "天宝十四载（755年）十二月，平原郡太守官署。寒风凛冽，烛火摇曳。案上急报墨迹未干，安禄山叛军已过黄河，城外远处隐约有烽烟。",
        "data": "平原郡守兵六千，安禄山叛军数万；安禄山于天宝十四载十一月初九（755年12月16日）在范阳起兵，三个月内横扫河北。"
    },
    "EP01_STRATEGY_CAUSE_001": {
        "quote": "河北诸郡太守多为安禄山旧部或受其威逼利诱，望风投降。",
        "scene": "安禄山起兵后，河北诸郡迅速陷落，仅平原郡、北海郡等少数城池未陷。",
        "data": "河北诸郡太守多为安禄山旧部或受其威逼利诱，望风投降；颜真卿坚守三因：平原郡位置偏东未受最初冲击、颜氏家族在河北根基深厚、颜真卿本人忠义为先。"
    },
    "EP01_STRATEGY_CAUSE_002": {
        "quote": "唐玄宗对安禄山的信任建立在二十年的恩宠之上，且安禄山以忠顺形象示人。",
        "scene": "唐玄宗天宝年间的朝廷。安禄山每次入京，均以憨态可掬的形象获取玄宗信任，朝中李林甫等人亦多为其辩护。",
        "data": "唐玄宗信任安禄山二十年；中央对藩镇将领的监察体制已严重弱化，信息传递受阻。"
    },
    "EP01_STRATEGY_TURNING_001": {
        "quote": "父陷子死，巢倾卵覆。（《祭侄文稿》原文）",
        "scene": "天宝十四载十二月，平原郡太守官署。颜真卿独坐灯下，使者立于堂前，等待答复。颜真卿最终选择死守，并诛杀安禄山使者以明志。",
        "data": "选项A（坚守平原）：六千对数万，必败无疑；选项B（弃城南逃）：留有用之身，但将成为弃民于贼的罪人。颜真卿最终选择死守。"
    },
    "EP01_NODE_002": {
        "quote": "颜杲卿、颜季明父子被俘后骂贼殉国，颜氏一门三十余口遇难。",
        "scene": "天宝十五载（756年）正月，常山郡。叛军攻破城池，颜杲卿被俘后痛骂安禄山，不屈而死；颜季明亦同日殉国。消息传至平原，已是数月之后。",
        "data": "颜氏一门三十余口遇难；天宝十五载正月，常山之难。"
    },
    "EP01_STRATEGY_IMPACT_001": {
        "quote": "维乾元元年岁次戊戌九月庚午朔三日壬申……父陷子死，巢倾卵覆。（《祭侄文稿》原文）",
        "scene": "乾元元年（758年）九月三日夜，蒲州刺史官署内室。烛火摇曳，案上摆着侄子颜季明的头骨。颜真卿手执狼毫，墨汁与泪水交融于纸面。",
        "data": "《祭侄文稿》被誉为天下第二行书；乾元元年=岁次戊戌（758年）；此时距常山之难已近三年。"
    },
    "EP01_NODE_003": {
        "quote": "达其情性，形其哀乐。（孙过庭《书谱》）",
        "scene": "乾元元年九月，蒲州。颜真卿执笔疾书，笔势剧烈变化——涂改、增删、墨色枯湿交替，烛影幢幢，心绪随之跌宕。",
        "data": "颜体三要素：篆籀气（线条圆厚如篆籀）、中锋行笔（筋骨力道）、屋漏痕涨墨（用墨如屋漏，厚重朴拙）；与王羲之秀逸流美书风形成鲜明对比。"
    },
    "EP01_STRATEGY_IMPACT_002": {
        "quote": "心正笔正。（颜真卿语）",
        "scene": "历代书论中，颜体始终与忠烈人格绑定。宋代苏轼、清代刘熙载等均以颜体为正气象征。书品与人品互相印证。",
        "data": "宋代苏轼评颜体；清代刘熙载《艺概》以颜体为正气象征；书法史上形成独特的忠烈书风传统。"
    }
}


def enrich_cards():
    cards_path = Path("core/历史/墨骨山河_Ep01/cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    updated = 0
    for card in cards:
        cid = card.get("card_id", "")
        if cid in MATERIALS_DATA:
            mat = MATERIALS_DATA[cid]
            # 更新 materials 层
            if "materials" not in card or not isinstance(card["materials"], dict):
                card["materials"] = {}
            card["materials"]["quote"] = mat["quote"]
            card["materials"]["scene"] = mat["scene"]
            card["materials"]["data"] = mat["data"]

            # 更新 metadata
            if "metadata" not in card or not isinstance(card.get("metadata"), dict):
                card["metadata"] = {}
            if isinstance(card.get("metadata"), dict):
                card["metadata"]["version"] = "v1.1"
                card["metadata"]["updated_at"] = TODAY
                card["metadata"]["note"] = "materials 层补全（2026-08-08），来源：墨骨山河_ep01_颜真卿.json + 史料"
                if "changelog" not in card["metadata"]:
                    card["metadata"]["changelog"] = []
                card["metadata"]["changelog"].append({
                    "version": "v1.1",
                    "date": TODAY,
                    "change": "补全 materials.quote / scene / data"
                })

            updated += 1
            print(f"  [{cid}] ✅ 已补全 materials")
        else:
            print(f"  [{cid}] ⚠️  无对应 materials 数据（跳过）")

    # 写回文件
    with open(cards_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\n完成：{updated}/8 张卡片已补全 materials 层")
    print(f"文件已更新：{cards_path}")


if __name__ == "__main__":
    enrich_cards()
