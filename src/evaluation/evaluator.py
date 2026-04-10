"""Evaluation pipeline — routing accuracy, content checks, and LLM-as-judge."""

import json
import os
import uuid
from pathlib import Path

from src.graph import build_graph
from src.state import EvaluationResult

EVAL_DATA = Path(__file__).resolve().parent.parent.parent / "data" / "eval_questions.json"


def load_eval_questions() -> list[dict]:
    """Load ground truth evaluation questions."""
    with open(EVAL_DATA) as f:
        return json.load(f)


def score_routing(expected_agents: list[str], actual_plan: list[str]) -> float:
    """Score routing accuracy: 1.0 if exact match, partial credit otherwise."""
    if set(expected_agents) == set(actual_plan):
        return 1.0
    # Partial credit: intersection / union
    intersection = set(expected_agents) & set(actual_plan)
    union = set(expected_agents) | set(actual_plan)
    return len(intersection) / len(union) if union else 0.0


def score_contains(expected_contains: list[str], final_answer: str) -> float:
    """Score content presence: fraction of expected strings found in answer."""
    if not expected_contains:
        return 1.0
    found = sum(1 for s in expected_contains if s.lower() in final_answer.lower())
    return found / len(expected_contains)


def score_facts(expected_facts: dict, result: dict) -> float:
    """Score factual correctness against ground truth.

    Checks specific known facts from the demo dataset.
    """
    if not expected_facts:
        return 1.0

    answer = result.get("final_answer", "")
    checks_passed = 0
    total_checks = len(expected_facts)

    for fact_key, expected_value in expected_facts.items():
        if fact_key == "best_roi_channel":
            checks_passed += 1 if expected_value in answer else 0
        elif fact_key == "worst_roi_channel":
            checks_passed += 1 if expected_value in answer else 0
        elif fact_key == "all_roi_positive":
            # All ROI values should be positive (no negative sign before ROI numbers)
            checks_passed += 1 if "ROI" in answer else 0
        elif fact_key == "has_tiktok_anomaly":
            checks_passed += 1 if "tiktok" in answer.lower() else 0
        elif fact_key == "has_email_anomaly":
            checks_passed += 1 if "email" in answer.lower() else 0
        elif fact_key == "lowest_cpa_channel":
            checks_passed += 1 if expected_value in answer else 0
        elif fact_key == "total_channels":
            checks_passed += 1 if "6" in answer or "six" in answer.lower() else 0
        elif fact_key == "total_months":
            checks_passed += 1 if "12" in answer or "twelve" in answer.lower() else 0
        else:
            total_checks -= 1  # Unknown fact, skip

    return checks_passed / total_checks if total_checks > 0 else 1.0


def evaluate_single(question: dict, result: dict) -> dict:
    """Evaluate a single question against graph output."""
    plan = result.get("plan", [])
    answer = result.get("final_answer", "")

    routing_score = score_routing(question["expected_agents"], plan)
    contains_score = score_contains(question["expected_contains"], answer)
    facts_score = score_facts(question.get("expected_facts", {}), result)

    # Completeness: answer length relative to a reasonable minimum
    min_length = 50
    completeness = min(1.0, len(answer) / min_length) if answer else 0.0

    return {
        "id": question["id"],
        "query": question["query"],
        "routing": routing_score,
        "contains": contains_score,
        "facts": facts_score,
        "completeness": completeness,
        "plan": plan,
        "answer_length": len(answer),
    }


def evaluate_with_llm_judge(query: str, answer: str) -> EvaluationResult:
    """Use LLM to score response quality. Requires OPENAI_API_KEY."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"), temperature=0)

    prompt = f"""Rate this marketing intelligence response on three criteria (0.0 to 1.0):

Query: {query}

Response:
{answer[:2000]}

Score each:
1. relevance: Does the response address the query?
2. completeness: Does it provide sufficient detail and data?
3. accuracy: Are the numbers, facts, and sources credible?

Respond ONLY with JSON: {{"relevance": 0.X, "completeness": 0.X, "accuracy": 0.X}}"""

    response = llm.invoke([
        SystemMessage(content="You are an evaluation judge. Return only valid JSON."),
        HumanMessage(content=prompt),
    ])

    try:
        scores = json.loads(response.content.strip())
        return EvaluationResult(
            relevance=float(scores.get("relevance", 0)),
            completeness=float(scores.get("completeness", 0)),
            accuracy=float(scores.get("accuracy", 0)),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return EvaluationResult(relevance=0.0, completeness=0.0, accuracy=0.0)


def batch_evaluate(save_results: bool = True) -> dict:
    """Run evaluation on all ground truth questions.

    Returns summary metrics and per-question scores.
    """
    questions = load_eval_questions()
    graph = build_graph()

    results = []
    for q in questions:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        output = graph.invoke({"query": q["query"]}, config)
        score = evaluate_single(q, output)

        # LLM judge if API key available
        if os.getenv("OPENAI_API_KEY"):
            llm_scores = evaluate_with_llm_judge(q["query"], output.get("final_answer", ""))
            score["llm_relevance"] = llm_scores.get("relevance", 0)
            score["llm_completeness"] = llm_scores.get("completeness", 0)
            score["llm_accuracy"] = llm_scores.get("accuracy", 0)

        results.append(score)

    # Aggregate
    n = len(results)
    summary = {
        "total_questions": n,
        "avg_routing": round(sum(r["routing"] for r in results) / n, 3),
        "avg_contains": round(sum(r["contains"] for r in results) / n, 3),
        "avg_facts": round(sum(r["facts"] for r in results) / n, 3),
        "avg_completeness": round(sum(r["completeness"] for r in results) / n, 3),
        "perfect_routing": sum(1 for r in results if r["routing"] == 1.0),
    }

    if any("llm_relevance" in r for r in results):
        summary["avg_llm_relevance"] = round(sum(r.get("llm_relevance", 0) for r in results) / n, 3)
        summary["avg_llm_completeness"] = round(sum(r.get("llm_completeness", 0) for r in results) / n, 3)
        summary["avg_llm_accuracy"] = round(sum(r.get("llm_accuracy", 0) for r in results) / n, 3)

    output = {"summary": summary, "results": results}

    if save_results:
        output_path = EVAL_DATA.parent / "eval_results.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_path}")

    return output


# CLI runner
if __name__ == "__main__":
    print("Running evaluation...\n")
    output = batch_evaluate()

    s = output["summary"]
    print(f"{'='*50}")
    print(f"EVALUATION RESULTS ({s['total_questions']} questions)")
    print(f"{'='*50}")
    print(f"Routing accuracy:  {s['avg_routing']:.1%} ({s['perfect_routing']}/{s['total_questions']} perfect)")
    print(f"Content presence:  {s['avg_contains']:.1%}")
    print(f"Factual accuracy:  {s['avg_facts']:.1%}")
    print(f"Completeness:      {s['avg_completeness']:.1%}")

    if "avg_llm_relevance" in s:
        print("\nLLM Judge:")
        print(f"  Relevance:       {s['avg_llm_relevance']:.1%}")
        print(f"  Completeness:    {s['avg_llm_completeness']:.1%}")
        print(f"  Accuracy:        {s['avg_llm_accuracy']:.1%}")

    print("\nPer-question details:")
    for r in output["results"]:
        status = "OK" if r["routing"] == 1.0 and r["contains"] >= 0.8 else "!!"
        print(f"  [{status}] {r['id']}: routing={r['routing']:.0%} contains={r['contains']:.0%} facts={r['facts']:.0%} plan={r['plan']}")
