# -*- coding: utf-8 -*-
"""民国形势图 · 数据构建。

读 content/ 的史料与 geodata/ 的底图，算出每个时间节点的疆域多边形，
写出 build/geo.json（几何）和 build/data.json（条目与说明）。

流程（规范第十三节，加本图的“混合做法”）：
  1. 读节点、归属点、单位与各节点归属（src/content.py）
  2. 在投影平面上建等距栅格，把海陆、大湖栅格化；疆域只在亚洲范围内推算（外框减去欧洲、非洲）
  3. 建通行代价栅格：地形起伏、高原、山脊、界河，再乘多尺度平滑噪声；
     今国界（剔除近代未定或晚出的段落）与手画的历史界线（三八线等）烧成高代价的“国界墙”，
     今中国省界烧成弱墙——国际与殖民地界因此贴合实际界线，境内派系、根据地、战线仍由归属点推算
  4. 以全部归属点为源做 16 邻接多源最短路，每个格子归代价距离最近的点
  5. 超出可达代价的为无主地；外缘闭运算、平滑，小空隙并回相邻一方；再加一层平滑位移场（国界墙、界河附近渐减为 0）
  6. 每个节点按“点 → 二级单位 → 政权”归属给格子分类，在相邻两类平滑值相等处描界，拼成覆盖图后整体简化
  7. 给相邻单位挑低饱和、互相区分的颜色（国民党蓝、中共红等预设）
  8. 整理底图（海岸、河湖、运河、山脉、荒漠、今国界，东端跨过日期变更线）与点、线条目
"""
import json, sys, math, gzip, zlib, time
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from skimage import measure
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import shape, box, LineString, Polygon, MultiPolygon, MultiLineString
from shapely.ops import unary_union
from shapely import affinity

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import config as C
import content as CT
sys.path.insert(0, str(C.CONTENT))
import geo as GM

LON0, LON1, LAT0, LAT1 = C.EXTENT
T0 = time.time()
BB = box(LON0 - 1, LAT0 - 1, LON1 + 1, LAT1 + 1)
EXT_BOX = box(LON0, LAT0, LON1, LAT1)
EXT_POLY = EXT_BOX.difference(unary_union([Polygon(p) for p in C.EXCLUDE]))
DEG = 1000 * math.pi / 180          # 一个纬度合多少投影单位（≈17.45）

# ======================================================================
# 0. 投影（与前端 proj() 完全一致）
# ======================================================================
RAD = math.pi / 180
_P1, _P2, _P0, _L0 = [v * RAD for v in C.PROJ]
NN = (math.sin(_P1) + math.sin(_P2)) / 2
CC = math.cos(_P1) ** 2 + 2 * NN * math.sin(_P1)
RHO0 = math.sqrt(CC - 2 * NN * math.sin(_P0)) / NN

def fwd(lon, lat):
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    r = np.sqrt(np.maximum(CC - 2 * NN * np.sin(lat * RAD), 1e-9)) / NN
    th = NN * (lon * RAD - _L0)
    return r * np.sin(th) * C.SCL, -(RHO0 - r * np.cos(th)) * C.SCL

def inv(x, y):
    X = np.asarray(x, float) / C.SCL; Y = RHO0 + np.asarray(y, float) / C.SCL
    r = np.hypot(X, Y); th = np.arctan2(X, Y)
    lon = (_L0 + th / NN) / RAD
    lat = np.arcsin(np.clip((CC - (r * NN) ** 2) / (2 * NN), -1, 1)) / RAD
    return lon, lat

def to_xy(g): return shapely.transform(g, lambda a: np.column_stack(fwd(a[:, 0], a[:, 1])))
def to_ll(g): return shapely.transform(g, lambda a: np.column_stack(inv(a[:, 0], a[:, 1])))

def enc_ring(coords):
    """坐标 ×100 取整后差分编码；前端 decode() 还原。"""
    out = []; px = py = 0
    for i, (x, y) in enumerate(coords):
        X, Y = int(round(x * 100)), int(round(y * 100))
        if i == 0: out += [X, Y]
        else:
            if X == px and Y == py: continue
            out += [X - px, Y - py]
        px, py = X, Y
    return out

def polys_of(g):
    if g is None or g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    if g.geom_type in ("MultiPolygon", "GeometryCollection"): return [p for x in g.geoms for p in polys_of(x)]
    return []
def lines_of(g):
    if g is None or g.is_empty: return []
    if g.geom_type == "LineString": return [g]
    if g.geom_type in ("MultiLineString", "GeometryCollection"): return [p for x in g.geoms for p in lines_of(x)]
    return []
def ne(name): return json.load(open(C.NE_DIR / f"{name}.geojson", encoding="utf8"))
def crc(s): return zlib.crc32(s.encode("utf8"))
WEST = box(-180, -90, C.BASE_EXTENT[1] - 360, 90)
def wrapped(g, clip):
    """把西经部分（日期变更线以东）平移 360° 接到东边，再裁到 clip。"""
    parts = [g.intersection(clip)] if g.intersects(clip) else []
    if g.intersects(WEST): parts.append(affinity.translate(g.intersection(WEST), 360, 0).intersection(clip))
    return [p for p in parts if not p.is_empty]

# ======================================================================
# 1—2. 史料
# ======================================================================
D = CT.load_all()
if CT.ERR:
    for e in CT.ERR[:60]: print("错误", e)
    sys.exit(f"史料有 {len(CT.ERR)} 处错误，先运行 python3 tools/check.py 修正")
for w in CT.WARN[:20]: print("提醒", w)
NODES, SEEDS, UNITS, STATES, IT = D["nodes"], D["seeds"], D["units"], D["states"], D["items"]
SID = {s["id"]: i for i, s in enumerate(SEEDS)}
UK = {u["k"]: i for i, u in enumerate(UNITS)}
for s in SEEDS:
    if not (LON0 < s["lon"] < LON1 and LAT0 < s["lat"] < LAT1): sys.exit("归属点在推算范围外：" + s["id"])
print("nodes", len(NODES), "seeds", len(SEEDS), "units", len(UNITS))
def pol_of(st, uk): return st["pol"].get(uk, UNITS[UK[uk]]["pol"])

# ======================================================================
# 3. 投影平面栅格、海陆
# ======================================================================
_lo = np.r_[np.linspace(LON0, LON1, 600), np.full(300, LON1), np.linspace(LON1, LON0, 600), np.full(300, LON0)]
_la = np.r_[np.full(600, LAT1), np.linspace(LAT1, LAT0, 300), np.full(600, LAT0), np.linspace(LAT0, LAT1, 300)]
_bx, _by = fwd(_lo, _la)
CELL = C.CELL
GX0 = math.floor(_bx.min() / CELL) * CELL - 2 * CELL; GY0 = math.floor(_by.min() / CELL) * CELL - 2 * CELL
NX = int(math.ceil((_bx.max() - GX0) / CELL)) + 2; NY = int(math.ceil((_by.max() - GY0) / CELL)) + 2
XC = GX0 + (np.arange(NX) + 0.5) * CELL; YC = GY0 + (np.arange(NY) + 0.5) * CELL
LONC, LATC = inv(XC[None, :], YC[:, None])
LONC = LONC.astype(np.float32); LATC = LATC.astype(np.float32)

