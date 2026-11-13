# Republican China to the Early PRC

[![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-red.svg)](README.md) [![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)

An interactive historical map of China and all of Asia from the 1911 Revolution to victory in the War to Resist US Aggression and Aid Korea and the Geneva Conference (1911–1954, opening in 1910 with the last years of the Qing), in Chinese and English. It has 115 monthly snapshots: from the late Qing, Beiyang rule and the warlord wars, through the founding of the Communist Party of China, the first KMT–CPC cooperation and the Northern Expedition, the Central Plains War, the Nanchang and Autumn Harvest Uprisings, the revolutionary base areas and the Long March of the Red Army, to Japan's invasion of China and the nationwide War of Resistance, the Pacific War, the War of Liberation and the founding of the People's Republic of China, the War to Resist US Aggression and Aid Korea and the Vietnamese people's war of resistance against France, ending with the Geneva Conference of 1954. The view covers all of Asia: Japanese expansion, Korea, Siberia, Indochina, Southeast, South, Central and West Asia are all on the map.

The map has 319 states, factions, base areas and colonial divisions; the allegiance over time of 1,467 cities and towns; 471 battles, 499 events and 82 campaign routes (the four Long March routes and the Western Route Army, the Korean War, the advance into Xizang and the Indochina War are marked stage by stage with arrival dates); 134 capitals and seats, 84 railways, 49 concessions and leased territories and 33 passes.

---

## 1. Just look

Double-click **`docs/index.html`** and open it in any modern browser (Chrome, Edge, Safari, Firefox).

The file is about 12 MB, with all data, styles and scripts embedded: no network, no server and no external libraries. You can copy it to a USB stick, send it to someone, or put it on your own website.

- **Timeline**: at least one snapshot a year; years such as 1911, the Northern Expedition, the Long March, 1937, 1941–1942, 1945 and 1948–1949 are split into several monthly snapshots (the Long March, for example: setting out in 1934.10, the Xiang River in 1934.12, Zunyi in 1935.01 … Wuqizhen in 1935.10). Click a tick to jump, ▶ on the left to play, 1× / 2× below to change speed; ← → on the keyboard step through snapshots.
- **Coloring**: "Factions / States" in the top bar. In Factions mode the Beiyang cliques, regional strongmen, the central Nationalist Government, the CPC's Soviet areas and base areas, Japan's colonies and occupied areas, and the British, French, Dutch and US dependencies are colored separately; in States mode they merge into their state. Colors come in faction bands that do not overlap: the KMT line is blue (the provincial military governments of 1911 light blue); the CPC's Soviet areas, base areas, liberated areas and the PRC's greater regions are all red, told apart by shade; Japan with its colonies and occupied areas is dark purple, puppet regimes light purple, the Qing and the Beiyang centre yellow; all other regional powers and foreign states use only ochre, olive, green and teal at lower saturation.
- **Narrative**: the map follows the historical account current in the People's Republic of China (the unified history textbooks); from October 1949 only Gregorian years are used. Wording and evaluation follow that account; the facts are unchanged.
- **Hatching**: a gap between nominal and actual control — the puppet regimes set up by Japan (Puppet Manchukuo, East Hebei, Mengjiang, the North China Provisional Government, the Wang Jingwei regime and others), regional strongmen nominally obedient to Nanjing after 1928 but in fact independent, Xizang and Outer Mongolia, protectorates and mandates, and the border regions and base areas of 1937–1945 that were nominally under the Nationalist Government but in fact held by the CPC.
- **Campaign routes**: the stretch covered in the current period is drawn solid with arrows, earlier stretches dashed. The Long March, the Northern Expedition, the Japanese offensives, the Chinese Expeditionary Force, US island-hopping, the Soviet offensive into Northeast China, the advances after the three great campaigns and the Korean War are all there.
- **Era-specific layers**: railways (shown by their opening and dismantling dates), roads and the Hump air routes, concessions and leased territories (shown by their establishment and recovery dates), and the Yellow River flooded area (the river's diversion of 1938–1947).
- **Views**: the drop-down in the top bar has China, all of Asia, the Long March and 20 regions (including the Korean War and Indochina).
- **Language**: switch with "中 | EN" at the top right of the map (at the top right of the content in the Timeline and Gazetteer views); the choice is remembered in the browser, and adding `#en` to the URL opens the English version directly. In English, the map shows only English labels; tooltips, the index, the timeline and the gazetteer add the original Chinese after the English name. Search works in both languages, and English searches need no diacritics.

---

## 2. Live site

https://jackyijun.github.io/minguo-xinzhongguo-map/

---

## 3. Build locally

You only need to rebuild after changing the historical content (`content/`) or the parameters (`src/config.py`). You need **Python 3.10 or later** and at least 6 GB of memory.

**macOS / Linux**

```bash
cd minguo-xinzhongguo-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

**Windows (PowerShell)**

```powershell
cd minguo-xinzhongguo-map
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --open
```

A full build takes about 15–20 minutes (3.59 million raster cells, 115 snapshots); then open the newly generated `docs/index.html` in a browser.

| Command | What it does |
|---|---|
| `python run.py` | Check the content → download base data if missing → compute territories → assemble the HTML |
| `python run.py --html` | Only reassemble the HTML (when you changed only `src/template.html` or `content/en/`; a few seconds) |
| `python run.py --html --draft` | Build even if English translations are missing or stale (missing ones show the Chinese); without `--draft` the build stops with an error |
| `python tools/i18n.py status` | English status: how many entries are missing, stale or unregistered (see section 7) |
| `python run.py --open` | Open the result in a browser after building |
| `python tools/check.py` | Only check the content's format and references (a few seconds); `--node 1937.12` lists the places held by each unit at a snapshot, `--who 中共` lists how many places a unit holds at each snapshot |
| `python run.py --preview 1937.12,1944.12` | Also draw territory sketches of these snapshots to `build/preview-*.png` |
| `python tools/preview.py 1935.06 --box 99,118,24,39 --mode zhen` | Only draw a sketch, optionally within a longitude/latitude box (west,east,south,north) |
| `python tools/screenshot.py` | (Optional, needs playwright) step through every snapshot, take screenshots and check for script errors |
| `python tools/stats.py` | Count snapshots, entries, places and units |
| `python tools/verify.py` | Check snapshot by snapshot that every place lies inside its unit's territory; lists places more than 3 km outside |

The zip already includes the base data (`geodata/`, about 43 MB), so you can build offline; if you delete it, `run.py` downloads pinned versions from GitHub (the ETOPO terrain is also checked by sha256).

On the same setup, the same input always produces byte-identical output, so changes can be tracked with git.

After building, commit `docs/index.html` together with your changes and push to `main`; the live site updates automatically.

---

## 4. Directory layout

```
minguo-xinzhongguo-map/
├── run.py                 one-step build
├── requirements.txt
├── README.md              documentation (Chinese; shown by default on GitHub)
├── README.en.md           documentation (English)
├── docs/
│   ├── index.html         ★ the finished map, one file (GitHub Pages publishes /docs directly)
│   └── .nojekyll
├── content/               ★ historical content (hand-written; this is what you usually edit)
│   ├── AGENTS.md          content format and style rules (shared conventions when several people write)
│   ├── nodes.txt          115 snapshots: year.month | era | title
│   ├── desc/              snapshot descriptions, one file per period
│   ├── seeds/             1,467 places: cn China (incl. Outer Mongolia, Xizang, Taiwan), ne Northeast Asia, se Southeast Asia and the Pacific, sw South, Central and West Asia
│   ├── snaps/             allegiance at each snapshot: cn1–cn7 seven periods of China, ne, se, sw three regions
│   ├── units/             states, factions, base areas, colonial divisions: core.py the shared core, the rest by period and region
│   ├── notes/             notes for the shared units in core.py
│   ├── items/             capitals, battles, events, passes, concessions (cn1–cn7, ne, se, sw); railways, roads, air routes and the capitals of Chinese regimes (lines.py); campaign routes (routes.py)
│   ├── geo.py             mountain ranges, rivers, lakes, canals, deserts, sea names, the Yellow River flooded area
│   └── en/                ★ English version: translations matching the files above (JSON), zh.lock.json Chinese fingerprints, GLOSSARY.md naming conventions
├── src/
│   ├── config.py          ★ all paths and tunable parameters (extent, projection, raster, costs, border walls, colors …)
│   ├── content.py         reads and validates content/ (shared by build.py and tools/check.py)
│   ├── fetch_data.py      downloads pinned base data if missing
│   ├── build.py           computes territories, writes build/geo.json and build/data.json
│   ├── assemble.py        merges the English, checks for missing translations, injects the data into the template, writes docs/index.html
│   ├── i18n.py            English version: lists what needs translating, checks for missing and stale entries, merges translations into the data
│   └── template.html      front end: page structure, styles, interaction scripts
├── geodata/
│   ├── prov.json          modern Chinese provincial boundaries (simplified)
│   ├── ne/                Natural Earth 1:10m GeoJSON
│   └── etopo/             ETOPO20 global terrain
├── tools/
│   ├── check.py           content checks
│   ├── preview.py         matplotlib territory sketches
│   ├── screenshot.py      playwright screenshot check
│   ├── i18n.py            English maintenance: status / todo / lock / table
│   ├── stats.py           counts
│   └── verify.py          checks snapshot by snapshot that places lie inside their territories
└── build/                 intermediate files (safe to delete)
```

---

## 5. How it works

```
content/ ──────┐
               ├─► build.py ─► build/geo.json + data.json ─► assemble.py ─► docs/index.html
geodata/ ──────┘                                               ▲
                                                 src/template.html
```

### 1. Why the territories are computed

What can be established is "who held which city in which month"; continuous boundary lines are rarely known. So only the allegiance **place → unit → state** is written by hand (`content/snaps/`), and a "travel cost" map lets the computer infer the boundaries between places, keeping them on ridges and large rivers as far as possible.

This map uses a hybrid method. Modern international and colonial borders are precisely known and inference alone would misplace them (the China–Burma, China–India and Indochina borders, for instance), so modern borders (minus a few stretches that were undetermined or drawn later) and hand-drawn historical lines (the 38th parallel, the 50th parallel on Sakhalin, the northern limit of the Kwantung Leased Territory and others) are burned into the cost map as very expensive "border walls", and the inferred boundaries follow them. Walls can be time-limited: the 38th parallel applies only until the outbreak of the Korean War, after which the front line is set entirely by the places held; the Military Demarcation Line replaces it from July 1953, and the 17th parallel in Vietnam is added from July 1954. Factions, base areas, occupied areas and fronts inside China are still inferred entirely from the places held, and modern provincial boundaries act only as a weak wall. No wall is burned around towns that lie right on a border (Khiva, Sinuiju), so that a town is not cut off by its own wall and its cells are not taken by a distant place.

### 2. What `build.py` does

1. **Read the content**: `src/content.py` reads and validates all of `content/`. All dates are converted to a month index (year × 12 + month − 1).
2. **Parse the snapshots**: `snaps/*.txt` is a small declarative language (syntax below). Each `@year.month` block inherits all allegiances from the previous snapshot and lists only the changes; the first block of each Chinese period file starts with `!重置` (reset) and lists all Chinese places.
3. **Planar raster**: project first (Albers equal-area conic, standard parallels 25°N and 47°N, origin 32°N 103°E), then cut a regular grid in the projected plane (cells of about 7.3 km), covering 26°E–180°E, 11°S–72°N, minus Europe north of the Urals–Caspian–Caucasus and everything west of the Bosporus and the Red Sea. Lakes of 0.15 square degrees or more count as water.
4. **Cost raster**: each cell costs 1, plus ETOPO20 relief and plateaus above 2,500 m, the ridge lines in `geo.RANGES`, Natural Earth mountain polygons, boundary rivers (Yangtze, Yellow River, Huai, Nu, Yalu, Heilong, Mekong, Indus, Euphrates …), the border walls and the weak provincial walls, all multiplied by ±38% multi-scale smooth noise.
5. **Multi-source shortest paths**: all places are sources; one run of `scipy.sparse.csgraph.dijkstra(min_only=True)` on a 16-neighbour land grid assigns each cell to the place nearest in cost. Cells beyond the reach cost are unclaimed; the outer edge is closed and smoothed, and a smooth displacement field is added (fading to zero on both sides of border walls and boundary rivers).
6. **Polygons**: for each snapshot, cells are classified by allegiance, shared boundaries are traced where the smoothed values of two neighbouring classes are equal, smoothed with three rounds of Laplacian smoothing, assembled with `polygonize` into a coverage and simplified together with `coverage_simplify`. Geometry unchanged between snapshots is stored only once (`GEO.pool`).
7. **Colors**: each unit is first put in a faction band (`BANDS`): KMT line blue, 1911 military governments light blue, CPC red, Japan dark purple, puppet regimes light purple, Qing and Beiyang yellow, the rest ochre–olive–green–teal; the band is set in `BAND_UNITS` or decided automatically from the unit's states (units only under the CPC go to the red band, units only under Japan and puppet regimes to the purple band). Within a band, colors are assigned greedily by adjacency across all snapshots, pulling neighbours apart in lightness; British, French, Dutch and US dependencies stay close to the colors of their metropoles. A few states are fixed in `PRESET_COLORS`.
8. **Base map and entries**: coasts, modern borders, lakes and deserts come from Natural Earth; the eastern edge crosses the date line (including Hawaii and Midway). After the Huayuankou breach the Yellow River ran south from 1938.06 to 1947.03; for that period the map does not draw the modern lower course but the flooded area.

### 3. The front end (`src/template.html`)

- **No dependencies**: plain JavaScript + SVG.
- **Time**: each snapshot covers the months "after the previous snapshot up to this one". Battles, events and campaign routes show only for the current period; clicking an entry of another period in the index or the timeline moves the timeline there. Railways and concessions show by their start and end months.
- **Capitals**: only current capitals (solid squares) and former capitals that have already served (dashed squares) are shown.
- **Language**: all text is taken for the current language (through a few getters such as `LZ(zh, en)` and `iF(entry, field)`); switching redraws the map, the index, the timeline and the gazetteer. English labels use measured canvas widths for collision avoidance, and long names that do not fit inside a territory wrap onto two lines.
- **Themes**: all colors are CSS variables and follow the system light or dark mode; each unit's color is `--u-<index>`, injected by `assemble.py`.

---

## 6. Common changes

**Change who held a place in a given month**: add a line to that snapshot block in the right period's `snaps/*.txt`, for example giving Yueyang to the Japanese-occupied area in October 1938:

```
@1938.10
日占区: 岳阳
```

**Add a place**: add a line `ID longitude latitude modern-place [type] [N=year.month:name,…]` to the right regional file in `seeds/`, then assign it to a unit in the first snapshot block of every period file (`python tools/check.py` lists unassigned places).

**Renamed places**: add `N=1910:old-name,year.month:new-name` to the place, e.g. `N=1910:奉天,1929.4:沈阳,1932.3:奉天,1945.8:沈阳`.

**Add a snapshot**: insert `@year.month | era | title` in `nodes.txt`, write the description in `desc/`, then write that month's changes from the previous snapshot in the `snaps/*.txt` files concerned.

**Add battles, events, capitals, passes, concessions, railways**: add an entry in the right file in `items/` following the format; dates are written `"1937.08.13"` or `"1937.08"`. Battles and events are placed in their snapshots automatically by date.

**Add a campaign route**: add one in `items/routes.py`; each point in `pts` is `[longitude, latitude, "arrival date", place-name]`.

**Add a state, faction or base area**: add one in `units/` with `S(...)` (state), `Z(...)` (faction and other second-level units) or `T(...)` (tribe, unclaimed belt), then use its key in `snaps/`.

**A boundary should not cross a mountain**: add the ridge coordinates to `RANGES` in `geo.py`, with the last value `1` (main range, higher cost).

**Change only the page style or interaction**: edit `src/template.html`, then `python run.py --html`.

**Any new or changed Chinese** (places, entries, units, snapshot descriptions …): add or update the English in `content/en/` at the same time, otherwise the strict build reports missing or stale translations; see section 7.

### `snaps/*.txt` syntax

```
@1937.07                                        start a snapshot (inherits the previous one)
!重置                                           reset display names, parents, seats and hatching of this file group's units (cn1–cn7 form one group)
单位: 点 点 点                                  assign these places to the unit
单位[显示名]{治所}>所属政权: 点 ……              also set display name, seat and parent state (each optional)
单位[]:                                         clear the display name and restore the name in units
单位: @另一单位                                  move every place held by another unit at the start of this snapshot
·: 点 点                                        make unclaimed
+斜线: 单位 单位 / -斜线: 单位                    add or remove hatching (nominal ≠ actual control)
# comment
```

Display names, seats, parents and hatching carry over to later snapshots until rewritten or `!重置`.

---

## 7. The English version

Chinese is the source text; the English is written under the same keys in `content/en/`. When that folder exists, `assemble.py` turns on the "中 | EN" switch at the top right of the map (add `#en` to the URL to open the English directly).

| File | Contents | Key |
|---|---|---|
| `units.json` | states, factions, base areas, colonial divisions: full name `n`, short map label `s`, note `note` | unit key |
| `labels.json` | names a unit bears at particular snapshots | Chinese name |
| `seeds.json` | cities and towns: modern place `mod`, names at different dates `n` | place ID |
| `items.json` | entry fields `old` `mod` `note` `yt` `sides` `cmd`, place names along routes `p` | `category:name` (capitals add `@unit-key`) |
| `snaps.json` | snapshots: era `era`, title `t`, description `d` | `year.month` |
| `misc.json` | sea names, modern province names | Chinese name |

`zh.lock.json` records the fingerprint (first 10 hex digits of sha1) of the Chinese each English entry was written from. If the Chinese changes and the English does not, the build reports the entry as "stale". Naming and style rules are in `content/en/GLOSSARY.md` (pinyin and minority-area place names, foreign place names, stance terms, eras and dates, how battle results are written, and more).

After changing Chinese:

1. `python tools/i18n.py status` shows how many entries are missing or stale;
2. `python tools/i18n.py todo` lists their Chinese; add or revise the English in the matching JSON file;
3. `python tools/i18n.py lock` registers the new Chinese fingerprints;
4. `python run.py --html` reassembles. `python tools/i18n.py table` exports a Chinese–English table for review (`table names` exports names only).

The names were translated first and approved by the author, then the notes, snapshot descriptions and state notes; both rounds were checked independently, and problems found in the Chinese facts or modern places were fixed in the Chinese first, then in the English.

---

## 8. Tuning (`src/config.py`)

| Parameter | Default | Effect |
|---|---|---|
| `EXTENT` / `EXCLUDE` / `BASE_EXTENT` | 26°E–180°E, 11°S–72°N minus Europe and Africa / 5°E–215°E, 30°S–82°N | extent of the territory computation / of the base map |
| `CELL` | 1.15 | raster cell size (projection units, about 7.3 km). Smaller is finer; time and memory grow roughly with the square |
| `WALL` / `WALL_PROV` | (60, 14) / (5, 10) | peak cost and half-width (km) of border walls and of the weak modern provincial walls |
| `WALL_CARVE` | (8, 22) | no wall within 8 km of a place, full strength again at 22 km, so towns right on a border are not cut off |
| `WALL_SKIP` / `MANUAL_WALLS` / `VAR_NE_WALLS` | — | modern border stretches not used as permanent walls (Kashmir, the McMahon Line, the Korean Military Demarcation Line) / hand-drawn historical lines (optionally with start and end months) / time-limited modern borders (the Korean Military Demarcation Line from 1953.07) |
| `RANGE_MAJOR` / `RANGE_MINOR` | (8.0, 26) / (3.5, 18) | peak cost and half-width (km) of main and minor mountain ranges |
| `BORDER_RIVERS` | — | peak cost and half-width of boundary rivers |
| `NOISE_AMP` | 0.38 | smooth-noise amplitude; larger means more winding boundaries |
| `REACH` | 130 | cells beyond this cost distance (times each place's `R=` factor) are unclaimed |
| `SIMPLIFY_TERR` | 0.018 | coverage simplification tolerance (°); larger is coarser and smaller |
| `BANDS` / `BAND_UNITS` / `JP_POLS` | — | faction color bands, units assigned to a band, Japan and the puppet regimes |
| `PRESET_COLORS` | — | states with fixed colors |
| `FIRST` | 1937.12 | the snapshot shown first |

---

## 9. Sources and reliability

- **Base map**: [Natural Earth](https://www.naturalearthdata.com/) 1:10m vector data (public domain), pinned at commit `ca96624`; ETOPO20 terrain from the matplotlib basemap v1.4.1 sample data.
- **Modern provinces**: the simplified provincial boundaries of the *Between Tang and Song* map.
- **Historical content**: for China, official documents of each period, campaign histories and standard works of modern Chinese history; the late Qing follows, in outline, vol. 8 (Qing) of Tan Qixiang's *Historical Atlas of China*; the rest of Asia follows standard historical atlases and national histories in outline. Every entry has been through one round of independent checking.
- **Limitations**:
  - Territorial boundaries are indicative lines inferred from the allegiance of cities and county towns, not researched historical borders.
  - In the War of Resistance and the civil war the fronts were interlocked: Japanese forces mostly held only cities and lines of communication, while base areas and guerrilla zones lay in the countryside. The map works at the level of county towns, so it can only give the outline of this "points and lines" pattern.
  - In the warlord period the factions' garrison areas changed often; a snapshot shows the situation at the end of its month.
  - Places are sparse in Siberia, the Qinghai–Xizang Plateau, the Arabian Peninsula and New Guinea, so boundaries there are especially rough.
  - All dates are Gregorian.
  - The English is translated from the Chinese; stance terms follow the official English usage of the People's Republic of China, and naming conventions are in `content/en/GLOSSARY.md`.
