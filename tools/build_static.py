#!/usr/bin/env python3
"""把仓库根目录的前端（index.html + assets）打成静态站，供 GitHub Pages / Vercel 使用。

要点：
- CSS / JS 内联进 HTML（减少请求，且绕开某些 CDN 的 MIME 限制）；
- **图片、字体保持独立文件**（原样复制 assets/ 到各发布目录），
  因为 app.js 会在运行时拼接 `assets/img/<skin>.png` 切换皮肤，
  内联成 data URI 反而会漏掉这些动态引用；
- 原作者 v1.3.0 起不再带 web-bridge.js（桌面版专用），这里注入 tools/web-bridge.js，
  把 window.pywebview.api 的 solve_limit / plot_range 转发到线上 API；
- 计算请求指向绝对地址，跨域由服务端 CORS 放行。

用法：
    API_BASE=https://xxx.ap-shanghai.tencentscf.com python tools/build_static.py
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_INDEX = ROOT / "index.html"
BRIDGE = ROOT / "tools" / "web-bridge.js"
API_BASE = os.environ.get("API_BASE", "https://1521327887-jiher90lo8.ap-shanghai.tencentscf.com").rstrip("/")
API_ENDPOINT = API_BASE + "/api/solve"

# 需要产出的发布目录（docs = GitHub Pages，web_version = Vercel）
OUT_DIRS = (ROOT / "docs", ROOT / "web_version", ROOT / "web_version" / "public")


def build_html() -> str:
    html = SRC_INDEX.read_text(encoding="utf-8")

    def css_repl(match: "re.Match[str]") -> str:
        target = ROOT / match.group(1)
        if not target.is_file():
            return match.group(0)
        return "<style>\n" + target.read_text(encoding="utf-8") + "\n</style>"

    html = re.sub(r'<link[^>]*href="([^"]+\.css)"[^>]*>', css_repl, html)

    def js_repl(match: "re.Match[str]") -> str:
        rel = match.group(1)
        target = ROOT / rel
        if not target.is_file():
            return match.group(0)
        js = target.read_text(encoding="utf-8")
        # 兼容旧版带 web-bridge 的仓库：顺手把相对接口改绝对
        js = js.replace('var ENDPOINT = "/api/solve";', 'var ENDPOINT = "%s";' % API_ENDPOINT)
        block = "<script>\n" + js + "\n</script>"
        if rel.endswith("app.js") and BRIDGE.is_file():
            bridge_js = BRIDGE.read_text(encoding="utf-8").replace(
                'var BASE = window.__CALC_API_BASE__ || "";',
                'var BASE = window.__CALC_API_BASE__ || "%s";' % API_BASE,
            )
            pre = (
                '<script>window.__CALC_API_BASE__ = "%s";</script>\n<script>\n%s\n</script>\n'
                % (API_BASE, bridge_js)
            )
            return pre + block
        return block

    return re.sub(r'<script[^>]*src="([^"]+\.js)"[^>]*></script>', js_repl, html)


def main() -> int:
    if not SRC_INDEX.is_file():
        print("index.html 不存在", file=sys.stderr)
        return 1

    html = build_html()

    for out in OUT_DIRS:
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(html, encoding="utf-8")
        # 图片/字体等静态资源原样复制（皮肤切换是运行时拼路径的）
        assets_src = ROOT / "assets"
        assets_dst = out / "assets"
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        if assets_src.is_dir():
            shutil.copytree(assets_src, assets_dst)

    left = re.findall(r'(?:src|href)="(?!https?:|#)([^"]+\.(?:css|js))"', html)
    print("已生成 docs/ web_version/ web_version/public/（%.1f KB），接口=%s" % (len(html) / 1024, API_BASE))
    if left:
        print("警告：仍有未内联的 css/js 外链：%s" % ", ".join(sorted(set(left))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