def xy_to_rc(x, y): return (np.asarray(y) - GY0) / CELL - 0.5, (np.asarray(x) - GX0) / CELL - 0.5
def rc_to_ll(r, c): return inv(GX0 + (np.asarray(c) + 0.5) * CELL, GY0 + (np.asarray(r) + 0.5) * CELL)

def rasterize(geoms_ll):
    """多边形（经纬度）→ 格子掩膜。每块多边形在自己的外接框里用 PIL 扫描线填充（外环填 1、内环填 0）再并入。"""
    m = np.zeros((NY, NX), bool)
    for g in geoms_ll:
        for p in polys_of(to_xy(g)):
            e = np.asarray(p.exterior.coords); r, c = xy_to_rc(e[:, 0], e[:, 1])
            r0, r1 = max(0, int(r.min()) - 1), min(NY, int(r.max()) + 2); c0, c1 = max(0, int(c.min()) - 1), min(NX, int(c.max()) + 2)
            if r1 <= r0 or c1 <= c0: continue
            im = Image.new("1", (c1 - c0, r1 - r0), 0); dr = ImageDraw.Draw(im)
            dr.polygon(list(zip(c - c0, r - r0)), fill=1)
            for h in p.interiors:
                a = np.asarray(h.coords); hr, hc = xy_to_rc(a[:, 0], a[:, 1])
                if len(a) >= 3: dr.polygon(list(zip(hc - c0, hr - r0)), fill=0)
            m[r0:r1, c0:c1] |= np.array(im, bool)
    return m

def densify_ll(g, step=0.25):
    """经纬度多边形加密后再投影，免得长直边投影后偏离纬线弧。"""
    return shapely.segmentize(g, step)
INEXT = rasterize([densify_ll(EXT_POLY)])
print("grid", NX, "x", NY, "=", NX * NY, "cells; in extent", int(INEXT.sum()))

LANDG = []
for nm in ("ne_10m_land", "ne_10m_minor_islands"):
    for f in ne(nm)["features"]:
        g = shape(f["geometry"])
        if g.intersects(BB): LANDG += polys_of(g.intersection(BB))
landU = unary_union(LANDG)
LAKEG = []
SKIP_LAKES = {"South Aral Sea", "North Aral Sea"} | set(getattr(GM, "SKIP_LAKES_EXTRA", ()))
KEEP_RESERVOIR = {"Lake Zaysan"}
for f in ne("ne_10m_lakes")["features"]:
    if not f["geometry"]: continue
    p = f["properties"]; nm = p.get("name")
    if nm in SKIP_LAKES: continue
    if p.get("featurecla") == "Reservoir" and nm not in KEEP_RESERVOIR: continue
    g = shape(f["geometry"])
    if g.intersects(BB): LAKEG.append((nm, g.intersection(BB)))
for f in ne("ne_10m_lakes_historic")["features"]:
    if not f["geometry"]: continue
    nm = f["properties"].get("name")
    if nm in ("Lop Nur", "Aral Sea"):
        g = shape(f["geometry"])
        if g.intersects(BB): LAKEG.append((nm, g.intersection(BB)))
LAND = rasterize([landU]) & INEXT
WATER = rasterize([g for n, g in LAKEG if g.area > C.BIG_LAKE_AREA])
LAND &= ~WATER
print(f"[{time.time()-T0:.0f}s]", "land cells", int(LAND.sum()))

# ======================================================================
# 4. 通行代价栅格
# ======================================================================
cost = np.ones((NY, NX), np.float64)
_E = np.loadtxt(gzip.open(C.ETOPO_DIR / "etopo20data.gz"))
_Elon = np.loadtxt(gzip.open(C.ETOPO_DIR / "etopo20lons.gz")); _Elat = np.loadtxt(gzip.open(C.ETOPO_DIR / "etopo20lats.gz"))
_rel = ndimage.maximum_filter(_E, 3) - ndimage.minimum_filter(_E, 3)
_lo2 = np.where(LONC < _Elon[0], LONC + 360, LONC); _lo2 = np.where(_lo2 > _Elon[-1], _lo2 - 360, _lo2)
_fi = (_lo2 - _Elon[0]) / (_Elon[1] - _Elon[0]); _fj = (LATC - _Elat[0]) / (_Elat[1] - _Elat[0])
ELEV = ndimage.map_coordinates(_E, [_fj, _fi], order=1, mode="nearest")
RELIEF = ndimage.map_coordinates(_rel, [_fj, _fi], order=1, mode="nearest")
cost += C.TERRAIN_RELIEF * np.clip(RELIEF / 1000, 0, 3) + C.TERRAIN_HIGH * np.clip((ELEV - 2500) / 1000, 0, 3)

KM = 6371.0 / C.SCL       # 一个投影单位合多少公里
def wiggle_xy(pts_ll, name, amp_km, wave_km):
    """把手绘脊线加密，并按名字确定的相位做横向摆动（投影平面内）。"""
    ls = LineString(pts_ll)
    n = max(2, int(ls.length / 0.04))
    P = np.array([ls.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)])
    x, y = fwd(P[:, 0], P[:, 1])
    if amp_km <= 0: return x, y
    dx = np.gradient(x); dy = np.gradient(y); L = np.hypot(dx, dy) + 1e-9
    s = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))] * KM
    h = crc(name); ph1 = (h % 1000) / 1000 * 2 * math.pi; ph2 = (h // 1000 % 1000) / 1000 * 2 * math.pi
    off = (np.sin(2 * math.pi * s / wave_km + ph1) + 0.5 * np.sin(2 * math.pi * s / (wave_km / 2.3) + ph2)) * amp_km / 1.5
    taper = np.minimum(1, np.minimum(s, s[-1] - s) / (wave_km / 2 + 1e-9))
    off = off * taper / KM
    return x - dy / L * off, y + dx / L * off

def line_mask(lines_xy):
    m = np.zeros((NY, NX), bool)
    for x, y in lines_xy:
        ls = LineString(np.column_stack([x, y]))
        if ls.length == 0: continue
        n = max(2, int(ls.length / (CELL / 3)))
        P = np.array([ls.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)])
        r, c = xy_to_rc(P[:, 0], P[:, 1]); r = np.round(r).astype(int); c = np.round(c).astype(int)
        ok = (r >= 0) & (r < NY) & (c >= 0) & (c < NX); m[r[ok], c[ok]] = True
    return m
