# -*- coding: utf-8 -*-
"""把 build/geo.json、build/data.json 和每个单位的颜色注入 src/template.html，
生成一个不依赖任何外部文件的 docs/index.html。

英文版（第二轮）完成前，DATA.en 为 false，界面隐藏“中 | EN”切换。
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>[hidden]{display:none!important}</style>
"""

def main():
    geo = json.loads((C.BUILD / "geo.json").read_text(encoding="utf8"))
    data = json.loads((C.BUILD / "data.json").read_text(encoding="utf8"))
    data["en"] = (C.CONTENT / "en").is_dir()
    geo = json.dumps(geo, ensure_ascii=False, separators=(",", ":"))
    # 每个单位的浅色 / 深色主题颜色写成 CSS 变量 --u-<序号>
    light = " ".join(f"--u-{i}:{u['cl']};" for i, u in enumerate(data["units"]))
    dark = " ".join(f"--u-{i}:{u['cd']};" for i, u in enumerate(data["units"]))
    for u in data["units"]:
        u.pop("cl"); u.pop("cd")
    t = C.TEMPLATE.read_text(encoding="utf8")
    for key in ("__UCSS_LIGHT__", "__UCSS_DARK__", "__GEO__", "__DATA__"):
        assert key in t, f"模板缺少占位符 {key}"
    t = t.replace("__UCSS_LIGHT__", light).replace("__UCSS_DARK__", dark)
    t = t.replace("__GEO__", geo).replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    t = t.replace('\n<div class="app">', '\n</head>\n<body>\n<div class="app">', 1)
    html = HEAD + t + "\n</body>\n</html>\n"
    C.DIST.mkdir(exist_ok=True)
    (C.DIST / ".nojekyll").write_text("", encoding="utf8")
    out = C.DIST / "index.html"
    out.write_text(html, encoding="utf8")
    print("wrote", out, out.stat().st_size // 1024, "KB")

if __name__ == "__main__":
    main()
