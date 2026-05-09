from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grading.types import Issue, IssueGroup


@dataclass(frozen=True)
class NlpScore:
    grammar: IssueGroup
    spelling: IssueGroup
    overall_score: int


def _match_to_issue(match: dict[str, Any]) -> Issue:
    message = match.get("shortMessage") or match.get("message") or ""
    replacements = [r.get("value", "") for r in match.get("replacements", [])[:3]]
    rule = match.get("rule", {})
    return Issue(
        message=str(message)[:100],
        offset=int(match.get("offset", 0)),
        length=int(match.get("length", 0)),
        replacements=[r for r in replacements if r],
        rule_id=str(rule.get("id", "")),
    )


def score_text(text: str, response: dict[str, Any]) -> NlpScore:
    del text
    grammar_issues: list[Issue] = []
    spelling_issues: list[Issue] = []

    for match in response.get("matches", []) or []:
        issue_type = match.get("rule", {}).get("issueType")
        if issue_type == "style":
            continue
        issue = _match_to_issue(match)
        if issue_type == "misspelling":
            spelling_issues.append(issue)
        else:
            grammar_issues.append(issue)

    grammar_score = max(0, 100 - len(grammar_issues) * 20)
    spelling_score = max(0, 100 - len(spelling_issues) * 15)
    return NlpScore(
        grammar=IssueGroup(grammar_score, grammar_issues),
        spelling=IssueGroup(spelling_score, spelling_issues),
        overall_score=round((grammar_score + spelling_score) / 2),
    )
