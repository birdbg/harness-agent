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

    def run(self, task: str) -> list[str]:
        response = self.llm.chat(
            [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": task},
            ]
        )
        try:
            data = _parse_json(response)
            steps = data["steps"] if isinstance(data, dict) else data
            if isinstance(steps, list) and steps:
                return [str(step) for step in steps]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        return [response or task]


class Worker:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.prompt = _load_prompt("worker")

    def run(self, task: str, step: str, previous_results: list[str]) -> str:
        context = json.dumps(previous_results, ensure_ascii=False, indent=2)
        return self.llm.chat(
            [
                {"role": "system", "content": self.prompt},
                {
                    "role": "user",
                    "content": (
                        f"Original task:\n{task}\n\nCurrent step:\n{step}\n\n"
                        f"Previous results:\n{context}"
                    ),
                },
            ],
            use_tools=True,
        )


class Reviewer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.prompt = _load_prompt("reviewer")

    def run(self, task: str, plan: list[str], results: list[str]) -> dict[str, Any]:
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
            if isinstance(reviewed, dict) and "final_answer" in reviewed:
                return reviewed
        except (json.JSONDecodeError, TypeError):
            pass
        return {"approved": True, "feedback": "Unstructured review", "final_answer": response}
