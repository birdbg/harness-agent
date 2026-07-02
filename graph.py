"""普通 Python 编排流程，后续可平滑替换为 LangGraph。"""

from __future__ import annotations

import json
import os
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
        worker_results: list[dict[str, Any]] = []
        for step in plan:
            worker_results.append(
                {
                    "step_id": step["id"],
                    "attempt": 1,
                    "result": self.worker.run(task, step, worker_results),
                }
            )

        review = self.reviewer.run(task, plan, worker_results)
        review_history = [review]
        max_rework_rounds = max(0, int(os.getenv("MAX_REWORK_ROUNDS", "2")))
        for round_number in range(1, max_rework_rounds + 1):
            if review["approved"]:
                break
            failed_ids = set(review.get("failed_step_ids") or [])
            steps_to_rework = [step for step in plan if not failed_ids or step["id"] in failed_ids]
            for step in steps_to_rework:
                previous_attempts = [r for r in worker_results if r["step_id"] == step["id"]]
                worker_results.append(
                    {
                        "step_id": step["id"],
                        "attempt": len(previous_attempts) + 1,
                        "result": self.worker.run(
                            task, step, worker_results, str(review.get("feedback", ""))
                        ),
                    }
                )
            review = self.reviewer.run(task, plan, worker_results)
            review_history.append(review)

        result = {
            "task_id": task_id,
            "task": task,
            "plan": plan,
            "worker_results": worker_results,
            "review": review,
            "review_history": review_history,
            "rework_rounds": len(review_history) - 1,
            "final_answer": review["final_answer"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / f"{task_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
