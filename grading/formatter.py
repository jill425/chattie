from __future__ import annotations

from grading.types import GradingResult, Issue

ISSUE_LIMIT = 3


def _format_issue(issue: Issue) -> str:
    replacements = ""
    if issue.replacements:
        replacements = f"；建議 {'、'.join(issue.replacements[:2])}"
    message = issue.message or issue.description or "未知問題"
    return f"- {message}{replacements}"


def _format_issue_block(title: str, issues: list[Issue]) -> str | None:
    if not issues:
        return None
    lines = [f"{title}（{len(issues)} 個）"]
    lines.extend(_format_issue(issue) for issue in issues[:ISSUE_LIMIT])
    if len(issues) > ISSUE_LIMIT:
        lines.append(f"（另有 {len(issues) - ISSUE_LIMIT} 個問題）")
    return "\n".join(lines)


def format_reply(result: GradingResult) -> str:
    blocks = [f"原文：{result.original_text}"]
    grammar_block = _format_issue_block("文法", result.grammar.issues)
    spelling_block = _format_issue_block("拼字", result.spelling.issues)

    if grammar_block is not None:
        blocks.append(grammar_block)
    if spelling_block is not None:
        blocks.append(spelling_block)
    if grammar_block is None and spelling_block is None:
        blocks.append("文法和拼字未發現明顯問題。")
    if result.source == "nlp+llm" and result.suggestion:
        blocks.append(f"建議：{result.suggestion}")
    if result.source == "nlp+llm" and result.tips:
        blocks.append(f"提示：{result.tips}")
    return "\n\n".join(blocks)
