"""OpenAI 格式的大模型调用封装。"""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_SCHEMAS, call_tool

load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    def chat(self, messages: list[dict[str, Any]], use_tools: bool = False) -> str:
        """调用模型；Worker 可在最多 5 轮内调用本地工具。"""
        history = list(messages)
        for _ in range(5):
            kwargs: dict[str, Any] = {"model": self.model, "messages": history}
            if use_tools:
                kwargs["tools"] = TOOL_SCHEMAS
                kwargs["tool_choice"] = "auto"

            message = self.client.chat.completions.create(**kwargs).choices[0].message
            if not message.tool_calls:
                return message.content or ""

            history.append(message.model_dump(exclude_none=True))
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": call_tool(tool_call.function.name, arguments),
                    }
                )
        return "Tool-call limit reached before a final answer was produced."
