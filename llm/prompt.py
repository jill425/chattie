from __future__ import annotations

from dataclasses import dataclass

from ..grading.types import Issue
from ..nlp.scorer import NlpScore


@dataclass(frozen=True)
class LlmPrompt:
    system: str
    user_message: str


SYSTEM = (
    "You are an expert Australian English grammar teacher reviewing a student's English text.\n"
    "You will receive the text along with pre-detected grammar and spelling issues.\n"
    "Use Australian English spelling, grammar, and phrasing in all corrections.\n"
    "Also check whether the sentence is semantically plausible and natural in context.\n"
    "The input may come from speech-to-text, so spelling may be correct while words may be wrong or unnatural in context.\n"
    "If the sentence is grammatical but logically odd, unnatural, or likely affected by speech-to-text misrecognition, suggest the most natural correction and explain the likely issue.\n"
    "If the intended meaning is unclear, avoid guessing too strongly; mention the uncertainty in the tips.\n"
    "Provide helpful, encouraging feedback.\n\n"
    "Respond ONLY with a JSON object in this exact format, with no other text before or after:\n"
    "{\"suggestion\":\"<the fully corrected version of the student's text>\",\"tips\":\"<one paragraph in English explaining the main errors and how to avoid them>\"}"
)


def _format_issue(issue: Issue, text: str) -> str:
    fragment = text[issue.offset : issue.offset + issue.length]
    base = f'- [{issue.rule_id}] {issue.message}: "{fragment}" (offset {issue.offset})'
    if not issue.replacements:
        return base
    suggestions = ", ".join(f'"{r}"' for r in issue.replacements[:2])
    return f"{base} -> suggested: {suggestions}"


def _format_issues(issues: list[Issue], text: str, limit: int = 5) -> str:
    if not issues:
        return "(none)"
    lines = [_format_issue(issue, text) for issue in issues[:limit]]
    if len(issues) > limit:
        lines.append(f"... and {len(issues) - limit} more")
    return "\n".join(lines)


def build_prompt(text: str, nlp_score: NlpScore) -> LlmPrompt:
    grammar_issues = nlp_score.grammar.issues
    spelling_issues = nlp_score.spelling.issues
    user_message = "\n".join(
        [
            f'Text: "{text}"',
            "",
            f"Grammar issues ({len(grammar_issues)}):",
            _format_issues(grammar_issues, text),
            "",
            f"Spelling issues ({len(spelling_issues)}):",
            _format_issues(spelling_issues, text),
            "",
            f"Overall score: {nlp_score.overall_score}/100 (grammar: {nlp_score.grammar.score}, spelling: {nlp_score.spelling.score})",
            "",
            "Please provide your feedback in the specified JSON format.",
        ]
    )
    return LlmPrompt(system=SYSTEM, user_message=user_message)
