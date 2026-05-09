import json
import unittest

from api.grading_api import grade_text_payload
from grading.formatter import format_reply
from grading.router import route_grading
from grading.types import GradingResult, Issue, IssueGroup
from line.message_filter import should_grade_message
from line.signature_guard import is_valid_line_signature
from llm.parser import parse_response
from llm.prompt import build_prompt
from nlp.scorer import score_text


def sample_result(text="I go to school yesterday."):
    issue = Issue("Possible tense issue", 2, 2, ["went"], "PAST_TENSE")
    return GradingResult(
        original_text=text,
        overall_score=92,
        source="nlp+llm",
        grammar=IssueGroup(85, [issue]),
        spelling=IssueGroup(100, []),
        suggestion="I went to school yesterday.",
        tips="Use past tense for past time expressions.",
    )


class CoreLogicTest(unittest.TestCase):
    def test_score_text_splits_grammar_and_spelling(self):
        response = {
            "matches": [
                {
                    "shortMessage": "Grammar",
                    "message": "Grammar problem",
                    "offset": 0,
                    "length": 1,
                    "replacements": [{"value": "A"}],
                    "rule": {"id": "G1", "issueType": "grammar"},
                },
                {
                    "shortMessage": "Spelling",
                    "message": "Spelling problem",
                    "offset": 2,
                    "length": 1,
                    "replacements": [{"value": "B"}],
                    "rule": {"id": "S1", "issueType": "misspelling"},
                },
                {
                    "shortMessage": "Style",
                    "message": "Style problem",
                    "offset": 4,
                    "length": 1,
                    "replacements": [],
                    "rule": {"id": "ST1", "issueType": "style"},
                },
            ]
        }
        score = score_text("x", response)
        self.assertEqual(score.grammar.score, 80)
        self.assertEqual(score.spelling.score, 85)
        self.assertEqual(score.overall_score, 82)
        self.assertEqual(len(score.grammar.issues), 1)
        self.assertEqual(len(score.spelling.issues), 1)

    def test_route_grading_matches_current_threshold_rules(self):
        no_issue = score_text("this sentence has no issue", {"matches": []})
        self.assertEqual(route_grading("This sentence has no issue", no_issue).route, "nlp+llm")

        short = score_text("hi there", {"matches": []})
        self.assertEqual(route_grading("Hi there", short).route, "nlp-only")

        many_issues = score_text(
            "This sentence has many grammar problems",
            {
                "matches": [
                    {"shortMessage": "x", "offset": 0, "length": 1, "replacements": [], "rule": {"id": str(i), "issueType": "grammar"}}
                    for i in range(5)
                ]
            },
        )
        self.assertEqual(route_grading("This sentence has many grammar problems", many_issues).route, "nlp+llm")

    def test_message_filter_direct_and_group_behavior(self):
        direct = {
            "type": "message",
            "message": {"type": "text", "text": "I go to school yesterday."},
            "source": {"type": "user"},
        }
        self.assertEqual(should_grade_message(direct).action, "grade")

        group_without_command = {
            "type": "message",
            "message": {"type": "text", "text": "I go to school yesterday."},
            "source": {"type": "group"},
        }
        self.assertEqual(should_grade_message(group_without_command).reason, "missing-group-trigger")

        group_with_command = {
            "type": "message",
            "message": {"type": "text", "text": "/check I go to school yesterday."},
            "source": {"type": "group"},
        }
        self.assertEqual(should_grade_message(group_with_command).text, "I go to school yesterday.")

    def test_llm_parser_accepts_embedded_json(self):
        parsed = parse_response('prefix {"suggestion":"Good day","tips":"Use a noun."} suffix')
        self.assertEqual(parsed.suggestion, "Good day")
        self.assertEqual(parsed.tips, "Use a noun.")

    def test_prompt_uses_australian_english_and_issues(self):
        result = sample_result()
        prompt = build_prompt(
            result.original_text,
            score_text(
                result.original_text,
                {
                    "matches": [
                        {
                            "shortMessage": "Tense",
                            "message": "Tense problem",
                            "offset": 2,
                            "length": 2,
                            "replacements": [{"value": "went"}],
                            "rule": {"id": "PAST_TENSE", "issueType": "grammar"},
                        }
                    ]
                },
            ),
        )
        self.assertIn("Australian English", prompt.system)
        self.assertIn("speech-to-text", prompt.system)
        self.assertIn("semantically plausible", prompt.system)
        self.assertIn("PAST_TENSE", prompt.user_message)
        self.assertIn('"go"', prompt.user_message)

    def test_formatter_includes_issues_suggestion_and_tips(self):
        text = format_reply(sample_result())
        self.assertNotIn("分數", text)
        self.assertIn("文法", text)
        self.assertIn("I went to school yesterday.", text)
        self.assertIn("Use past tense", text)

    def test_grade_text_payload_validation_and_success(self):
        status, body = grade_text_payload({"text": "  "}, sample_result)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "invalid_text")

        status, body = grade_text_payload({"text": "你好"}, sample_result)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["message"], "only English text is supported")

        status, body = grade_text_payload({"text": "I go to school yesterday."}, sample_result)
        self.assertEqual(status, 200)
        self.assertEqual(body["originalText"], "I go to school yesterday.")
        self.assertEqual(body["grammar"]["issues"][0]["ruleId"], "PAST_TENSE")

    def test_line_signature_validation(self):
        body = json.dumps({"events": []}).encode()
        self.assertFalse(is_valid_line_signature(body, None, "secret"))


if __name__ == "__main__":
    unittest.main()
