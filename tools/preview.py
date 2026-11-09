# -*- coding: utf-8 -*-
"""疆域草图：python tools/preview.py 1937.12,1944.12 [--box 西,东,南,北] [--mode pol|zhen]
读 build/geo.json、build/data.json，画出这几个节点的疆域（投影与前端一致），输出 build/preview-<年.月>.png。
用来检查归属有没有填错、界线有没有白缝或叠色。"""
import json, sys, math, argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import config as C

RAD = math.pi / 180
P1, P2, P0, L0 = [v * RAD for v in C.PROJ]
NN = (math.sin(P1) + math.sin(P2)) / 2
CC = math.cos(P1) ** 2 + 2 * NN * math.sin(P1)
RHO0 = math.sqrt(CC - 2 * NN * math.sin(P0)) / NN
def proj(lon, lat):
    lon = np.asarray(lon); lat = np.asarray(lat)
    r = np.sqrt(np.maximum(CC - 2 * NN * np.sin(lat * RAD), 1e-9)) / NN
    th = NN * (lon * RAD - L0)
    return r * np.sin(th) * C.SCL, -(RHO0 - r * np.cos(th)) * C.SCL
def decode(flat):
    a = np.cumsum(np.asarray(flat, float).reshape(-1, 2), 0) / 100
    return np.column_stack(proj(a[:, 0], a[:, 1]))
def rings_path(rings):
    verts, codes = [], []
    for r in rings:
        p = decode(r)
        if len(p) < 3: continue
        verts += list(p) + [p[0]]; codes += [MPath.MOVETO] + [MPath.LINETO] * (len(p) - 1) + [MPath.CLOSEPOLY]
    return MPath(verts, codes) if verts else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nodes")
    ap.add_argument("--box", help="经纬框 西,东,南,北")
    ap.add_argument("--mode", default="pol", choices=["pol", "zhen"])
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    geo = json.load(open(C.BUILD / "geo.json", encoding="utf8")); data = json.load(open(C.BUILD / "data.json", encoding="utf8"))
    pool = geo.get("pool", [])
    U = data["units"]
    for nid in a.nodes.split(","):
        yy, mm = (int(x) for x in nid.split("."))
        sn = min(geo["snaps"], key=lambda s: abs(s["t"] - (yy * 12 + mm - 1)))
        y = f"{sn['y']}.{sn['m']:02d}"
        fig, ax = plt.subplots(figsize=(16, 10))
        ax.set_facecolor("#D5DCDB")
        for poly in geo["land"]:
            p = rings_path(poly)
            if p: ax.add_patch(PathPatch(p, fc="#ECEBE3", ec="#A9AFAE", lw=0.4))
        get = lambda v: pool[v] if isinstance(v, int) else v
        multi = {int(k) for k in sn["p"]}
        fills = []
        for u, rings in sn["z"].items():
            u = int(u); pu = sn["pol"].get(str(u), u)
            if a.mode == "pol" and pu in multi: continue
            fills.append((u, get(rings)))
        if a.mode == "pol":
            fills += [(int(p), get(r)) for p, r in sn["p"].items()]
        for u, rings in fills:
            p = rings_path(rings)
            if p: ax.add_patch(PathPatch(p, fc=U[u]["cl"], ec="#333", lw=0.5, alpha=0.75))
        labs = sn["lz"] if a.mode == "zhen" else {**{k: v for k, v in sn["lz"].items() if int(sn["pol"].get(k, k)) not in multi}, **sn["lp"]}
        for k, L in labs.items():
            x, y_ = proj(L[0], L[1]); n = sn["lab"].get(k, U[int(k)]["n"])
            if L[2] > (0.02 if a.box else 0.3): ax.text(x, y_, n, ha="center", va="center", fontsize=max(5, min(14, math.sqrt(L[2]) * (4 if a.box else 1.6))), family="Noto Sans CJK JP", clip_on=True)
        if a.box:
            w, e, s, n = map(float, a.box.split(","))
            xs, ys = proj(np.r_[np.linspace(w, e, 20), np.linspace(w, e, 20)], np.r_[np.full(20, s), np.full(20, n)])
        else:
            w, e, s, n = geo["ext"]
            xs, ys = proj(np.r_[np.linspace(w, e, 50), np.linspace(w, e, 50), np.full(20, w), np.full(20, e)], np.r_[np.full(50, s), np.full(50, n), np.linspace(s, n, 20), np.linspace(s, n, 20)])
        ax.set_xlim(xs.min(), xs.max()); ax.set_ylim(ys.max(), ys.min()); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{sn['y']} {sn['t']}", family="Noto Sans CJK JP")
        out = C.BUILD / f"preview-{y}{'-' + a.box.replace(',', '_') if a.box else ''}-{a.mode}.png"
        fig.savefig(out, dpi=a.dpi, bbox_inches="tight"); plt.close(fig)
        print("wrote", out)

if __name__ == "__main__":
    main()
