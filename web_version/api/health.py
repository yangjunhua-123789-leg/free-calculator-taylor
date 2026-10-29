"""Vercel 健康检查 / 预热入口。"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