def burn(lines_xy, amp, sig_km):
    if not lines_xy: return 0
    m = line_mask(lines_xy)
    d = ndimage.distance_transform_edt(~m) * CELL * KM
    return amp * np.exp(-(d / sig_km) ** 2)
def ll_lines_xy(geoms):
    out = []
    for g in geoms:
        for ls in lines_of(g):
            a = np.asarray(shapely.segmentize(ls, 0.05).coords)
            if len(a) >= 2: out.append(fwd(a[:, 0], a[:, 1]))
    return out

R_MAJOR = [r for r in GM.RANGES if r[4]]; R_MINOR = [r for r in GM.RANGES if not r[4]]
cost += burn([wiggle_xy(r[2], r[0], *C.RANGE_WIGGLE) for r in R_MAJOR], *C.RANGE_MAJOR)
cost += burn([wiggle_xy(r[2], r[0], *C.RANGE_WIGGLE) for r in R_MINOR], *C.RANGE_MINOR)
RANGEPOLY, DESERTPOLY = [], {}
for f in ne("ne_10m_geography_regions_polys")["features"]:
    p = f["properties"]
    if not f["geometry"]: continue
    g = shape(f["geometry"])
    if not g.intersects(BB): continue
    if p.get("FEATURECLA") == "Range/mtn" and g.area < 60: RANGEPOLY.append(g.intersection(BB))
    if p.get("FEATURECLA") == "Desert": DESERTPOLY[p.get("NAME")] = g
cost += C.RANGE_POLY[0] * ndimage.gaussian_filter(rasterize(RANGEPOLY).astype(np.float32), C.RANGE_POLY[1])

NE_RV = []
for f in ne("ne_10m_rivers_lake_centerlines")["features"]:
    g = f["geometry"]
    if not g: continue
    gg = shape(g)
    if not gg.intersects(BB): continue
    p = f["properties"]
    for ls in lines_of(gg.intersection(EXT_BOX)):
        NE_RV.append((p.get("name"), p.get("scalerank"), ls))
_byamp = {}
for n, sr, ls in NE_RV:
    if n in C.BORDER_RIVERS:
        a = np.asarray(ls.coords); _byamp.setdefault(C.BORDER_RIVERS[n], []).append(fwd(a[:, 0], a[:, 1]))
RIVMASK = np.zeros((NY, NX), bool)
for (amp, sig), L in sorted(_byamp.items()):
    cost += burn(L, amp, sig); RIVMASK |= line_mask(L)

# 4b 国界墙：今国界（剔除 WALL_SKIP 内的段落）+ 手画的历史界线；今中国省界为弱墙
CTRY_ALL = [(f["properties"]["ADM0_A3"], shape(f["geometry"])) for f in ne("ne_10m_admin_0_countries_chn")["features"] if f["geometry"]]
CTRY_BB = [(a, g.intersection(BB)) for a, g in CTRY_ALL if g.intersects(BB)]
_coast = landU.boundary.buffer(0.04)
_bl = unary_union([g.boundary for a, g in CTRY_BB]).difference(_coast)
_skip = unary_union([Polygon(p) for p in C.WALL_SKIP])
WALL_LL = _bl.difference(_skip).intersection(EXT_POLY.buffer(0.5))
def _mt(s_): y_, m_ = s_.split("."); return int(y_) * 12 + int(m_) - 1
def _mline(pts):
    a = np.asarray(shapely.segmentize(LineString(pts), 0.05).coords); return fwd(a[:, 0], a[:, 1])
# 有时效的墙：MANUAL_WALLS 第 3、4 项为起止月（"1950.06"，含起不含止）；VAR_NE_WALLS 取 WALL_SKIP 某框内的今国界
VAR = []
for w in C.MANUAL_WALLS:
    if len(w) > 2: VAR.append((w[0], [_mline(w[1])], _mt(w[2]) if w[2] else -10**9, _mt(w[3]) if w[3] else 10**9))
for nm, ib, a_, b_ in C.VAR_NE_WALLS:
    VAR.append((nm, ll_lines_xy([_bl.intersection(Polygon(C.WALL_SKIP[ib]))]), _mt(a_) if a_ else -10**9, _mt(b_) if b_ else 10**9))
WALL_LINES = ll_lines_xy([WALL_LL]) + [_mline(w[1]) for w in C.MANUAL_WALLS if len(w) == 2]
# 归属点附近不烧墙：贴着国界、省界的城镇（希瓦、新义州、柔佛巴鲁……）否则会被墙带围住，
# 本城的格子反被远处的点占去。墙在点周围 WALL_CARVE[0] 公里内为 0，到 WALL_CARVE[1] 公里恢复全强度
_sm = np.zeros((NY, NX), bool)
for s in SEEDS:
    r_, c_ = xy_to_rc(*fwd(s["lon"], s["lat"])); r_, c_ = int(round(float(r_))), int(round(float(c_)))
    if 0 <= r_ < NY and 0 <= c_ < NX: _sm[r_, c_] = True
_sd = ndimage.distance_transform_edt(~_sm) * CELL * KM
CARVE = np.clip((_sd - C.WALL_CARVE[0]) / (C.WALL_CARVE[1] - C.WALL_CARVE[0]), 0, 1).astype(np.float32)
del _sm, _sd
cost += burn(WALL_LINES, *C.WALL) * CARVE
WALLMASK = line_mask(WALL_LINES)
VARBURN = [burn(L, *C.WALL) * CARVE for _, L, _, _ in VAR]
VARMASK = [line_mask(L) for _, L, _, _ in VAR]
print("time-limited walls:", [(n, a_, b_) for n, _, a_, b_ in VAR])
PROV = json.load(open(C.PROV_JSON, encoding="utf8"))
def _dec(flat):
    out = []; x = y = 0
    for i in range(0, len(flat), 2): x += flat[i]; y += flat[i + 1]; out.append((x / 100, y / 100))
    return out
_pv = [Polygon(_dec(r)) for p in PROV for r in p["r"] if len(r) >= 6]
_pb = unary_union([g.boundary for g in _pv]).difference(_coast).difference(WALL_LL.buffer(0.1))
cost += burn(ll_lines_xy([_pb]), *C.WALL_PROV) * CARVE

# 4c 多尺度平滑噪声
rng = np.random.default_rng(C.SEED)
acc = np.zeros((NY, NX), np.float32)
for sg, w in C.NOISE_SCALES:
    n_ = ndimage.gaussian_filter(rng.standard_normal((NY, NX)).astype(np.float32), sg)
    acc += w * n_ / (n_.std() + 1e-9)
acc /= acc.std() + 1e-9
NOISEMUL = (1 + C.NOISE_AMP * np.clip(acc, -2, 2) / 2).astype(np.float32)
cost *= NOISEMUL
for i in range(len(VARBURN)): VARBURN[i] *= NOISEMUL
cost[~LAND] = -1          # 海、大湖与图外：不可通行
print(f"[{time.time()-T0:.0f}s]", "cost built; land cost mean", round(float(cost[LAND].mean()), 2))

