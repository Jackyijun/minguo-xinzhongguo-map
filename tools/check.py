# -*- coding: utf-8 -*-
"""检查 content/ 的史料格式与引用：python3 tools/check.py [--part 文件名关键字] [--node 1937.12] [--who 单位键]

  --part cn3   只列出文件名含 cn3 的错误与警告（错误仍以全体为准）
  --node X     打印节点 X 时各单位领有的归属点
  --who K      打印单位 K 在各节点领有的归属点数量
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import content as CT

ap = argparse.ArgumentParser()
ap.add_argument("--part"); ap.add_argument("--node"); ap.add_argument("--who")
a = ap.parse_args()
D = CT.load_all()
sel = (lambda s: a.part in s) if a.part else (lambda s: True)
E = [e for e in CT.ERR if sel(e)]; W = [w for w in CT.WARN if sel(w)]
print(f"节点 {len(D['nodes'])} · 归属点 {len(D['seeds'])} · 单位 {len(D['units'])} · 战役 {len(D['items']['battles'])} · 事件 {len(D['items']['events'])} · 都城 {len(D['items']['capitals'])} · 线状 {len(D['items']['lines'])} · 行军 {len(D['items']['routes'])} · 租界 {len(D['items']['concs'])}")
for e in E[:200]: print("错误", e)
for w in W[:80]: print("提醒", w)
if a.node:
    j = [n["id"] for n in D["nodes"]].index(a.node); st = D["states"][j]
    by = {}
    for s, u in st["own"].items(): by.setdefault(u, []).append(s)
    for u, ss in sorted(by.items(), key=lambda kv: (kv[0] is None, str(kv[0]))):
        pol = st["pol"].get(u) if u else None
        print(f"{u}{'['+st['lab'][u]+']' if u in st['lab'] else ''}{'>'+pol if pol else ''}{' (斜线)' if u in st['hatch'] else ''}: {len(ss)}  " + " ".join(ss))
if a.who:
    for n, st in zip(D["nodes"], D["states"]):
        c = sum(1 for u in st["own"].values() if u == a.who)
        if c: print(n["id"], c, st["lab"].get(a.who, ""), st["pol"].get(a.who, ""), "斜线" if a.who in st["hatch"] else "")
print("结果：", "通过" if not E else f"{len(E)} 处错误")
sys.exit(1 if E else 0)
