# -*- coding: utf-8 -*-
"""（可选）用无头浏览器给成品截图，并检查页面有没有脚本错误。

需要：pip install playwright && python -m playwright install chromium
  python tools/screenshot.py                         走一遍全部节点与两种着色、年表、对照表，报告脚本错误，再截首屏
  python tools/screenshot.py --node 1935.06 --fit cz  截某节点某视野（浅色、深色、手机宽度）
  python tools/screenshot.py --page path/to/index.html --quick
"""
import asyncio, os, argparse
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--page", default=str(ROOT / "docs" / "index.html"))
ap.add_argument("--node"); ap.add_argument("--fit"); ap.add_argument("--cm")
ap.add_argument("--out", default=str(ROOT / "build"))
ap.add_argument("--quick", action="store_true", help="不逐节点检查，只截图")
ap.add_argument("--only", default="desktop-light,desktop-dark,phone")
ap.add_argument("--zoom", type=float, default=0, help="在当前视野中心再放大几倍")
a = ap.parse_args()

async def main():
    out = Path(a.out); out.mkdir(exist_ok=True)
    page = Path(a.page).resolve().as_uri()
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}
        b = await p.chromium.launch(**kw)
        errors = []
        sizes = {"desktop-light": ((1440, 900), "light"), "desktop-dark": ((1440, 900), "dark"), "phone": ((400, 860), "light")}
        for i, name in enumerate(a.only.split(",")):
            vp, scheme = sizes[name]
            ctx = await b.new_context(viewport={"width": vp[0], "height": vp[1]}, color_scheme=scheme)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e, n=name: errors.append((n, str(e))))
            pg.on("console", lambda m, n=name: errors.append((n, m.text)) if m.type == "error" else None)
            await pg.goto(page); await pg.wait_for_timeout(1200)
            if i == 0 and not a.quick:
                n = await pg.locator(".tick").count()
                for cm in ("pol", "zhen"):
                    await pg.click(f'#cmode [data-cm="{cm}"]')
                    for j in range(n): await pg.click(f'.tick[data-j="{j}"]')
                for m in ("chron", "table", "map"): await pg.click(f'[data-mode="{m}"]'); await pg.wait_for_timeout(300)
            if a.cm: await pg.click(f'#cmode [data-cm="{a.cm}"]')
            if a.fit: await pg.select_option("#fit", a.fit); await pg.wait_for_timeout(700)
            if a.node:
                j = await pg.evaluate(f"[...document.querySelectorAll('.tick')].findIndex(b => b.querySelector('.yr').textContent === '{a.node.replace('.0', '.').replace('.', '·')}')")
                if j < 0: print("没有这个节点", a.node)
                else: await pg.click(f'.tick[data-j="{j}"]'); await pg.wait_for_timeout(500)
            if a.zoom:
                for _ in range(int(a.zoom)): await pg.click("#zin"); await pg.wait_for_timeout(550)
            tag = f"{name}" + (f"-{a.node}" if a.node else "") + (f"-{a.fit}" if a.fit else "") + (f"-z{int(a.zoom)}" if a.zoom else "")
            path = out / f"shot-{tag}.png"
            await pg.screenshot(path=str(path)); print("wrote", path)
            await ctx.close()
        await b.close()
        print("脚本错误：", errors[:20] or "无")

asyncio.run(main())
