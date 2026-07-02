"""Planner、Worker、Reviewer 的轻量实现。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from llm import LLMClient

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def _parse_json(text: str) -> Any:
    """兼容模型偶尔返回 Markdown JSON 代码块的情况。"""
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


class Planner:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.prompt = _load_prompt("planner")

    def run(self, task: str) -> list[dict[str, str]]:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": task},
        ]
        for attempt in range(2):
            response = self.llm.chat(messages)
            try:
                data = _parse_json(response)
                steps = data["steps"]
                if not isinstance(steps, list) or not steps:
                    raise ValueError("steps must be a non-empty list")
                normalized = []
                for index, step in enumerate(steps, 1):
                    if not isinstance(step, dict) or not step.get("description"):
                        raise ValueError("each step must be an object with description")
                    normalized.append(
                        {
                            "id": str(step.get("id") or f"step_{index}"),
                            "description": str(step["description"]),
                            "expected_output": str(step.get("expected_output") or "Completed step result"),
                        }
                    )
                return normalized
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                if attempt == 0:
                    messages.extend(
                        [
                            {"role": "assistant", "content": response},
                            {
                                "role": "user",
                                "content": f"Invalid planner JSON ({exc}). Return only the required JSON object.",
                            },
                        ]
                    )
        raise ValueError("Planner failed to return valid structured JSON after 2 attempts")


class Worker:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.prompt = _load_prompt("worker")

    def run(
        self,
        task: str,
        step: dict[str, str],
        previous_results: list[dict[str, Any]],
        review_feedback: str | None = None,
    ) -> str:
        context = json.dumps(previous_results, ensure_ascii=False, indent=2)
        return self.llm.chat(
            [
                {"role": "system", "content": self.prompt},
                {
                    "role": "user",
                    "content": (
                        f"Original task:\n{task}\n\nCurrent step:\n"
                        f"{json.dumps(step, ensure_ascii=False, indent=2)}\n\n"
                        f"Previous results:\n{context}\n\n"
                        f"Reviewer feedback:\n{review_feedback or 'None (first attempt)'}"
                    ),
                },
            ],
            use_tools=True,
        )


class Reviewer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.prompt = _load_prompt("reviewer")

    def run(
        self, task: str, plan: list[dict[str, str]], results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        payload = json.dumps(
            {"task": task, "plan": plan, "worker_results": results},
            ensure_ascii=False,
            indent=2,
        )
        response = self.llm.chat(
            [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": payload},
            ]
        )
        try:
            reviewed = _parse_json(response)
            if (
                isinstance(reviewed, dict)
                and isinstance(reviewed.get("approved"), bool)
                and "final_answer" in reviewed
            ):
                reviewed.setdefault("feedback", "")
                reviewed.setdefault("failed_step_ids", [])
                return reviewed
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "approved": False,
            "feedback": "Reviewer returned invalid structured JSON",
            "failed_step_ids": [],
            "final_answer": response,
        }
