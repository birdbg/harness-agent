"""供 Worker 使用的最小工具集。所有文件操作均限制在项目目录内。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT_DIR = Path(__file__).resolve().parent


def _safe_path(path: str) -> Path:
    """解析相对路径，并阻止访问项目目录之外的文件。"""
    target = (ROOT_DIR / path).resolve()
    if target != ROOT_DIR and ROOT_DIR not in target.parents:
        raise ValueError("Path must stay inside the project directory")
    return target


def read_file(path: str) -> str:
    return _safe_path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}"


def run_python(code: str) -> str:
    """执行短 Python 代码。生产环境应替换为容器或沙箱。"""
    if os.getenv("ENABLE_PYTHON_TOOL", "false").lower() != "true":
        return "Python execution is disabled. Set ENABLE_PYTHON_TOOL=true to enable it."

    timeout = int(os.getenv("PYTHON_TIMEOUT_SECONDS", "10"))
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Python execution timed out after {timeout} seconds"

    output = result.stdout
    if result.stderr:
        output += f"\nSTDERR:\n{result.stderr}"
    return f"Exit code: {result.returncode}\n{output}".strip()


TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    "read_file": read_file,
    "write_file": write_file,
    "run_python": run_python,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file inside the project directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a UTF-8 text file inside the project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Run a short Python snippet and return stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    },
]


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    function = TOOL_FUNCTIONS.get(name)
    if not function:
        return f"Unknown tool: {name}"
    try:
        return function(**arguments)
    except Exception as exc:  # 将工具错误反馈给模型，而不是中断整个任务
        return f"Tool error: {type(exc).__name__}: {exc}"
