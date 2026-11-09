# -*- coding: utf-8 -*-
"""统计构建结果的各项数量（README、历代舆图首页用）：python3 tools/stats.py"""
import json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
G = json.load(open(ROOT / "build" / "geo.json", encoding="utf8"))
D = json.load(open(ROOT / "build" / "data.json", encoding="utf8"))
c = Counter(i["c"] for i in D["items"])
st = Counter(s["t"] for s in D["seeds"])
kinds = Counter(u["kind"] for u in D["units"])
print("节点", len(G["snaps"]))
print("条目", len(D["items"]), dict(c))
print("归属点", len(D["seeds"]), "城市", st["z"], "城镇", st["c"], "辅助点", st["r"])
print("单位", len(D["units"]), dict(kinds))
print("行军路线", len(G["routes"]))
print("geo.json", (ROOT / "build" / "geo.json").stat().st_size // 1024, "KB")
