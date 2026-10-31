#!/usr/bin/env python3
"""把仓库根目录的前端（index.html + assets）打成单文件 docs/index.html。

用途：GitHub Pages 纯静态托管。
- CSS / JS / 图片全部内联（图片转 data URI），页面只依赖一个文件；
- 原作者 v1.3.0 起不再带 web-bridge.js（桌面版专用），这里注入 tools/web-bridge.js，
  把 window.pywebview.api 的 solve_limit / plot_range 转发到线上 API；
- 计算请求指向绝对地址，跨域由服务端 CORS 放行。

用法：
    API_BASE=https://xxx.ap-shanghai.tencentscf.com python tools/build_static.py
"""

from __future__ import annotations

import base64
import mimetypes
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_INDEX = ROOT / "index.html"
BRIDGE = ROOT / "tools" / "web-bridge.js"
OUT_INDEX = ROOT / "docs" / "index.html"
API_BASE = os.environ.get("API_BASE", "https://1521327887-jiher90lo8.ap-shanghai.tencentscf.com").rstrip("/")
API_ENDPOINT = API_BASE + "/api/solve"


def data_uri(rel: str) -> str | None:
    target = (ROOT / rel).resolve()
    if not str(target).startswith(str(ROOT)) or not target.is_file():
        return None
    ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return "data:%s;base64,%s" % (ctype, base64.b64encode(target.read_bytes()).decode("ascii"))


def inline_css(css: str) -> str:
    def sub(match: "re.Match[str]") -> str:
        rel = match.group(1).strip("'\"")
        if rel.startswith("data:"):
            return match.group(0)
        uri = data_uri(rel)
        return "url(%s)" % uri if uri else match.group(0)

    return re.sub(r"url\(([^)]+)\)", sub, css)


def main() -> int:
    if not SRC_INDEX.is_file():
        print("index.html 不存在", file=sys.stderr)
        return 1

    html = SRC_INDEX.read_text(encoding="utf-8")

    def css_repl(match: "re.Match[str]") -> str:
        target = ROOT / match.group(1)
        if not target.is_file():
            return match.group(0)
        return "<style>\n" + inline_css(target.read_text(encoding="utf-8")) + "\n</style>"

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
        # 在 app.js 之前注入桥接层
        if rel.endswith("app.js") and BRIDGE.is_file():
            bridge_js = BRIDGE.read_text(encoding="utf-8").replace(
                'var BASE = window.__CALC_API_BASE__ || "";',
                'var BASE = window.__CALC_API_BASE__ || "%s";' % API_BASE,
            )
            pre = '<script>window.__CALC_API_BASE__ = "%s";</script>\n<script>\n%s\n</script>\n' % (
                API_BASE,
                bridge_js,
            )
            return pre + block
        return block

    html = re.sub(r'<script[^>]*src="([^"]+\.js)"[^>]*></script>', js_repl, html)

    def img_repl(match: "re.Match[str]") -> str:
        uri = data_uri(match.group(2))
        return (match.group(1) + uri + match.group(3)) if uri else match.group(0)

    html = re.sub(r'(<img[^>]*src=")([^"]+)(")', img_repl, html)

    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_INDEX.write_text(html, encoding="utf-8")
    left = re.findall(r'(?:src|href)="(?!data:|https?:|#)([^"]+)"', html)
    print("已生成 %s（%.1f KB），接口=%s" % (OUT_INDEX, len(html) / 1024, API_BASE))
    if left:
        print("警告：仍有外链引用：%s" % ", ".join(sorted(set(left))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
