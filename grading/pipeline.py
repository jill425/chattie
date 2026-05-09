from __future__ import annotations

from llm.client import call_llm
from llm.parser import parse_response
from llm.prompt import build_prompt
from nlp.client import check_grammar
from nlp.scorer import NlpScore, score_text
from utils.logger import logger
from .router import route_grading
from .types import GradingResult, LlmUsage


def _to_nlp_only_result(text: str, nlp_score: NlpScore) -> GradingResult:
    return GradingResult(
        original_text=text,
        overall_score=nlp_score.overall_score,
        source="nlp-only",
        grammar=nlp_score.grammar,
        spelling=nlp_score.spelling,
        suggestion=None,
        tips=None,
    )


def run_grading_pipeline(text: str) -> GradingResult:
    response = check_grammar(text)
    nlp_score = score_text(text, response)
    decision = route_grading(text, nlp_score)

    if decision.route == "nlp-only":
        return _to_nlp_only_result(text, nlp_score)

    try:
        prompt = build_prompt(text, nlp_score)
        llm_response = call_llm(prompt)
        total_tokens = llm_response.input_tokens + llm_response.output_tokens
        llm_usage = LlmUsage(
            model=llm_response.model,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            total_tokens=total_tokens,
        )
        logger.info(
            "LLM usage: model=%s input_tokens=%s output_tokens=%s total_tokens=%s",
            llm_usage.model,
            llm_usage.input_tokens,
            llm_usage.output_tokens,
            llm_usage.total_tokens,
        )
        parsed = parse_response(llm_response.content)
        return GradingResult(
            original_text=text,
            overall_score=nlp_score.overall_score,
            source="nlp+llm",
            grammar=nlp_score.grammar,
            spelling=nlp_score.spelling,
            suggestion=parsed.suggestion,
            tips=parsed.tips,
            llm_usage=llm_usage,
        )
    except Exception as exc:
        logger.warning("LLM downgrade: %s", exc)
        return _to_nlp_only_result(text, nlp_score)
