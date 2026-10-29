# 自由计算器 Web 端部署指南（Render）

Web 端是桌面版的同源改造：核心数学逻辑（SymPy 升阶、白名单、超时防护）原样复用 `core/math_engine.py`，本分支**未改动任何计算代码**。

## 目录结构

```
web_version/
├── main.py            # FastAPI：/health、/api/solve、静态前端挂载
├── requirements.txt   # fastapi / uvicorn / sympy / gunicorn
├── start.sh           # gunicorn + UvicornWorker，exec 接管进程
├── render.yaml        # Render Blueprint
├── README_deploy.md   # 本文件
└── static/            # 前端（index.html + assets/，含 web-bridge.js）
```

`main.py` 通过 `Path(__file__).parent.parent` 定位仓库根目录来 `from core.math_engine import MathEngine`，因此仓库里必须保留 `core/`。

## 部署步骤

1. 确认 `web_version/` 下包含：`main.py`、`requirements.txt`、`start.sh`、`render.yaml`、`static/`。
2. 赋予启动脚本执行权限：
   ```bash
   chmod +x web_version/start.sh
   ```
   （Windows 上可忽略；Render 用 `bash start.sh` 启动，不依赖该权限位。）
3. 提交并推送到 GitHub：
   ```bash
   git add .
   git commit -m "feat(web): FastAPI + SymPy web version for Render"
   git push -u origin web_version
   ```
4. 打开 Render 控制台 → New → Web Service → 绑定该仓库与 `web_version` 分支。
5. 若仓库根目录不是 `web_version/`，在 Render 服务的 **Root Directory** 填 `web_version`。
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`bash start.sh`
   - 或者在 Render 里直接选 Blueprint（`render.yaml`）自动创建。
6. 部署完成后，先访问 `/health` 预热（返回 `{"status":"ok"}`），再访问根路径 `/` 使用界面。
   - 免费实例休眠后首次唤醒较慢，`/health` 只用于提前拉起进程；首个 `/api/solve` 仍可能多等几秒。

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 预热 / 健康检查 |
| POST | `/api/solve` | 入参 `{expression, center, max_order, direction}`，返回与桌面端一致的结果字典 |
| GET | `/` | 静态前端（`static/index.html`） |

## 安全提醒

- 服务部署在公网，任何人都能调用 `/api/solve`。原有的**字符白名单**、**函数/标识符白名单**、**5 秒超时 + 冷却**都在 `core/math_engine.py` 里生效，请勿为了"方便调试"放宽它们。
- 公开 API 未使用 Cookie，因此 CORS 配置为 `allow_credentials=False`；不要改成 `True`，否则浏览器的 `*` 通配会失效。
- 如需进一步限流，可在 Render 前面加 Cloudflare，或在 `main.py` 里加简单的 IP 速率限制（不影响计算逻辑）。
- 免费实例内存有限，避免用超大表达式压测；超时保护会兜底，但反复触发会进入冷却。