# ======================================================================
# 5. 16 邻接多源最短路 → 每格最近的归属点
# ======================================================================
taken = set(); starts = []
for s in SEEDS:   # 吸附到最近的、未被占用的陆地格
    x, y = fwd(s["lon"], s["lat"]); r, c = xy_to_rc(x, y); r, c = int(round(float(r))), int(round(float(c)))
    best = None
    for rad in range(0, 12):
        cands = [(dr * dr + dc * dc, r + dr, c + dc) for dr in range(-rad, rad + 1) for dc in range(-rad, rad + 1)
                 if 0 <= r + dr < NY and 0 <= c + dc < NX and LAND[r + dr, c + dc] and (r + dr, c + dc) not in taken]
        if cands: best = min(cands); break
    if best is None: raise SystemExit("归属点不在陆地上：" + s["id"])
    taken.add((best[1], best[2])); starts.append((best[1], best[2]))
NL = int(LAND.sum())
nid = np.full((NY, NX), -1, np.int64); nid[LAND] = np.arange(NL)
DXW = ndimage.gaussian_filter(rng.standard_normal((NY, NX)).astype(np.float32), C.WARP_SIGMA)
DYW = ndimage.gaussian_filter(rng.standard_normal((NY, NX)).astype(np.float32), C.WARP_SIGMA)
DXW *= C.WARP_AMP / (DXW.std() + 1e-9); DYW *= C.WARP_AMP / (DYW.std() + 1e-9)
def label_grid(costg, wmask):
    rows, cols, ws = [], [], []
    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (1, -2), (2, 1), (2, -1)]:
        r0 = slice(0, NY - dr); r1 = slice(dr, NY)
        if dc >= 0: c0 = slice(0, NX - dc); c1 = slice(dc, NX)
        else: c0 = slice(-dc, NX); c1 = slice(0, NX + dc)
        a = nid[r0, c0]; b = nid[r1, c1]; ok = (a >= 0) & (b >= 0)
        w = (0.5 * (costg[r0, c0] + costg[r1, c1]) * math.hypot(dr, dc) * CELL)[ok]
        rows.append(a[ok]); cols.append(b[ok]); ws.append(w)
    G = coo_matrix((np.concatenate(ws), (np.concatenate(rows), np.concatenate(cols))), shape=(NL, NL)).tocsr()
    del rows, cols, ws
    sidx = np.array([nid[r, c] for r, c in starts])
    t0 = time.time()
    dist, _, src = dijkstra(G, directed=False, indices=sidx, min_only=True, return_predecessors=True)
    del G
    pos = np.full(NL, -1, np.int32)
    okv = src >= 0
    seedpos = {int(v): i for i, v in enumerate(sidx)}
    srcmap = np.full(NL, -1, np.int32)
    for v, i in seedpos.items(): srcmap[v] = i
    pos[okv] = srcmap[src[okv]]
    LAB = np.full((NY, NX), -1, np.int32); LAB[LAND] = pos
    cum = np.full((NY, NX), np.inf); cum[LAND] = dist
    print("labelled in", round(time.time() - t0, 1), "s; reached land", int((LAB >= 0).sum()), "/", NL)

    # 5b 无主地与外缘
    Rs = np.array([C.REACH * s["R"] for s in SEEDS])
    inreach = LAND & (LAB >= 0) & (cum <= Rs[np.clip(LAB, 0, None)])
    dil = ndimage.distance_transform_edt(~inreach) <= C.CLOSE_RADIUS
    closed = (ndimage.distance_transform_edt(dil) > C.CLOSE_RADIUS) & LAND
    lbl, nl = ndimage.label(LAND & ~closed)
    if nl:
        sz = ndimage.sum(np.ones_like(lbl), lbl, range(1, nl + 1))
        small = np.isin(lbl, np.nonzero(sz < C.HOLE_MAX)[0] + 1)
        closed |= small
    # 外缘平滑只磨推算范围的内陆外缘：海面当作“有主”参与平滑，免得海岛、半岛尖被磨掉
    owned = (ndimage.gaussian_filter((closed | ~LAND).astype(np.float32), C.EDGE_SIGMA) > 0.5) & LAND
    _, (jr, jc) = ndimage.distance_transform_edt(~inreach, return_indices=True)
    LABF = np.where(owned, LAB[jr, jc], -1).astype(np.int32)
    # 5c 位移场：界线带小弯；国界墙与界河两侧渐减为 0
    _, (jr, jc) = ndimage.distance_transform_edt(~(LABF >= 0), return_indices=True)
    ext_lab = np.where(LAND, LABF, LABF[jr, jc])
    taper = np.clip(ndimage.distance_transform_edt(~(wmask | RIVMASK)) / C.WARP_TAPER, 0, 1).astype(np.float32)
    dxw = DXW * taper; dyw = DYW * taper
    RI, CI = np.indices((NY, NX))
    wr = np.clip(np.round(RI + dyw).astype(int), 0, NY - 1); wc = np.clip(np.round(CI + dxw).astype(int), 0, NX - 1)
    LABW = np.where(LAND & owned, ext_lab[wr, wc], -1).astype(np.int32)
    LABW[(LABW < 0) & LAND & owned] = LABF[(LABW < 0) & LAND & owned]
    return LABW

def wall_key(t): return tuple(i for i, (_, _, a_, b_) in enumerate(VAR) if a_ <= t < b_)
LABWS = {}
for nd in NODES:
    k = wall_key(nd["t"])
    if k in LABWS: continue
    cg = cost.copy(); wm = WALLMASK.copy()
    for i in k: cg[LAND] += VARBURN[i][LAND]; wm |= VARMASK[i]
    LABWS[k] = label_grid(cg, wm); del cg, wm
    print("walls", [VAR[i][0] for i in k], "owned land", int((LABWS[k] >= 0).sum()))
LABW = LABWS[wall_key(NODES[-1]["t"])]


# ======================================================================
# 6. 各节点疆域：共享界线的覆盖图
# ======================================================================
SEA = ~LAND
_, (sjr, sjc) = ndimage.distance_transform_edt(SEA, return_indices=True)
seadist = ndimage.distance_transform_edt(SEA)

