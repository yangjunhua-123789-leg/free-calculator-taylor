"""自由计算器 Web 端（FastAPI + SymPy）。

设计约束：
- 核心计算逻辑完全来自仓库根目录的 ``core/math_engine.py``，本文件不做任何数学逻辑改动。
- 前后端同源：静态前端挂载在 ``/``，API 在 ``/api/solve``。
- 公开 API（无 Cookie），因此 CORS 使用 ``allow_credentials=False``。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# 仓库根目录（含 core/ 包）：web_version/main.py -> 上两级
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.math_engine import MathEngine  # noqa: E402  （路径就绪后再导入）

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="自由计算器 Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 公开 API，无 Cookie；与 allow_origins=["*"] 不冲突
    allow_methods=["*"],
    allow_headers=["*"],
)

# 单例引擎：内部自带线程池、超时与冷却，保持与桌面端一致
_engine = MathEngine()


class SolveRequest(BaseModel):
    """与桌面端 ``pywebview.api.solve_limit(expression, center, order, direction)`` 对齐。"""

    expression: str = Field(..., description="关于 x 的表达式")
    center: str | None = Field(default=None, description="趋近点，默认 0")
    max_order: str | int | None = Field(default=None, description="最大展开阶数")
    order: str | int | None = Field(default=None, description="与 max_order 等价的别名")
    direction: str | None = Field(default=None, description="auto / left / right")


def _jsonable(value: Any) -> Any:
    """把结果里的非 JSON 类型（SymPy 对象等）安全降级为字符串。"""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        import json

        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Render 冷启动预热：先打这个接口，避免首个用户请求承担 SymPy 加载时间。"""
    return {"status": "ok"}


@app.post("/api/solve")
def solve(payload: SolveRequest) -> JSONResponse:
    order = payload.max_order if payload.max_order is not None else payload.order
    result = _engine.solve_limit(
        payload.expression,
        payload.center,
        order,
        payload.direction,
    )
    return JSONResponse(content=_jsonable(result))


# 必须在所有 API 路由之后挂载，否则会吞掉 /api/*
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
