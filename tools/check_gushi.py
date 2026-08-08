import json
from pathlib import Path
from collections import Counter

root = Path("core/历史/古史_v4")
with open(root/"cards.json", encoding="utf-8") as f:
    raw = json.load(f)
cards = raw["cards"]

types = Counter(c.get("type") for c in cards)
print("type分布:")
for t, n in types.most_common():
    print(f"  {t}: {n}")
print()

# 找几类典型back
for c in cards[:5]:
    cid = c.get("card_id", "?")
    ctype = c.get("type", "?")
    back = c.get("back", "")
    print(f"[{cid}] type={ctype}")
    print(f"  back[:150]: {back[:150]}")
    print()
