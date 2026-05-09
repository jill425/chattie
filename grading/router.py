from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

from ..config.constants import LLM_UPGRADE_THRESHOLD
from ..nlp.scorer import NlpScore

LLM_MIN_WORD_COUNT = 4
WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass(frozen=True)
class RoutingDecision:
    route: Literal["nlp-only", "nlp+llm"]
    nlp_score: NlpScore
    reason: str


def count_words(text: str) -> int:
    return len(WORD_PATTERN.findall(text))


def _has_nlp_issues(nlp_score: NlpScore) -> bool:
    return bool(nlp_score.grammar.issues or nlp_score.spelling.issues)


def route_grading(text: str, nlp_score: NlpScore) -> RoutingDecision:
    word_count = count_words(text)
    if word_count < LLM_MIN_WORD_COUNT:
        return RoutingDecision(
            "nlp-only",
            nlp_score,
            f"wordCount {word_count} < {LLM_MIN_WORD_COUNT}, text too short for LLM",
        )

    score = nlp_score.overall_score
    if isinstance(score, float) and math.isnan(score):
        return RoutingDecision("nlp+llm", nlp_score, "invalid score, defaulting to nlp+llm")

    if not _has_nlp_issues(nlp_score):
        return RoutingDecision(
            "nlp+llm",
            nlp_score,
            f"wordCount {word_count} >= {LLM_MIN_WORD_COUNT} and no NLP issues, upgrading to LLM for fluency check",
        )

    if score >= LLM_UPGRADE_THRESHOLD:
        return RoutingDecision(
            "nlp-only",
            nlp_score,
            f"overallScore {score} >= threshold {LLM_UPGRADE_THRESHOLD}, NLP sufficient",
        )

    return RoutingDecision(
        "nlp+llm",
        nlp_score,
        f"overallScore {score} < threshold {LLM_UPGRADE_THRESHOLD}, upgrading to LLM",
    )