def partition(U):
    classes = sorted(set(np.unique(U).tolist()))
    best1 = np.full((NY, NX), -1.0, np.float32); best2 = np.full((NY, NX), -1.0, np.float32)
    arg1 = np.full((NY, NX), -2, np.int32); arg2 = np.full((NY, NX), -2, np.int32)
    sg = C.SMOOTH_SIGMA; pad = int(4 * sg) + 2
    for k in classes:
        m = U == k
        rows = np.nonzero(m.any(1))[0]; cols = np.nonzero(m.any(0))[0]
        r0, r1 = max(0, rows[0] - pad), min(NY, rows[-1] + pad + 1); c0, c1 = max(0, cols[0] - pad), min(NX, cols[-1] + pad + 1)
        g = ndimage.gaussian_filter(m[r0:r1, c0:c1].astype(np.float32), sg, truncate=3.0)
        B1 = best1[r0:r1, c0:c1]; B2 = best2[r0:r1, c0:c1]; A1 = arg1[r0:r1, c0:c1]; A2 = arg2[r0:r1, c0:c1]
        m1 = g > B1
        m2 = ~m1 & (g > B2)
        B2[m1] = B1[m1]; A2[m1] = A1[m1]; B1[m1] = g[m1]; A1[m1] = k
        B2[m2] = g[m2]; A2[m2] = k
    return arg1, best1, arg2, best2

def boundary_lines(A, B1, A2, B2):
    segs = []
    for axis in (1, 0):
        if axis == 1: a, b = A[:, :-1], A[:, 1:]; b1a, b1b = B1[:, :-1], B1[:, 1:]; b2a, b2b = B2[:, :-1], B2[:, 1:]
        else: a, b = A[:-1, :], A[1:, :]; b1a, b1b = B1[:-1, :], B1[1:, :]; b2a, b2b = B2[:-1, :], B2[1:, :]
        msk = (a != b) & ((a >= 0) | (b >= 0))
        r, c = np.nonzero(msk)
        da = b1a[r, c] - b2a[r, c]
        db = b1b[r, c] - b2b[r, c]
        t = np.clip(da / (da + db + 1e-9), 0.08, 0.92)
        if axis == 1:
            p0 = np.column_stack([GX0 + (c + 1) * CELL, GY0 + r * CELL]); p1 = np.column_stack([GX0 + (c + 1) * CELL, GY0 + (r + 1) * CELL])
            d = np.column_stack([GX0 + (c + 0.5 + t) * CELL, GY0 + (r + 0.5) * CELL])
        else:
            p0 = np.column_stack([GX0 + c * CELL, GY0 + (r + 1) * CELL]); p1 = np.column_stack([GX0 + (c + 1) * CELL, GY0 + (r + 1) * CELL])
            d = np.column_stack([GX0 + (c + 0.5) * CELL, GY0 + (r + 0.5 + t) * CELL])
        segs.append(np.stack([p0, d, p1], 1))
    S = np.concatenate(segs, 0)
    def ckey(xy): return (int(round((xy[1] - GY0) / CELL)), int(round((xy[0] - GX0) / CELL)))
    ends = np.concatenate([S[:, 0], S[:, 2]], 0)
    er = np.round((ends[:, 1] - GY0) / CELL).astype(np.int64); ec = np.round((ends[:, 0] - GX0) / CELL).astype(np.int64)
    ukeys, cnt = np.unique(er * (NX + 1) + ec, return_counts=True)
    JUNC = set((ukeys[cnt != 2]).tolist())
    isj = lambda xy: (ckey(xy)[0] * (NX + 1) + ckey(xy)[1]) in JUNC
    merged = shapely.line_merge(shapely.multilinestrings(shapely.linestrings(S)))
    chains = [np.asarray(l.coords) for l in lines_of(merged)]
    jun = {}
    for i, P in enumerate(chains):
        if not isj(P[0]): continue
        for end, nb in ((0, 1), (-1, -2)):
            jun.setdefault(ckey(P[end]), []).append(P[nb])
    jpos = {k: np.mean(v, 0) for k, v in jun.items()}
    out = []
    for P in chains:
        closed_ = not isj(P[0])
        if closed_:
            Q = P[1:-1:2]
            for _ in range(C.LAPLACE_ROUNDS):
                Q = Q + 0.5 * ((np.roll(Q, 1, 0) + np.roll(Q, -1, 0)) / 2 - Q)
            out.append(np.vstack([Q, Q[:1]]))
        else:
            Q = np.vstack([jpos[ckey(P[0])], P[1:-1:2], jpos[ckey(P[-1])]])
            for _ in range(C.LAPLACE_ROUNDS):
                Q[1:-1] = Q[1:-1] + 0.5 * ((Q[:-2] + Q[2:]) / 2 - Q[1:-1])
            out.append(Q)
    return out

def cover(A, lines, keys):
    noded = shapely.node(MultiLineString([LineString(q) for q in lines]))
    faces = [p for p in polys_of(shapely.polygonize(lines_of(noded))) if p.area > 0]
    pts = shapely.point_on_surface(faces)
    fx, fy = shapely.get_x(pts), shapely.get_y(pts)
    r = np.clip(np.floor((fy - GY0) / CELL).astype(int), 0, NY - 1); c = np.clip(np.floor((fx - GX0) / CELL).astype(int), 0, NX - 1)
    cls = A[r, c]
    groups = {}
    for f, k in zip(faces, cls.tolist()):
        if k >= 0: groups.setdefault(k, []).append(f)
    ks = [k for k in keys if k in groups]
    geoms = []
    for k in ks:
        try: g = shapely.coverage_union_all(groups[k])
        except Exception: g = unary_union(groups[k])
        geoms.append(to_ll(shapely.make_valid(g)))
    simp = shapely.coverage_simplify(np.array(geoms, dtype=object), C.SIMPLIFY_TERR, simplify_boundary=True) if geoms else []
    res = {}
    for k, g in zip(ks, simp):
        parts = []
        for p in polys_of(shapely.make_valid(g)):
            if p.area < C.MIN_PART_AREA: continue
            holes = [h for h in p.interiors if Polygon(h).area >= C.MIN_PART_AREA]
            parts.append(Polygon(p.exterior, holes))
        if parts: res[k] = MultiPolygon(parts)
    return res

def rings_of(mp):
    out = []
    for p in polys_of(mp):
        out.append(enc_ring(list(p.exterior.coords)))
        out += [enc_ring(list(h.coords)) for h in p.interiors]
    return out

