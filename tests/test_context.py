from __future__ import annotations

import tempfile
import unittest
import sys
import types
from pathlib import Path
from unittest.mock import patch

import context

# These unit tests inspect agent message construction and do not need the OpenAI stack.
fake_llm_module = types.ModuleType("llm")
fake_llm_module.LLMClient = object
sys.modules.setdefault("llm", fake_llm_module)

from agents import Planner, Reviewer, Worker
import graph


class FakeLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = []

    def chat(self, messages, use_tools=False):
        self.calls.append((messages, use_tools))
        return self.response


class ContextPackTests(unittest.TestCase):
    def test_load_skips_missing_files_and_metadata_lists_loaded_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "project_profile.md").write_text("Profile", encoding="utf-8")
            (root / "examples").mkdir()
            (root / "examples/report_example.md").write_text("Example", encoding="utf-8")
            with patch.object(context, "KNOWLEDGE_DIR", root):
                pack = context.load_context_pack()

        self.assertEqual(
            pack,
            {"project_profile.md": "Profile", "examples/report_example.md": "Example"},
        )
        self.assertEqual(
            context.get_context_metadata(pack),
            {
                "context_used": True,
                "context_files": ["project_profile.md", "examples/report_example.md"],
            },
        )

    def test_build_prompt_is_empty_without_files_and_has_clear_sections(self):
        self.assertEqual(context.build_context_prompt({}), "")
        prompt = context.build_context_prompt(
            {"business_rules.md": "Do the safe thing.", "terminology.md": "Harness: runner"}
        )
        self.assertIn("## 业务规则（Business Rules）", prompt)
        self.assertIn("\n\n---\n\n", prompt)
        self.assertLess(prompt.index("Business Rules"), prompt.index("Terminology"))

    def test_all_agents_place_context_before_current_task(self):
        planner_llm = FakeLLM(
            '{"steps":[{"id":"step_1","description":"Do it","expected_output":"Done"}]}'
        )
        Planner(planner_llm).run("USER TASK", context_prompt="PACK CONTENT")

        worker_llm = FakeLLM("worker result")
        Worker(worker_llm).run(
            "USER TASK", {"id": "step_1", "description": "Do it"}, [], context_prompt="PACK CONTENT"
        )

        reviewer_llm = FakeLLM(
            '{"approved":true,"feedback":"","failed_step_ids":[],"final_answer":"done"}'
        )
        Reviewer(reviewer_llm).run("USER TASK", [], [], context_prompt="PACK CONTENT")

        for fake_llm in (planner_llm, worker_llm, reviewer_llm):
            user_message = fake_llm.calls[0][0][1]["content"]
            self.assertLess(user_message.index("PACK CONTENT"), user_message.index("USER TASK"))
            self.assertIn("user's current task takes precedence", user_message)

        self.assertTrue(worker_llm.calls[0][1])

    def test_graph_passes_context_through_rework_and_writes_metadata(self):
        class FakePlanner:
            def __init__(self):
                self.contexts = []

            def run(self, task, context_prompt=""):
                self.contexts.append(context_prompt)
                return [{"id": "step_1", "description": "Do it", "expected_output": "Done"}]

        class FakeWorker:
            def __init__(self):
                self.contexts = []

            def run(self, task, step, results, review_feedback=None, context_prompt=""):
                self.contexts.append(context_prompt)
                return "result"

        class FakeReviewer:
            def __init__(self):
                self.contexts = []

            def run(self, task, plan, results, context_prompt=""):
                self.contexts.append(context_prompt)
                approved = len(self.contexts) > 1
                return {
                    "approved": approved,
                    "feedback": "retry" if not approved else "",
                    "failed_step_ids": ["step_1"] if not approved else [],
                    "final_answer": "done",
                }

        harness = graph.HarnessGraph.__new__(graph.HarnessGraph)
        harness.planner = FakePlanner()
        harness.worker = FakeWorker()
        harness.reviewer = FakeReviewer()
        pack = {"project_profile.md": "Profile"}

        with tempfile.TemporaryDirectory() as directory, patch.object(
            graph, "OUTPUT_DIR", Path(directory)
        ), patch.object(graph, "load_context_pack", return_value=pack):
            result = harness.run("task-id", "USER TASK")

        self.assertTrue(result["context_used"])
        self.assertEqual(result["context_files"], ["project_profile.md"])
        self.assertEqual(len(harness.worker.contexts), 2)
        self.assertTrue(all("Profile" in value for value in harness.worker.contexts))
        self.assertTrue(all("Profile" in value for value in harness.reviewer.contexts))


if __name__ == "__main__":
    unittest.main()
