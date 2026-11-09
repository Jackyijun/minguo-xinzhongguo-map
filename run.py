# -*- coding: utf-8 -*-
"""民国形势图 · 一键构建。

  python run.py               检查史料 → 底图缺失则下载 → 计算疆域 → 生成 docs/index.html
  python run.py --html        只重新拼装 HTML（改了 src/template.html 时用，几秒钟）
  python run.py --open        构建完成后用浏览器打开
  python run.py --preview 1937.12,1944.12
                              构建后用 matplotlib 画出这几个节点的疆域草图（build/preview-*.png）
"""
import argparse, subprocess, sys, time, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

def step(title, script, args=()):
    print(f"\n== {title} ==")
    t0 = time.time()
    r = subprocess.run([sys.executable, str(script), *args], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"失败：{title}")
    print(f"   用时 {time.time() - t0:.1f}s")

def main():
    ap = argparse.ArgumentParser(description="构建民国形势图")
    ap.add_argument("--html", action="store_true", help="跳过计算，只重新拼装 HTML")
    ap.add_argument("--open", action="store_true", help="完成后在浏览器中打开")
    ap.add_argument("--preview", metavar="NODES", help="逗号分隔的节点（年.月），画疆域草图")
    a = ap.parse_args()
    if not a.html:
        step("检查史料", ROOT / "tools" / "check.py")
        step("下载底图（已有则跳过）", SRC / "fetch_data.py")
        step("计算疆域（约 10—20 分钟）", SRC / "build.py")
    step("拼装 HTML", SRC / "assemble.py")
    if a.preview:
        step("画草图", ROOT / "tools" / "preview.py", [a.preview])
    out = ROOT / "docs" / "index.html"
    print(f"\n完成：{out}")
    if a.open:
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
