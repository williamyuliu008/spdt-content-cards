import json
from pathlib import Path

root = Path("core/书法/CAFA楷书")
with open(root/"cards.json", encoding="utf-8") as f:
    cards = json.load(f)

for c in cards:
    cid = c.get("card_id", "?")
    ctype = c.get("type", "?")
    front = c.get("front", "")[:80]
    back = c.get("back", "")[:200]
    print(f"[{cid}] type={ctype}")
    print(f"  front: {front}")
    print(f"  back: {back}")
    print()
