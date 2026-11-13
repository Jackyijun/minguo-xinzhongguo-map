# -*- coding: utf-8 -*-
"""英文版：把 content/en/ 下的译文并入构建结果，并检查缺译与过期。

中文是源文本。每一条要显示的中文都有一个“键/字段”，英文按同样的键写在 content/en/*.json 里：

  units.json    政权、派系、根据地、殖民地  {"国民政府": {"n": 全称, "s": 地图短名（可省）, "note": 说明}}
  labels.json   节点里的当年别名           {"东北军（张学良）": "Northeastern Army (Zhang Xueliang)"}
  seeds.json    城市与城镇（键为点的 ID）   {"西安": {"mod": 今地, "n": {"西安": …, "长安": …}}}
  items.json    条目（键为 类别:名称）      {"battle:台儿庄战役": {"old", "mod", "note", "yt", "sides", "cmd", "p": {路线地名: …}}}
                都城另加 @政权键             "capital:南京@国民政府"
  snaps.json    时间节点（键为 年.月）      {"1937.12": {"era": 纪年, "t": 标题, "d": 概述}}
  misc.json     海名与今省名               {"sea": {"南海": …}, "prov": {"河南": …}}

zh.lock.json 记着每条英文写成时对应中文的指纹。中文改了而英文没改，就是“过期”。
改完英文后运行 `python tools/i18n.py lock` 更新指纹。
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "content" / "en"
FILES = ["units", "labels", "seeds", "items", "snaps", "misc"]
LOCK = EN / "zh.lock.json"
ITEM_FIELDS = ("old", "mod", "note", "yt", "sides", "cmd")


def fp(zh):
    return hashlib.sha1(zh.encode("utf8")).hexdigest()[:10]


def load_en():
    out = {}
    for f in FILES:
        p = EN / f"{f}.json"
        out[f] = json.load(open(p, encoding="utf8")) if p.exists() else {}
    return out


def load_lock():
    return json.load(open(LOCK, encoding="utf8")) if LOCK.exists() else {}


UNIT_KEYS = []   # 单位序号 → 单位键；required()/attach() 开头填好


def item_key(it):
    """条目键“类别:名称”；同一城市作几个政权的都城时，都城键另加“@政权键”。"""
    k = f"{it['c']}:{it['old']}"
    return k + "@" + UNIT_KEYS[it["st"]] if it["c"] == "capital" else k


def snap_key(s):
    return f"{s['y']}.{s['m']:02d}"


def required(geo, data):
    """列出全部需要英文的 (文件, 路径, 中文)。路径是键名组成的元组。"""
    UNIT_KEYS[:] = [u["k"] for u in data["units"]]
    req = []
    for u in data["units"]:
        req.append(("units", (u["k"], "n"), u["n"]))
        if u.get("note"): req.append(("units", (u["k"], "note"), u["note"]))
    labs = sorted({v for s in geo["snaps"] for v in s["lab"].values()})
    for v in labs: req.append(("labels", (v,), v))
    for s in data["seeds"]:
        if s["t"] == "r": continue
        if s.get("mod"): req.append(("seeds", (s["id"], "mod"), s["mod"]))
        names = [s["n"]] + [n for _, n in (s.get("nm") or [])]
        for n in dict.fromkeys(names): req.append(("seeds", (s["id"], "n", n), n))
    for it in data["items"]:
        k = item_key(it)
        for f in ITEM_FIELDS:
            if it.get(f): req.append(("items", (k, f), it[f]))
    for R in geo.get("routes", []):
        k = item_key(data["items"][R["it"]])
        for p in dict.fromkeys(p[3] for p in R["pts"] if p[3]): req.append(("items", (k, "p", p), p))
    for s in geo["snaps"]:
        y = snap_key(s)
        for f, src in (("era", "era"), ("t", "ti"), ("d", "d")):
            if s.get(src): req.append(("snaps", (y, f), s[src]))
    for n, *_ in geo.get("seas", []): req.append(("misc", ("sea", n), n))
    for p in geo.get("prov", []): req.append(("misc", ("prov", p["n"]), p["n"]))
    return req


def get(en, f, path):
    v = en.get(f, {})
    for k in path:
        if not isinstance(v, dict) or k not in v: return None
        v = v[k]
    return v if isinstance(v, str) and v.strip() else None


def lock_key(f, path):
    return f + "/" + "/".join(path)


def check(geo, data, en=None, lock=None):
    en = en if en is not None else load_en()
    lock = lock if lock is not None else load_lock()
    missing, stale, unlocked = [], [], []
    for f, path, zh in required(geo, data):
        if get(en, f, path) is None: missing.append((f, path, zh)); continue
        lk = lock.get(lock_key(f, path))
        if lk is None: unlocked.append((f, path, zh))
        elif lk != fp(zh): stale.append((f, path, zh))
    return missing, stale, unlocked


def attach(geo, data, en=None):
    """把英文写进 geo/data（缺译时退回中文），返回 (geo, data)。"""
    en = en if en is not None else load_en()
    g = lambda f, *path: get(en, f, path)
    UNIT_KEYS[:] = [u["k"] for u in data["units"]]
    for u in data["units"]:
        u["ne"] = g("units", u["k"], "n") or u["n"]
        s = g("units", u["k"], "s")
        if s: u["se"] = s
        u["notee"] = g("units", u["k"], "note") or u.get("note", "")
    for s in data["seeds"]:
        if s["t"] == "r": continue
        s["ne"] = g("seeds", s["id"], "n", s["n"]) or s["n"]
        if s.get("nm"): s["nme"] = [g("seeds", s["id"], "n", n) or n for _, n in s["nm"]]
        s["mode"] = g("seeds", s["id"], "mod") or s.get("mod", "")
    for it in data["items"]:
        k = item_key(it)
        it["e"] = {f: (g("items", k, f) or it[f]) for f in ITEM_FIELDS if it.get(f)}
    for R in geo.get("routes", []):
        k = item_key(data["items"][R["it"]])
        R["pe"] = [(g("items", k, "p", p[3]) or p[3]) if p[3] else "" for p in R["pts"]]
    for s in geo["snaps"]:
        y = snap_key(s)
        s["erae"] = g("snaps", y, "era") or s.get("era", "")
        s["te"] = g("snaps", y, "t") or s["ti"]
        s["de"] = g("snaps", y, "d") or s.get("d", "")
        s["labe"] = {u: (g("labels", v) or v) for u, v in s["lab"].items()}
    geo["seas"] = [[n, lo, la, lv, g("misc", "sea", n) or n] for n, lo, la, lv, *_ in geo.get("seas", [])]
    for p in geo.get("prov", []): p["ne"] = g("misc", "prov", p["n"]) or p["n"]
    return geo, data
