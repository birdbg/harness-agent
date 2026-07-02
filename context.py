"""Context Pack knowledge loading and prompt construction."""

from __future__ import annotations

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

CONTEXT_SECTIONS = (
    ("project_profile.md", "项目背景（Project Profile）"),
    ("business_rules.md", "业务规则（Business Rules）"),
    ("terminology.md", "术语表（Terminology）"),
    ("output_style.md", "输出风格（Output Style）"),
    ("user_preferences.md", "用户偏好（User Preferences）"),
    ("examples/report_example.md", "报告样例（Report Example）"),
    ("examples/excel_example.md", "Excel 样例（Excel Example）"),
    ("examples/html_example.md", "HTML 样例（HTML Example）"),
)


def load_context_pack() -> dict[str, str]:
    """Load existing Markdown knowledge files; missing files are ignored."""
    context_pack: dict[str, str] = {}
    for relative_path, _ in CONTEXT_SECTIONS:
        path = KNOWLEDGE_DIR / relative_path
        if path.is_file():
            context_pack[relative_path] = path.read_text(encoding="utf-8")
    return context_pack


def build_context_prompt(context_pack: dict[str, str]) -> str:
    """Build a deterministic, clearly separated prompt from a Context Pack."""
    sections = []
    for filename, title in CONTEXT_SECTIONS:
        if filename in context_pack:
            sections.append(f"## {title}\n\n{context_pack[filename].strip()}")
    if not sections:
        return ""
    return "# Context Pack\n\n" + "\n\n---\n\n".join(sections)


def get_context_metadata(context_pack: dict[str, str]) -> dict[str, object]:
    """Return serializable Context Pack usage metadata."""
    return {
        "context_used": bool(context_pack),
        "context_files": list(context_pack.keys()),
    }
