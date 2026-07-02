"""普通 Python 编排流程，后续可平滑替换为 LangGraph。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import Planner, Reviewer, Worker
from llm import LLMClient

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


class HarnessGraph:
    def __init__(self) -> None:
        llm = LLMClient()
        self.planner = Planner(llm)
        self.worker = Worker(llm)
        self.reviewer = Reviewer(llm)

    def run(self, task_id: str, task: str) -> dict[str, Any]:
        plan = self.planner.run(task)
        worker_results: list[str] = []
        for step in plan:
            worker_results.append(self.worker.run(task, step, worker_results))

        review = self.reviewer.run(task, plan, worker_results)
        result = {
            "task_id": task_id,
            "task": task,
            "plan": plan,
            "worker_results": worker_results,
            "review": review,
            "final_answer": review["final_answer"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / f"{task_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
