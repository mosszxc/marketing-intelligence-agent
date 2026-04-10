"""Tests for the evaluation pipeline."""

import pytest

from src.evaluation.evaluator import (
    batch_evaluate,
    evaluate_single,
    load_eval_questions,
    score_contains,
    score_facts,
    score_routing,
)


class TestScoring:
    def test_routing_exact_match(self):
        assert score_routing(["analytics"], ["analytics"]) == 1.0
        assert score_routing(["research"], ["research"]) == 1.0
        assert score_routing(["analytics", "research"], ["analytics", "research"]) == 1.0

    def test_routing_partial_match(self):
        assert score_routing(["analytics", "research"], ["analytics"]) == 0.5
        assert score_routing(["analytics"], ["analytics", "research"]) == 0.5

    def test_routing_no_match(self):
        assert score_routing(["analytics"], ["research"]) == 0.0

    def test_contains_all_found(self):
        assert score_contains(["ROI", "channel"], "ROI by channel: 200%") == 1.0

    def test_contains_partial(self):
        assert score_contains(["ROI", "CPA", "CTR"], "ROI is 200%") == pytest.approx(1 / 3)

    def test_contains_empty_expected(self):
        assert score_contains([], "anything") == 1.0

    def test_contains_case_insensitive(self):
        assert score_contains(["roi"], "ROI is 200%") == 1.0

    def test_facts_empty(self):
        assert score_facts({}, {}) == 1.0

    def test_facts_channel_check(self):
        result = {"final_answer": "email has the best ROI", "agent_outputs": {}}
        assert score_facts({"best_roi_channel": "email"}, result) == 1.0

    def test_facts_missing(self):
        result = {"final_answer": "no data", "agent_outputs": {}}
        assert score_facts({"best_roi_channel": "email"}, result) == 0.0


class TestEvalSingle:
    def test_perfect_analytics(self):
        question = {
            "id": "test",
            "query": "ROI",
            "expected_agents": ["analytics"],
            "expected_contains": ["ROI"],
            "expected_facts": {},
        }
        result = {
            "plan": ["analytics"],
            "final_answer": "ROI by channel: google_ads 216%, meta_ads 202%, email 2881%, seo 1775%",
            "agent_outputs": {},
        }
        score = evaluate_single(question, result)
        assert score["routing"] == 1.0
        assert score["contains"] == 1.0
        assert score["facts"] == 1.0
        assert score["completeness"] == 1.0


class TestEvalDataset:
    def test_load_questions(self):
        questions = load_eval_questions()
        assert len(questions) >= 10
        for q in questions:
            assert "id" in q
            assert "query" in q
            assert "expected_agents" in q

    def test_batch_evaluate_baseline(self):
        """Full eval run — baseline metrics must meet thresholds."""
        output = batch_evaluate(save_results=False)
        s = output["summary"]

        assert s["avg_routing"] >= 0.9, f"Routing {s['avg_routing']} < 0.9"
        assert s["avg_contains"] >= 0.9, f"Contains {s['avg_contains']} < 0.9"
        assert s["avg_facts"] >= 0.8, f"Facts {s['avg_facts']} < 0.8"
        assert s["avg_completeness"] >= 0.9, f"Completeness {s['avg_completeness']} < 0.9"
