import json
from pathlib import Path
from collections import defaultdict

root = Path("core")
total = 0
mat_stats = defaultdict(lambda: {"total": 0, "has_quote": 0, "has_scene": 0, "has_data": 0, "has_any": 0})
type_stats = defaultdict(lambda: {"total": 0, "has_any": 0})

for f in root.rglob("cards.json"):
    if "_meta" in f.parts:
        continue
    with open(f, encoding="utf-8") as fp:
        raw = json.load(fp)
        cards = raw if isinstance(raw, list) else raw.get("cards", raw.get("materials_cards", []))
    for c in cards:
        total += 1
        m = c.get("materials", {})
        if not isinstance(m, dict):
            m = {"quote": "", "scene": "", "data": ""}
        batch = f.parent.name
        ctype = c.get("type", "")
        has_q = bool(m.get("quote"))
        has_s = bool(m.get("scene"))
        has_d = bool(m.get("data"))
        has_any = has_q or has_s or has_d
        mat_stats[batch]["total"] += 1
        mat_stats[batch]["has_quote"] += int(has_q)
        mat_stats[batch]["has_scene"] += int(has_s)
        mat_stats[batch]["has_data"] += int(has_d)
        mat_stats[batch]["has_any"] += int(has_any)
        type_stats[ctype]["total"] += 1
        type_stats[ctype]["has_any"] += int(has_any)

print(f"总卡片: {total}")
print()
print("按批次:")
for b, d in mat_stats.items():
    t = d["total"]
    pct = d["has_any"] / t * 100 if t else 0
    print(f"  {b}: {t}张 | quote:{d['has_quote']} scene:{d['has_scene']} data:{d['has_data']} 有任意:{d['has_any']} ({pct:.0f}%)")
print()
print("按类型:")
for t, d in type_stats.items():
    pct = d["has_any"] / d["total"] * 100 if d["total"] else 0
    print(f"  {t}: {d['total']}张 | 有materials:{d['has_any']} ({pct:.0f}%)")

# 列出最值得补全的卡片（node + strategy_turning，无任何materials）
print()
print("最值得优先补全的卡片（node/strategy_turning，无materials）:")
priority = []
for f in root.rglob("cards.json"):
    if "_meta" in f.parts:
        continue
    with open(f, encoding="utf-8") as fp:
        raw = json.load(fp)
        cards = raw if isinstance(raw, list) else raw.get("cards", raw.get("materials_cards", []))
    for c in cards:
        m = c.get("materials", {})
        if not isinstance(m, dict):
            m = {"quote": "", "scene": "", "data": ""}
        ctype = c.get("type", "")
        if ctype in ("node", "strategy_turning", "strategy_cause") and not (m.get("quote") or m.get("scene") or m.get("data")):
            concepts = c.get("concepts", [])
            batch = f.parent.name
            front = c.get("front", "")[:40]
            priority.append({
                "card_id": c.get("card_id", ""),
                "type": ctype,
                "batch": batch,
                "front": front,
                "concepts": concepts[:3],
            })

# 按批次+类型排序
priority.sort(key=lambda x: (x["batch"], {"strategy_turning": 0, "node": 1, "strategy_cause": 2, "strategy_impact": 3}.get(x["type"], 9)))
for i, c in enumerate(priority[:30]):
    print(f"  [{i+1}] {c['card_id']} | {c['type']} | {c['batch']} | {c['concepts']}")
if len(priority) > 30:
    print(f"  …还有 {len(priority)-30} 张")
print(f"  合计优先级卡片: {len(priority)} 张")
