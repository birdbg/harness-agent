"""FastAPI 入口。"""

from __future__ import annotations

import os
import json
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph import HarnessGraph

load_dotenv()

app = FastAPI(title="Minimal Multi-Agent Harness", version="0.3.0")
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20_000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tasks")
def submit_task(request: TaskRequest) -> dict:
    """同步执行最小流程；长任务在企业版中应改为异步队列。"""
    task_id = uuid4().hex
    try:
        return HarnessGraph().run(task_id, request.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    # UUID hex 白名单也避免路径穿越。
    if len(task_id) != 32 or any(char not in "0123456789abcdef" for char in task_id):
        raise HTTPException(status_code=400, detail="Invalid task id")
    path = OUTPUT_DIR / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")))