def anchor(mask):
    """注记点：最大陆块的不可达极点。返回 [经, 纬, 面积(平方度), 内切半径(度)]。"""
    ml = mask & LAND
    if not ml.any(): ml = mask
    lab, n = ndimage.label(ml)
    sizes = ndimage.sum(ml, lab, range(1, n + 1))
    big = lab == (int(np.argmax(sizes)) + 1)
    rows = np.nonzero(big.any(1))[0]; cols = np.nonzero(big.any(0))[0]
    sub = big[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    dt = ndimage.distance_transform_edt(np.pad(sub, 1))[1:-1, 1:-1]
    r, c = np.unravel_index(np.argmax(dt), dt.shape)
    lo, la = rc_to_ll(r + rows[0], c + cols[0])
    k = CELL / DEG
    return [round(float(lo), 2), round(float(la), 2), round(float(ml.sum()) * k * k, 2), round(float(dt[r, c]) * k, 2)]

ADJ_Z, ADJ_P = set(), set()
def adj_pairs(own, S):
    for a, b in [(own[:, :-1], own[:, 1:]), (own[:-1, :], own[1:, :])]:
        m = (a != b) & (a >= 0) & (b >= 0)
        if m.any():
            pr = np.unique(np.stack([np.minimum(a[m], b[m]), np.maximum(a[m], b[m])], 1), axis=0)
            S.update(map(tuple, pr.tolist()))

POOL, POOLIX = [], {}
def pooled(rings):
    key = json.dumps(rings, separators=(",", ":"))
    if key not in POOLIX: POOLIX[key] = len(POOL); POOL.append(rings)
    return POOLIX[key]

OUTSN = []
_cache = {}
for nd, st in zip(NODES, STATES):
    own_seed = np.full(len(SEEDS), -1, np.int32)
    for sid, uk in st["own"].items():
        if uk is not None: own_seed[SID[sid]] = UK[uk]
    present = sorted(set(own_seed[own_seed >= 0].tolist()))
    polmap = {u: UK[pol_of(st, UNITS[u]["k"])] for u in present}
    ck = own_seed.tobytes() + json.dumps(sorted(polmap.items())).encode() + repr(wall_key(nd["t"])).encode()
    if ck in _cache:   # 归属与所属都没变：几何照搬
        z, p_, lz, lp, multi = _cache[ck]
    else:
        LW = LABWS[wall_key(nd["t"])]
        U = np.where(LW >= 0, own_seed[np.clip(LW, 0, None)], -1).astype(np.int32)
        U[~LAND] = -2
        fill = SEA & (seadist <= C.SEA_FILL_CELLS) & INEXT
        U[fill] = U[sjr[fill], sjc[fill]]
        U[fill & (U == -1)] = -2
        A, B1, A2, B2 = partition(U)
        PR = A.copy()
        for u, p in polmap.items(): PR[A == u] = p
        adj_pairs(np.where(LAND, A, -1), ADJ_Z); adj_pairs(np.where(LAND, PR, -1), ADJ_P)
        zpoly = cover(A, boundary_lines(A, B1, A2, B2), present)
        multi = sorted({p for u, p in polmap.items() if p != u or list(polmap.values()).count(p) > 1})
        ppoly = {}
        for p in multi:
            mem = [zpoly[u] for u in present if polmap[u] == p and u in zpoly]
            if mem:
                try: ppoly[p] = shapely.coverage_union_all(mem)
                except Exception: ppoly[p] = unary_union(mem)
        z = {str(k): pooled(rings_of(v)) for k, v in zpoly.items()}
        p_ = {str(k): pooled(rings_of(v)) for k, v in ppoly.items()}
        lz = {str(u): anchor(A == u) for u in present if (A == u).any()}
        lp = {str(p): anchor(PR == p) for p in multi if (PR == p).any()}
        _cache[ck] = (z, p_, lz, lp, multi)
    OUTSN.append(dict(y=nd["y"], m=nd["m"], t=nd["t"], era=nd["era"], ti=nd["title"], d=nd["d"], z=z, lz=lz, p=p_, lp=lp,
             own=own_seed.tolist(),
             pol={str(u): p for u, p in polmap.items()},
             lab={str(UK[k]): v for k, v in sorted(st["lab"].items()) if UK[k] in polmap or UK[k] in polmap.values()},
             seat={str(UK[k]): SID[v] for k, v in sorted(st["seat"].items()) if UK[k] in polmap},
             h=sorted(UK[k] for k in st["hatch"] if UK[k] in polmap or UK[k] in polmap.values())))
    print(f"[{time.time()-T0:.0f}s] snap", nd["id"], "units", len(present), "polities", len(set(polmap.values())), flush=True)
print("pool", len(POOL))

# ======================================================================
# 7. 配色：低饱和度，相邻单位尽量区分（OKLCH 空间贪心着色）
# ======================================================================
def oklch_to_rgb(L, Cc, h):
    a = Cc * math.cos(math.radians(h)); b = Cc * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def gam(x):
        x = max(0, min(1, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return "#%02X%02X%02X" % tuple(int(round(gam(v) * 255)) for v in (r, g, bb))
def lab_of_pal(p):
    L, Cc, h = p
    return np.array([L, Cc * math.cos(math.radians(h)), Cc * math.sin(math.radians(h))])
# 派系色带：每个单位归入一个色带，只在本色带内挑色；色带之间互不重叠（国民党蓝、共产党红、日本深紫、傀儡浅紫、清与北洋黄，其余土黄—绿—青绿）
def band_pal(bd):
    h0, h1, hs = bd["h"]; out = []
    for L in bd["L"]:
        for h in range(h0, h1 + 1, hs):
            for Cc in bd["C"]:
                out.append((L, Cc * (bd.get("hiL_C", 1.0) if L >= 0.72 else 1.0), h % 360))
    return out
BANDPAL = {k: band_pal(v) for k, v in C.BANDS.items()}
BANDLAB = {k: [lab_of_pal(p) for p in v] for k, v in BANDPAL.items()}
POLS_OF = {}
for sn in OUTSN:
    for u, p in sn["pol"].items(): POLS_OF.setdefault(int(u), set()).add(UNITS[p]["k"])
FIXED_BAND = {k: b for b, ks in C.BAND_UNITS.items() for k in ks}
def band_of(u):
    k = UNITS[u]["k"]
    if k in FIXED_BAND: return FIXED_BAND[k]
    ps = POLS_OF.get(u) or {k}
    if ps <= {"中共"}: return "ccp"
    if ps <= C.JP_POLS:
        if UNITS[u]["kind"] == "state": return "jp" if k == "日本" else "jpp"
        return "jp" if ps <= {"日本"} else "jpp"
    return "other"
BAND = {u: band_of(u) for u in range(len(UNITS))}
nbr = {i: set() for i in range(len(UNITS))}
for a, b in sorted(ADJ_Z | ADJ_P):
    nbr[a].add(b); nbr[b].add(a)
LIGHT, DARK, LABV = {}, {}, {}
def setcol(u, v):
    L, Cc, h = v
    LIGHT[u] = oklch_to_rgb(L, Cc, h); DARK[u] = oklch_to_rgb(min(C.DARK_L_MAX, L + C.DARK_L_LIFT), Cc + C.DARK_C_LIFT, h); LABV[u] = lab_of_pal(v)
for k, v in C.PRESET_COLORS.items():
    if k in UK: setcol(UK[k], v)
FAMILY = {"英国", "法国", "荷兰", "美国", "俄国", "葡萄牙"}   # 外国属地靠近宗主国的颜色（仍在本色带内）
usage = {}
for u in sorted(range(len(UNITS)), key=lambda u: (-len(nbr[u]), u)):
    if u in LIGHT: continue
    U_ = UNITS[u]; bd = BAND[u]; PALB, PLB = BANDPAL[bd], BANDLAB[bd]
    pref = U_.get("like") or (U_["pol"] if U_["pol"] in FAMILY and U_["pol"] != U_["k"] else None)
    best, bs = None, -1e9
    for j, p in enumerate(PALB):
        dmin = min([np.linalg.norm(PLB[j] - LABV[n]) for n in nbr[u] if n in LABV] + [1.0])
        score = dmin - C.REUSE_PENALTY * usage.get((bd, j), 0)
        if pref and pref in UK and UK[pref] in LABV: score -= 0.45 * np.linalg.norm(PLB[j] - LABV[UK[pref]])
        if score > bs: bs, best = score, j
    usage[(bd, best)] = usage.get((bd, best), 0) + 1
    setcol(u, PALB[best])
from collections import Counter as _Ct
print("bands:", dict(_Ct(BAND.values())))
for bd in ("kmt", "kmt0", "ccp", "jp", "jpp"):
    print(" ", bd, " ".join(UNITS[u]["k"] for u in sorted(BAND) if BAND[u] == bd))
mind = min([np.linalg.norm(LABV[a] - LABV[b]) for a, b in ADJ_Z if a in LABV and b in LABV] or [0])
print("min neighbour colour distance", round(float(mind), 3))
_worst = sorted((float(np.linalg.norm(LABV[a] - LABV[b])), UNITS[a]["k"], UNITS[b]["k"]) for a, b in ADJ_Z if a in LABV and b in LABV)[:10]
print("closest neighbour colours:", "; ".join(f"{x}/{y} {d:.3f}" for d, x, y in _worst))

# ======================================================================
# 8. 底图要素与条目
# ======================================================================
BLON0, BLON1, BLAT0, BLAT1 = C.BASE_EXTENT
BASEBOX = box(BLON0, BLAT0, min(180, BLON1), BLAT1)
_lb = []
for nm in ("ne_10m_land", "ne_10m_minor_islands"):
    for f in ne(nm)["features"]:
        if not f["geometry"]: continue
        for g in wrapped(shape(f["geometry"]), box(BLON0, BLAT0, BLON1, BLAT1)): _lb += polys_of(g)
landB = unary_union(_lb)
LAND_OUT = []
for p in polys_of(landB):
    p = p.simplify(C.SIMPLIFY_LAND)
    if p.is_empty or p.area < C.LAND_MIN_AREA: continue
    for q in polys_of(p):
        rings = [enc_ring(list(q.exterior.coords))] + [enc_ring(list(h.coords)) for h in q.interiors if Polygon(h).area > C.LAND_HOLE_MIN_AREA]
        LAND_OUT.append(rings)
print("land polys", len(LAND_OUT))

CTRY = []
for a, g in CTRY_ALL:
    for gg in wrapped(g, box(BLON0, BLAT0, BLON1, BLAT1)): CTRY.append(gg)
coastbuf = landB.boundary.buffer(0.03)
BORDER = []
_bl2 = unary_union([g.boundary for g in CTRY]).difference(coastbuf)
for ls in lines_of(shapely.line_merge(_bl2) if not _bl2.is_empty else _bl2):
    ls = ls.simplify(C.SIMPLIFY_BORDER)
    if ls.length > 0.08: BORDER.append(enc_ring(list(ls.coords)))
print("border lines", len(BORDER))
EXTPOLY = [enc_ring(list(densify_ll(p, 0.5).exterior.coords)) for p in polys_of(EXT_POLY)]

ITEMS = []
def add_item(d): d["i"] = len(ITEMS); ITEMS.append(d); return d["i"]

# 河流
NE_RV_OUT = []
for f in ne("ne_10m_rivers_lake_centerlines")["features"]:
    g = f["geometry"]
    if not g: continue
    p = f["properties"]
    for gg in wrapped(shape(g), box(BLON0, BLAT0, BLON1, BLAT1)):
        for ls in lines_of(gg): NE_RV_OUT.append((p.get("name"), p.get("scalerank"), ls))
RIVERS = []
river_item = {}
TB0, TB1 = CT.T(GM.HUANG_BREAK[0]), CT.T(GM.HUANG_BREAK[1])
for n, sr, ls in NE_RV_OUT:
    pts = list(ls.simplify(C.SIMPLIFY_RIVER).coords)
    if len(pts) < 2: continue
    xs = [x for x, y in pts]; ys = [y for x, y in pts]
    name = GM.river_alias(n, xs, ys)
    if name is False: continue
    info = GM.NE_RIVERS.get(name)
    kind = "faint"
    if sr is not None and sr <= 6: kind = "minor"
    if info: kind = "major" if info[3] else "minor"
    if sr is not None and sr > C.RIVER_MAX_SCALERANK and not info: continue
    if name == "Huang" and max(xs) > GM.HUANG_CUT_LON:
        # 花园口以下：1938.06—1947.03 改道，期间不画
        west = [(x, y) for x, y in pts if x <= GM.HUANG_CUT_LON]; east = [(x, y) for x, y in pts if x >= GM.HUANG_CUT_LON - 0.02]
        if len(west) > 1: RIVERS.append(dict(k=kind, p=enc_ring(west), nm=info[0], info=info, key="Huang"))
        if len(east) > 1:
            RIVERS.append(dict(k=kind, p=enc_ring(east), nm=info[0], info=info, key="Huang", y1=TB0))
            RIVERS.append(dict(k=kind, p=enc_ring(east), nm=info[0], info=info, key="Huang", y0=TB1))
        continue
    RIVERS.append(dict(k=kind, p=enc_ring(pts), nm=(info[0] if info else None), info=info, key=name if info else None))
for mr in GM.MANUAL_RIVERS:
    RIVERS.append(dict(k="major" if mr["major"] else "minor", p=enc_ring(mr["pts"]), nm=mr["nm"],
                       info=(mr["nm"], mr["mod"], mr["note"], mr["major"]), y0=CT.T(mr.get("y0")), y1=CT.T(mr.get("y1")), key=mr.get("key", mr["nm"])))
for r in RIVERS:
    if not r.get("nm"): r["it"] = None; continue
    info = r["info"]; key = r["nm"]
    if key not in river_item:
        river_item[key] = add_item(dict(c="river", sub="river", old=info[0], mod=info[1], note=info[2], major=bool(info[3]),
                                        **({"y0": r["y0"]} if r.get("y0") is not None and r.get("key") == "黄泛" else {}),
                                        **({"y1": r["y1"]} if r.get("y1") is not None and r.get("key") == "黄泛" else {})))
    r["it"] = river_item[key]
seglen = {}
for r in RIVERS:
    if r.get("it") is None: continue
    x = y = 0; pts = []
    for i in range(0, len(r["p"]), 2): x += r["p"][i]; y += r["p"][i + 1]; pts.append((x / 100, y / 100))
    if len(pts) < 2: continue
    L = LineString(pts).length
    if L > seglen.get(r["it"], (0, None))[0]:
        mid = LineString(pts).interpolate(0.5, normalized=True)
        seglen[r["it"]] = (L, [round(mid.x, 3), round(mid.y, 3)])
for it, (L, a) in seglen.items(): ITEMS[it]["anc"] = a
RIV_OUT = []
for r in RIVERS:
    d = dict(k=r["k"], p=r["p"])
    if r.get("it") is not None: d["it"] = r["it"]
    if r.get("y0") is not None: d["y0"] = r["y0"]
    if r.get("y1") is not None: d["y1"] = r["y1"]
    RIV_OUT.append(d)
print("rivers", len(RIV_OUT), "named", len(river_item))

LAKES = []
for f in ne("ne_10m_lakes")["features"] + [x for x in ne("ne_10m_lakes_historic")["features"] if x["properties"].get("name") in ("Lop Nur", "Aral Sea")]:
    if not f["geometry"]: continue
    p = f["properties"]; nm = p.get("name")
    if nm in SKIP_LAKES: continue
    if p.get("featurecla") == "Reservoir" and nm not in KEEP_RESERVOIR: continue
    for g in wrapped(shape(f["geometry"]), box(BLON0, BLAT0, BLON1, BLAT1)):
        info = GM.NE_LAKES.get(nm)
        if not info and g.area < 0.03: continue
        for pp in polys_of(g.simplify(0.01)):
            if pp.area < 0.004: continue
            it = None
            if info:
                ex = [x for x in ITEMS if x["c"] == "river" and x.get("sub") == "lake" and x["old"] == info[0]]
                if ex: it = ex[0]["i"]
                else:
                    c = pp.representative_point()
                    it = add_item(dict(c="river", sub="lake", old=info[0], mod=info[1], note=info[2], anc=[round(c.x, 2), round(c.y, 2)]))
            LAKES.append(dict(r=enc_ring(list(pp.exterior.coords)), **({"it": it} if it is not None else {})))
CAN = []
for nm, mod, pts, note in GM.CANALS:
    it = add_item(dict(c="canal", old=nm, mod=mod, note=note, anc=list(LineString(pts).interpolate(0.5, normalized=True).coords[0])))
    CAN.append(dict(p=enc_ring(pts), it=it))
for nm, mod, pts, note, major in GM.RANGES:
    a = LineString(pts).interpolate(0.5, normalized=True)
    add_item(dict(c="range", old=nm, mod=mod if mod != nm else "", note=note, geo=pts, anc=[round(a.x, 3), round(a.y, 3)], major=bool(major)))
DES = []
for nm, mod, nename, note in GM.DESERTS:
    g = DESERTPOLY.get(nename)
    if g is None: print("  没找到荒漠", nename); continue
    g = g.intersection(EXT_BOX)
    c = g.representative_point()
    it = add_item(dict(c="desert", old=nm, mod=mod if mod != nm else "", note=note, anc=[round(c.x, 2), round(c.y, 2)]))
    for p in polys_of(g.simplify(0.05)):
        DES.append(dict(r=enc_ring(list(p.exterior.coords)), it=it))

# 点状条目
for x in IT["capitals"]:
    add_item(dict(c="capital", old=x["old"], mod=x["mod"], lon=x["lon"], lat=x["lat"], st=UK[x["st"]], yrs=x["yrs"], note=x["note"], at=SID.get(x["at"]) if x["at"] else None))
for x in IT["battles"]:
    add_item(dict(c="battle", old=x["old"], mod=x["mod"], lon=x["lon"], lat=x["lat"], t=x["t"], t1=x["t1"], yt=x["yt"], sides=x["sides"], cmd=x["cmd"], note=x["note"]))
for x in IT["passes"]:
    add_item(dict(c="pass", old=x["old"], mod=x["mod"], lon=x["lon"], lat=x["lat"], note=x["note"]))
for x in IT["events"]:
    add_item(dict(c="event", old=x["old"], mod=x["mod"], lon=x["lon"], lat=x["lat"], t=x["t"], t1=x["t1"], yt=x["yt"], note=x["note"]))
for x in IT["concs"]:
    add_item(dict(c="conc", old=x["old"], mod=x["mod"], lon=x["lon"], lat=x["lat"], st=UK[x["st"]], t0=x["t0"], t1=x["t1"] if x["t1"] is not None else 9999 * 12, note=x["note"]))
for x in IT["lines"]:
    a = LineString(x["geo"]).interpolate(0.5, normalized=True)
    add_item(dict(c=x["c"], old=x["old"], mod=x["mod"], geo=x["geo"], anc=[round(a.x, 3), round(a.y, 3)], t0=x["t0"], t1=x["t1"] if x["t1"] is not None else 9999 * 12, note=x["note"]))
# 行军路线：每条一组 [经, 纬, 到达月序, 地名]，前端按节点画出已走过的一段
ROUTES = []
for R in IT["routes"]:
    pts = [list(p) for p in R["pts"]]
    it = add_item(dict(c="route", old=R["name"], mod=R["mod"], note=R["note"], side=R["side"], t=pts[0][2], t1=pts[-1][2], yt=R["yt"], anc=pts[len(pts) // 2][:2]))
    ROUTES.append(dict(it=it, pts=pts))
print("items", len(ITEMS), "routes", len(ROUTES))

# ======================================================================
# 输出
# ======================================================================
SEAS = [[n, lo, la, lv] for n, lo, la, lv in GM.SEAS]
FIRST = next((nd["t"] for nd in NODES if nd["id"] == C.FIRST), NODES[0]["t"])
GEO = dict(land=LAND_OUT, prov=PROV, border=BORDER, rivers=RIV_OUT, lakes=LAKES, canals=CAN, deserts=DES,
           pool=POOL, snaps=OUTSN, routes=ROUTES, seas=SEAS, ext=[LON0, LON1, LAT0, LAT1], extpoly=EXTPOLY,
           base=list(C.BASE_EXTENT), proj=list(C.PROJ), first=FIRST)
UOUT = [dict(k=u["k"], n=u["n"], kind=u["kind"], note=u.get("note", ""), cl=LIGHT[i], cd=DARK[i]) for i, u in enumerate(UNITS)]
SOUT = [dict(id=s["id"], n=s["n"], mod=s["mod"], lon=s["lon"], lat=s["lat"], t=s["t"], **({"nm": s["names"]} if s["names"] else {})) for s in SEEDS]
DATA = dict(units=UOUT, seeds=SOUT, items=ITEMS)
C.BUILD.mkdir(exist_ok=True)
json.dump(GEO, open(C.BUILD / "geo.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(DATA, open(C.BUILD / "data.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
np.save(C.BUILD / "label.npy", LABW)
print("geo.json", (C.BUILD / "geo.json").stat().st_size // 1024, "KB; data.json", (C.BUILD / "data.json").stat().st_size // 1024, "KB", f"[{time.time()-T0:.0f}s]")
