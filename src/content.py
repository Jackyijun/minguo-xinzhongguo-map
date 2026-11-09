# -*- coding: utf-8 -*-
"""读入 content/ 下全部史料并校验：节点、归属点、单位、说明、各节点归属（snaps）、条目与线状要素。

build.py 和 tools/check.py 共用。时间一律换算成“月序” T = 年 × 12 + (月 − 1)；
节点取所标月份之末，本期 = 上一节点之后（不含）至本节点（含）。
"""
import json, re, sys, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ERR, WARN = [], []
def err(msg): ERR.append(msg)
def warn(msg): WARN.append(msg)

# ---------------------------------------------------------------- 时间
def T(s, default_month=1):
    """'1937.07' / '1937.7' / '1937.07.15' / 1937 / '1937' → 月序；None → None；9999 → 很大。"""
    if s is None: return None
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        y = int(s)
        if y >= 9999: return 9999 * 12
        return y * 12 + default_month - 1
    m = re.fullmatch(r"\s*(\d{4})(?:\.(\d{1,2}))?(?:\.(\d{1,2}))?\s*", str(s))
    if not m: raise ValueError(f"无法识别的日期：{s!r}（应写成 1937.07 或 1937.07.15）")
    y = int(m.group(1)); mo = int(m.group(2)) if m.group(2) else default_month
    if y >= 9999: return 9999 * 12
    if not 1 <= mo <= 12: raise ValueError(f"月份超出范围：{s!r}")
    return y * 12 + mo - 1
