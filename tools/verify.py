# -*- coding: utf-8 -*-
"""逐节点核对每个归属点是否落在其归属单位的疆域之内：python3 tools/verify.py [--tol 公里]

报告落在别的单位里的点（距自己单位疆域超过容差）。规范第十三节的验收项。
"""
import json, argparse
from collections import defaultdict
from pathlib import Path
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--tol", type=float, default=3.0); ap.add_argument("--all", action="store_true")
a = ap.parse_args()
G = json.load(open(ROOT / "build" / "geo.json", encoding="utf8"))
D = json.load(open(ROOT / "build" / "data.json", encoding="utf8"))
UN = [u["n"] for u in D["units"]]

def ring(r):
    pts, x, y = [], 0, 0
    for i in range(0, len(r), 2):
        x += r[i]; y += r[i + 1]; pts.append((x / 100, y / 100))
    return pts
cache = {}
def geom(pi):
    if pi not in cache:
        rings = [ring(r) for r in G["pool"][pi]]
        polys = [Polygon(r) for r in rings if len(r) >= 4]
        g = shapely.make_valid(shapely.unary_union([shapely.make_valid(p) for p in polys])) if polys else Polygon()
        cache[pi] = g
    return cache[pi]

bad = defaultdict(list)
for sn in G["snaps"]:
    zs = {int(k): geom(v) for k, v in sn["z"].items()}
    for i, u in enumerate(sn["own"]):
        if u < 0 or u not in zs: continue
        sd = D["seeds"][i]
        if sd["t"] == "r" and not a.all: continue
        p = Point(sd["lon"], sd["lat"])
        g = zs[u]
        if g.is_empty: bad[(sd["id"], UN[u])].append((sn["y"], sn["m"], -1)); continue
        if g.contains(p): continue
        d = g.distance(p) * 111 * max(0.3, abs(__import__("math").cos(sd["lat"] / 57.3)))
        if d > a.tol: bad[(sd["id"], UN[u])].append((sn["y"], sn["m"], round(d, 1)))
print("容差", a.tol, "km；不在本单位疆域内的点：", len(bad))
for (sid, un), v in sorted(bad.items(), key=lambda kv: -len(kv[1])):
    print(f"  {sid} → {un}：{len(v)} 个节点，如 {v[0][0]}.{v[0][1]}（偏 {v[0][2]} km）")
