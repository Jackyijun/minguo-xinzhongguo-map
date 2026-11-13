# -*- coding: utf-8 -*-
"""把 build/geo.json、build/data.json、content/en/ 的英文和每个单位的颜色注入 src/template.html，
生成一个不依赖任何外部文件的 docs/index.html。

  python src/assemble.py           严格：有缺译或过期的英文就报错退出
  python src/assemble.py --draft   草稿：缺译、过期处临时显示中文，只给警告

没有 content/en/ 时 DATA.en 为 false，界面隐藏“中 | EN”切换。
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import i18n

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>[hidden]{display:none!important}</style>
"""

def check_english(geo, data, draft):
    missing, stale, unlocked = i18n.check(geo, data)
    from collections import Counter
    bad = missing + stale
    if unlocked:
        print(f"   提醒：{len(unlocked)} 条英文未登记指纹（改完英文后运行 python tools/i18n.py lock）")
    if not bad:
        print("   英文：齐全")
        return
    msg = (f"英文缺译 {len(missing)} 条、过期 {len(stale)} 条："
           + "、".join(f"{f} {n}" for f, n in Counter(f for f, _, _ in bad).items())
           + "。运行 python tools/i18n.py todo 查看清单。")
    if not draft:
        sys.exit("   " + msg + "\n   如只想先看效果，用 python run.py --html --draft（缺译处显示中文）。")
    print("   草稿模式，" + msg)


def main():
    draft = "--draft" in sys.argv[1:]
    geo = json.loads((C.BUILD / "geo.json").read_text(encoding="utf8"))
    data = json.loads((C.BUILD / "data.json").read_text(encoding="utf8"))
    data["en"] = (C.CONTENT / "en").is_dir()
    if data["en"]:
        check_english(geo, data, draft)
        geo, data = i18n.attach(geo, data)
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
    (C.DIST / ".nojekyll").write_text("", encoding="utf8")   # 让 GitHub Pages 原样发布，不经 Jekyll 处理
    out = C.DIST / "index.html"
    out.write_text(html, encoding="utf8")
    print("wrote", out, out.stat().st_size // 1024, "KB")

if __name__ == "__main__":
    main()
