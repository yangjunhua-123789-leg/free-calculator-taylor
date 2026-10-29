"""Vercel 无服务器入口（ASGI）。

只做 HTTP 适配：计算逻辑全部来自 `core/math_engine.py`，本文件不改动任何数学逻辑。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from core.math_engine import MathEngine  # noqa: E402

app = FastAPI(title="自由计算器 Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = MathEngine()


class SolveRequest(BaseModel):
    expression: str
    center: str | None = None
    max_order: str | int | None = None
    order: str | int | None = None
    direction: str | None = None


def _jsonable(value: Any) -> Any:
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
@app.get("/api/solve/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/")
@app.post("/api/solve")
@app.post("/api/solve/")
def solve(payload: SolveRequest) -> JSONResponse:
    order = payload.max_order if payload.max_order is not None else payload.order
    result = _engine.solve_limit(
        payload.expression,
        payload.center,
        order,
        payload.direction,
    )
    return JSONResponse(content=_jsonable(result))
