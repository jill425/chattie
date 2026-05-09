from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class Issue:
    message: str
    offset: int
    length: int
    replacements: list[str]
    rule_id: str
    description: str | None = None


@dataclass(frozen=True)
class IssueGroup:
    score: int
    issues: list[Issue]


@dataclass(frozen=True)
class LlmUsage:
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class GradingResult:
    original_text: str
    overall_score: int
    source: Literal["nlp-only", "nlp+llm"]
    grammar: IssueGroup
    spelling: IssueGroup
    suggestion: str | None
    tips: str | None
    llm_usage: LlmUsage | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["originalText"] = data.pop("original_text")
        data["overallScore"] = data.pop("overall_score")
        llm_usage = data.pop("llm_usage")
        if llm_usage is not None:
            data["llmUsage"] = {
                "model": llm_usage["model"],
                "inputTokens": llm_usage["input_tokens"],
                "outputTokens": llm_usage["output_tokens"],
                "totalTokens": llm_usage["total_tokens"],
            }
        for group_name in ("grammar", "spelling"):
            for issue in data[group_name]["issues"]:
                issue["ruleId"] = issue.pop("rule_id")
        return data