def ym(t): return (t // 12, t % 12 + 1)
def tstr(t): y, m = ym(t); return f"{y}.{m:02d}"

# ---------------------------------------------------------------- 节点
def load_nodes():
    nodes = []
    for ln, raw in enumerate(open(CONTENT / "nodes.txt", encoding="utf8"), 1):
        line = raw.strip()
        if not line or line.startswith("#"): continue
        if not line.startswith("@"): err(f"nodes.txt:{ln} 应以 @ 开头"); continue
        parts = [p.strip() for p in line[1:].split("|")]
        if len(parts) != 3: err(f"nodes.txt:{ln} 应有 3 段：年.月 | 纪年 | 标题"); continue
        t = T(parts[0]); y, m = ym(t)
        nodes.append(dict(id=parts[0], t=t, y=y, m=m, era=parts[1], title=parts[2], d=""))
    for a, b in zip(nodes, nodes[1:]):
        if b["t"] <= a["t"]: err(f"节点须递增：{a['id']} → {b['id']}")
    return nodes

def load_desc(nodes):
    NID = {n["id"]: n for n in nodes}
    src = {}
    for f in sorted((CONTENT / "desc").glob("*.txt")):
        for ln, raw in enumerate(open(f, encoding="utf8"), 1):
            line = raw.strip()
            if not line or line.startswith("#"): continue
            if not line.startswith("@") or "|" not in line: err(f"desc/{f.name}:{ln} 应写成 @年.月 | 概述"); continue
            k, _, d = line[1:].partition("|"); k = k.strip(); d = d.strip()
            if k not in NID: err(f"desc/{f.name}:{ln} 没有这个节点：{k}"); continue
            if k in src: err(f"desc/{f.name}:{ln} 节点 {k} 的概述已在 {src[k]} 写过")
            src[k] = f.name; NID[k]["d"] = d
    for n in nodes:
        if not n["d"]: warn(f"节点 {n['id']} 缺概述")

# ---------------------------------------------------------------- 归属点
def load_seeds():
    seeds = []
    for f in sorted((CONTENT / "seeds").glob("*.txt")):
        for ln, raw in enumerate(open(f, encoding="utf8"), 1):
            line = raw.strip()
            if not line or line.startswith("#"): continue
            t = line.split()
            where = f"seeds/{f.name}:{ln}"
            if len(t) < 4: err(f"{where} 至少要有 ID 经度 纬度 今地"); continue
            try: lo, la = float(t[1]), float(t[2])
            except ValueError: err(f"{where} 经纬度不是数字"); continue
            if not (-180 <= lo <= 360 and -60 <= la <= 85): err(f"{where} 经纬度超出范围")
            typ, names, reach = "z", None, 1.0
            for x in t[4:]:
                if x in ("c", "r", "z"): typ = x
                elif x.startswith("N="):
                    names = []
                    for part in x[2:].split(","):
                        if ":" not in part: err(f"{where} 名称沿革应写成 年.月:名"); continue
                        y, n = part.split(":", 1)
                        try: names.append([T(y), n])
                        except ValueError as e: err(f"{where} {e}")
                elif x.startswith("R="):
                    try: reach = float(x[2:])
                    except ValueError: err(f"{where} R= 应为数字")
                else: err(f"{where} 无法识别的字段：{x}（今地里不能有空格）")
            seeds.append(dict(id=t[0], n=t[0].split("·")[0], lon=lo, lat=la, mod=t[3], t=typ, names=names, R=reach, file=f.name))
    ids = {}
    for s in seeds:
        if s["id"] in ids: err(f"归属点 ID 重复：{s['id']}（{ids[s['id']]} 与 {s['file']}）")
        ids[s["id"]] = s["file"]
    return seeds

# ---------------------------------------------------------------- 单位与说明
def _import(path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"_u_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod
def load_units():
    units = []
    for f in sorted((CONTENT / "units").glob("*.py")):
        if f.name.startswith("_"): continue
        try: mod = _import(f)
        except Exception as e: err(f"units/{f.name} 无法导入：{e}"); continue
        for u in getattr(mod, "U", []):
            u["file"] = f.name; units.append(u)
    keys = {}
    for u in units:
        if u["k"] in keys: err(f"单位键重复：{u['k']}（{keys[u['k']]} 与 {u['file']}）")
        keys[u["k"]] = u["file"]
    for u in units:
        if u["pol"] not in keys: err(f"单位 {u['k']} 的默认所属政权不存在：{u['pol']}")
    notes = {}
    for f in sorted((CONTENT / "notes").glob("*.json")):
        try: d = json.load(open(f, encoding="utf8"))
        except Exception as e: err(f"notes/{f.name} 不是合法 JSON：{e}"); continue
        for k, v in d.items():
            if k not in keys: err(f"notes/{f.name}：没有这个单位 {k}")
            elif k in notes: err(f"notes/{f.name}：单位 {k} 的说明已在 {notes[k][0]} 写过")
            else: notes[k] = (f.name, v)
    for u in units:
        if u["k"] in notes:
            if u.get("note"): err(f"单位 {u['k']} 在 units/{u['file']} 与 notes/{notes[u['k']][0]} 都写了说明")
            else: u["note"] = notes[u["k"]][1]
    return units

# ---------------------------------------------------------------- 各节点归属
HEAD_RE = re.compile(r"^([^\[\]{}>]+)(?:\[([^\]]*)\])?(?:\{([^}]*)\})?(?:>(.+))?$")
def load_snaps(nodes, seeds, units):
    SID = {s["id"] for s in seeds}; UK = {u["k"] for u in units}
    NID = [n["id"] for n in nodes]
    blocks = {}     # 节点 id → [(文件, 行号, 行)]
    for f in sorted((CONTENT / "snaps").glob("*.txt")):
        cur = None; seen = []
        for ln, raw in enumerate(open(f, encoding="utf8"), 1):
            line = raw.rstrip("\n").split("#", 1)[0].rstrip()
            if not line.strip(): continue
            if line.startswith("@"):
                k = line[1:].strip()
                if k not in NID: err(f"snaps/{f.name}:{ln} 没有这个节点：{k}"); cur = None; continue
                if seen and NID.index(k) <= NID.index(seen[-1]): err(f"snaps/{f.name}:{ln} 节点 {k} 顺序不对或重复")
                seen.append(k); cur = k; blocks.setdefault(k, []); continue
            if cur is None: err(f"snaps/{f.name}:{ln} 在第一个 @节点 之前"); continue
            blocks[cur].append((f.name, ln, line))
    # 分工“道”：文件名去掉数字（cn3 → cn）。同一道的文件按时段接力；!重置 清空本道单位的显示名、所属、治所与斜线
    lane = lambda fname: re.sub(r"\d+", "", Path(fname).stem)
    lane_units = {}
    for k, lst in blocks.items():
        for fname, ln, line in lst:
            h = line.partition(":")[0].strip()
            m = HEAD_RE.match(h)
            if m and not h.startswith(("+", "-", "·", "!")): lane_units.setdefault(lane(fname), set()).add(m.group(1).strip())
    lane_seeds = {}
    for s in seeds: lane_seeds.setdefault(re.sub(r"\d+", "", Path(s["file"]).stem), set()).add(s["id"])
    first_block = {}
    for k in NID:
        for fname, ln, line in blocks.get(k, []): first_block.setdefault(fname, k)
    state = dict(own={}, lab={}, pol={}, seat={}, hatch=set())
    who = {}       # 归属点 → 最后改动它的文件
    out = []
    for n in nodes:
        start_own = dict(state["own"])
        for fname, ln, line in blocks.get(n["id"], []):
            where = f"snaps/{fname}:{ln}（{n['id']}）"
            if line.strip() == "!重置":
                for uk in lane_units.get(lane(fname), ()):
                    state["lab"].pop(uk, None); state["pol"].pop(uk, None); state["seat"].pop(uk, None); state["hatch"].discard(uk)
                continue
            head, sep, body = line.partition(":")
            if not sep: err(f"{where} 缺少冒号"); continue
            head = head.strip(); toks = body.split()
            if head in ("+斜线", "-斜线", "+藩属", "-藩属"):
                for k in toks:
                    if k not in UK: err(f"{where} 斜线行里的单位不存在：{k}")
                    elif head[0] == "+": state["hatch"].add(k)
                    else: state["hatch"].discard(k)
                continue
            if head == "·":
                for tk in toks:
                    if tk not in SID: err(f"{where} 未知归属点：{tk}")
                    else: state["own"][tk] = None; who[tk] = fname
                continue
            m = HEAD_RE.match(head)
            if not m: err(f"{where} 无法解析：{head}"); continue
            uk, lab, seat, pol = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
            if uk not in UK: err(f"{where} 单位不存在：{uk}"); continue
            if lab is not None:
                if lab == "": state["lab"].pop(uk, None)
                else: state["lab"][uk] = lab
            if seat is not None:
                if seat == "": state["seat"].pop(uk, None)
                elif seat not in SID: err(f"{where} 治所不在归属点里：{seat}")
                else: state["seat"][uk] = seat
            if pol is not None:
                pol = pol.strip()
                if pol not in UK: err(f"{where} 所属政权不存在：{pol}")
                else: state["pol"][uk] = pol
            for tk in toks:
                if tk.startswith("@"):
                    rk = tk[1:]
                    if rk not in UK: err(f"{where} 引用的单位不存在：{rk}"); continue
                    lst = [s for s, u in start_own.items() if u == rk]
                    if not lst: warn(f"{where} 引用 {tk} 时该单位没有任何归属点")
                    for s in lst: state["own"][s] = uk; who[s] = fname
                elif tk not in SID: err(f"{where} 未知归属点：{tk}")
                else: state["own"][tk] = uk; who[tk] = fname
        out.append(dict(own=dict(state["own"]), lab=dict(state["lab"]), pol=dict(state["pol"]), seat=dict(state["seat"]), hatch=set(state["hatch"])))
    # 每个文件的第一个节点块必须写全本道的归属点
    for fname, k in first_block.items():
        got = set()
        for fn, ln, line in blocks[k]:
            if fn != fname: continue
            h, sep, body = line.partition(":")
            if sep and not h.strip().startswith(("+", "-")): got.update(t for t in body.split() if not t.startswith("@"))
        need = lane_seeds.get(lane(fname), set())
        miss = sorted(need - got)
        if need and miss: err(f"snaps/{fname} 的第一个节点 {k} 没有写到 {len(miss)} 个本道归属点：" + " ".join(miss[:40]) + (" …" if len(miss) > 40 else ""))
    missing = [s["id"] for s in seeds if s["id"] not in out[0]["own"]] if out else []
    if missing: err(f"首节点 {nodes[0]['id']} 有 {len(missing)} 个归属点没有分配：" + " ".join(missing[:40]) + (" …" if len(missing) > 40 else ""))
    return out, blocks

# ---------------------------------------------------------------- 条目
def load_items(units, seeds):
    UK = {u["k"] for u in units}; SID = {s["id"] for s in seeds}
    L = {k: [] for k in ("BATTLES", "EVENTS", "CAPITALS", "PASSES", "CONCS", "RAILS", "ROADS", "AIRS", "ROUTES", "RANGES", "SEAS")}
    for f in sorted((CONTENT / "items").glob("*.py")):
        if f.name.startswith("_"): continue
        try: mod = _import(f)
        except Exception as e: err(f"items/{f.name} 无法导入：{e}"); continue
        for k in L:
            for x in getattr(mod, k, []): L[k].append((f.name, x))
    out = dict(battles=[], events=[], capitals=[], passes=[], concs=[], lines=[], routes=[])
    def chk_ll(where, lo, la):
        if not (isinstance(lo, (int, float)) and isinstance(la, (int, float)) and -180 <= lo <= 360 and -60 <= la <= 85): err(f"{where} 经纬度不对：{lo}, {la}")
    def tt(where, s, need=True):
        if s is None:
            if need: err(f"{where} 缺日期")
            return None
        try: return T(s)
        except ValueError as e: err(f"{where} {e}"); return None
    for fn, x in L["BATTLES"]:
        where = f"items/{fn} 战役 {x[0] if x else '?'}"
        if len(x) != 10: err(f"{where} 应有 10 项：名, 今地, 经, 纬, 起, 止, 年代文字, 胜负, 主将, 按语"); continue
        nm, mod, lo, la, a, b, yt, sides, cmd, note = x; chk_ll(where, lo, la)
        ta, tb = tt(where, a), tt(where, b, False)
        out["battles"].append(dict(old=nm, mod=mod, lon=lo, lat=la, t=ta, t1=tb if tb is not None else ta, yt=yt, sides=sides, cmd=cmd, note=note, file=fn))
    for fn, x in L["EVENTS"]:
        where = f"items/{fn} 事件 {x[0] if x else '?'}"
        if len(x) != 8: err(f"{where} 应有 8 项：名, 今地, 经, 纬, 起, 止, 年代文字, 按语"); continue
        nm, mod, lo, la, a, b, yt, note = x; chk_ll(where, lo, la)
        ta, tb = tt(where, a), tt(where, b, False)
        out["events"].append(dict(old=nm, mod=mod, lon=lo, lat=la, t=ta, t1=tb if tb is not None else ta, yt=yt, note=note, file=fn))
    for fn, x in L["CAPITALS"]:
        where = f"items/{fn} 都城 {x[0] if x else '?'}"
        if len(x) != 8: err(f"{where} 应有 8 项：名, 今地, 经, 纬, 所属单位键, 为都时段, 按语, 关联归属点"); continue
        nm, mod, lo, la, st, yrs, note, at = x; chk_ll(where, lo, la)
        if st not in UK: err(f"{where} 所属单位不存在：{st}")
        if at is not None and at not in SID: err(f"{where} 关联归属点不存在：{at}")
        segs = []
        for seg in yrs:
            if len(seg) != 2: err(f"{where} 为都时段应写成 [起, 止]"); continue
            a, b = tt(where, seg[0]), tt(where, seg[1])
            if a is not None and b is not None:
                if b <= a: err(f"{where} 为都时段止不晚于起：{seg}")
                segs.append([a, b])
        out["capitals"].append(dict(old=nm, mod=mod, lon=lo, lat=la, st=st, yrs=segs, note=note, at=at, file=fn))
    for fn, x in L["PASSES"]:
        where = f"items/{fn} 关隘 {x[0] if x else '?'}"
        if len(x) != 5: err(f"{where} 应有 5 项：名, 今地, 经, 纬, 按语"); continue
        nm, mod, lo, la, note = x; chk_ll(where, lo, la)
        out["passes"].append(dict(old=nm, mod=mod, lon=lo, lat=la, note=note, file=fn))
    for fn, x in L["CONCS"]:
        where = f"items/{fn} 租界 {x[0] if x else '?'}"
        if len(x) != 8: err(f"{where} 应有 8 项：名, 今地, 经, 纬, 所属国键, 起, 止, 按语"); continue
        nm, mod, lo, la, st, a, b, note = x; chk_ll(where, lo, la)
        if st not in UK: err(f"{where} 所属国不存在：{st}")
        out["concs"].append(dict(old=nm, mod=mod, lon=lo, lat=la, st=st, t0=tt(where, a), t1=tt(where, b, False), note=note, file=fn))
    for kind, key in (("rail", "RAILS"), ("road", "ROADS"), ("air", "AIRS")):
        for fn, x in L[key]:
            where = f"items/{fn} {key} {x[0] if x else '?'}"
            if len(x) != 6: err(f"{where} 应有 6 项：名, 今名, 坐标, 起, 止, 按语"); continue
            nm, mod, pts, a, b, note = x
            if not isinstance(pts, list) or len(pts) < 2: err(f"{where} 坐标至少两点"); continue
            for p in pts: chk_ll(where, p[0], p[1])
            out["lines"].append(dict(c=kind, old=nm, mod=mod, geo=[[float(p[0]), float(p[1])] for p in pts], t0=tt(where, a), t1=tt(where, b, False), note=note, file=fn))
    for fn, R in L["ROUTES"]:
        where = f"items/{fn} 行军 {R.get('name', '?')}"
        pts = []
        for p in R.get("pts", []):
            if len(p) != 4: err(f"{where} 每点应为 [经, 纬, 日期, 地名]"); continue
            chk_ll(where, p[0], p[1]); tp = tt(where, p[2])
            if tp is not None: pts.append([float(p[0]), float(p[1]), tp, p[3]])
        for a, b in zip(pts, pts[1:]):
            if b[2] < a[2]: err(f"{where} 日期倒退：{a[3]} → {b[3]}")
        if len(pts) < 2: err(f"{where} 至少两点"); continue
        out["routes"].append(dict(name=R["name"], mod=R.get("mod", ""), note=R.get("note", ""), yt=R.get("yt", ""), side=R.get("side", ""), pts=pts, file=fn))
    out["ranges"] = [x for fn, x in L["RANGES"]]
    out["seas"] = [x for fn, x in L["SEAS"]]
    return out

def load_all():
    nodes = load_nodes(); load_desc(nodes)
    seeds = load_seeds(); units = load_units()
    states, blocks = load_snaps(nodes, seeds, units) if nodes else ([], {})
    items = load_items(units, seeds)
    return dict(nodes=nodes, seeds=seeds, units=units, states=states, blocks=blocks, items=items)
