from __future__ import annotations

import json
import re
import sys
import time

from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR))

from scripts.test_real_rag import build_pipeline


DATASET_PATH = (
    BASE_DIR / "tests/datasets/traffic_questions.json"
)

REPORT_PATH = (
    BASE_DIR / "reports/e2e_results.json"
)

TOP_K = 5


# ============================================================
# SAFETY PATTERNS
# ============================================================

MONEY_PATTERN = re.compile(
    r"\b\d[\d.,\s]*"
    r"(?:đồng|vnd|vnđ|triệu|tỷ)\b",
    re.IGNORECASE,
)


# ============================================================
# DATASET LOADING
# ============================================================

def load_dataset() -> list[dict]:

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    test_cases = data.get("test_cases")

    if not isinstance(test_cases, list):
        raise ValueError(
            "Dataset must contain a test_cases list."
        )

    if not test_cases:
        raise ValueError(
            "Dataset must contain at least one test case."
        )

    seen_ids = set()

    for index, test_case in enumerate(test_cases):

        if not isinstance(test_case, dict):
            raise ValueError(
                f"Test case {index} must be an object."
            )

        case_id = test_case.get("id")
        question = test_case.get("question")

        if not isinstance(case_id, str) or not case_id:
            raise ValueError(
                f"Test case {index} has invalid id."
            )

        if case_id in seen_ids:
            raise ValueError(
                f"Duplicate test case id: {case_id}"
            )

        seen_ids.add(case_id)

        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                f"Test case {case_id} has invalid question."
            )

        if "expected_intent" not in test_case:
            raise ValueError(
                f"Test case {case_id} must define expected_intent."
            )

        expected_clarification = test_case.get(
            "expected_requires_clarification"
        )

        if (
            expected_clarification is not None
            and not isinstance(expected_clarification, bool)
        ):
            raise ValueError(
                f"Test case {case_id}: "
                "expected_requires_clarification must be boolean."
            )

    return test_cases


# ============================================================
# RETRIEVAL EXTRACTION
# ============================================================

def extract_retrieved_ids(result: dict) -> list[str]:

    ids = []

    retrieval_results = result.get(
        "retrieval_results",
        [],
    ) or []

    for item in retrieval_results:

        if isinstance(item, dict):
            payload = item.get("payload", item)
        else:
            payload = getattr(item, "payload", {})

        if not isinstance(payload, dict):
            continue

        chunk_id = payload.get("chunk_id")

        if chunk_id:
            ids.append(chunk_id)

    return ids


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================

def extract_selected_evidence(
    result: dict,
) -> list[dict]:

    selection = result.get(
        "evidence_selection",
        {},
    ) or {}

    if not isinstance(selection, dict):
        return []

    selected = selection.get(
        "selected_evidence",
        [],
    )

    if not isinstance(selected, list):
        return []

    return selected


# ============================================================
# CLARIFICATION CHECKS
# ============================================================

def evaluate_clarification(
    test_case: dict,
    result: dict,
    checks: dict,
) -> bool:

    expected_clarification = test_case.get(
        "expected_requires_clarification"
    )

    actual_clarification = result.get(
        "requires_clarification",
        False,
    )

    if expected_clarification is not None:

        checks["clarification"] = (
            actual_clarification
            is expected_clarification
        )

    expected_reason = test_case.get(
        "expected_clarification_reason"
    )

    if expected_reason is not None:

        checks["clarification_reason"] = (
            result.get("clarification_reason")
            == expected_reason
        )

    if expected_clarification is True:

        checks["clarification_no_retrieval"] = (
            result.get("retrieved_chunks") == 0
            and not result.get("retrieval_results", [])
        )

        checks["clarification_no_evidence"] = (
            result.get("selected_evidence_count") == 0
            and not extract_selected_evidence(result)
        )

        checks["clarification_has_message"] = (
            isinstance(result.get("answer"), str)
            and bool(result["answer"].strip())
        )

        checks["clarification_unverified"] = (
            result.get("verified") is False
        )

        checks["clarification_no_citations"] = (
            result.get("citations", []) == []
        )

        return True

    return False


# ============================================================
# EVALUATE SINGLE CASE
# ============================================================

def evaluate_case(
    test_case: dict,
    result: dict,
) -> dict:

    checks = {}

    # --------------------------------------------------------
    # 1. INTENT
    # --------------------------------------------------------

    expected_intent = test_case.get(
        "expected_intent"
    )

    if expected_intent is not None:

        checks["intent"] = (
            result.get("intent") == expected_intent
        )

    # --------------------------------------------------------
    # 2. VERIFIED STATUS
    # --------------------------------------------------------

    expected_verified = test_case.get(
        "expected_verified"
    )

    if expected_verified is not None:

        checks["verified"] = (
            result.get("verified") is expected_verified
        )

    # --------------------------------------------------------
    # 3. CLARIFICATION
    # --------------------------------------------------------

    expected_clarification = test_case.get(
        "expected_requires_clarification"
    )

    actual_clarification = result.get(
        "requires_clarification",
        False,
    )

    is_clarification_case = evaluate_clarification(
        test_case=test_case,
        result=result,
        checks=checks,
    )

    # --------------------------------------------------------
    # 4. EVIDENCE SELECTION
    # --------------------------------------------------------

    selection = result.get(
        "evidence_selection",
        {},
    ) or {}

    if not isinstance(selection, dict):
        selection = {}

    retrieved_ids = extract_retrieved_ids(result)

    selected_evidence = extract_selected_evidence(
        result
    )

    selected_ids = [
        item.get("chunk_id")
        for item in selected_evidence
        if isinstance(item, dict)
    ]

    # --------------------------------------------------------
    # 5. VEHICLE / ROLE / RETRIEVAL
    # --------------------------------------------------------

    # Clarification cases terminate before retrieval.
    # Therefore, vehicle and role metadata from
    # evidence_selection are not expected to exist.

    if not is_clarification_case:

        expected_vehicle = test_case.get(
            "expected_vehicle"
        )

        if expected_vehicle is not None:

            checks["vehicle"] = (
                selection.get("query_vehicle")
                == expected_vehicle
            )

        expected_role = test_case.get(
            "expected_role"
        )

        if expected_role is not None:

            checks["role"] = (
                selection.get("query_role")
                == expected_role
            )

        expected_chunk_id = test_case.get(
            "expected_chunk_id"
        )

        if expected_chunk_id is not None:

            checks["retrieval_hit_at_k"] = (
                expected_chunk_id in retrieved_ids
            )

            checks["evidence_hit_at_k"] = (
                expected_chunk_id in selected_ids
            )

            checks["evidence_top1"] = (
                bool(selected_ids)
                and selected_ids[0] == expected_chunk_id
            )

    # --------------------------------------------------------
    # 6. ANSWER SAFETY
    # --------------------------------------------------------

    answer = result.get("answer", "")

    if not isinstance(answer, str):
        answer = str(answer)

    # A monetary fine must not be emitted without
    # a verified fine record.

    if result.get("verified") is False:

        checks["answer_safety"] = (
            MONEY_PATTERN.search(answer) is None
        )

    # --------------------------------------------------------
    # 7. RESULT
    # --------------------------------------------------------

    passed = bool(checks) and all(
        checks.values()
    )

    return {
        "id": test_case["id"],
        "question": test_case["question"],
        "passed": passed,
        "checks": checks,
        "actual": {
            "intent": result.get("intent"),
            "verified": result.get("verified"),
            "requires_clarification": actual_clarification,
            "clarification_reason": result.get(
                "clarification_reason"
            ),
            "retrieved_chunks": result.get(
                "retrieved_chunks"
            ),
            "selected_evidence_count": result.get(
                "selected_evidence_count"
            ),
            "query_vehicle": selection.get(
                "query_vehicle"
            ),
            "query_role": selection.get(
                "query_role"
            ),
            "retrieved_ids": retrieved_ids,
            "selected_ids": selected_ids,
            "answer": answer,
            "citations": result.get(
                "citations",
                [],
            ),
        },
    }


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    results: list[dict],
) -> dict:

    metrics = {}

    names = sorted({
        name
        for result in results
        for name in result.get("checks", {})
    })

    for name in names:

        values = [
            result["checks"][name]
            for result in results
            if name in result["checks"]
        ]

        passed = sum(values)
        total = len(values)

        metrics[name] = {
            "passed": passed,
            "total": total,
            "accuracy": (
                round(passed / total, 4)
                if total
                else None
            ),
        }

    return metrics


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("VIETTRAFFIC RAG - END-TO-END EVALUATION")
    print("=" * 65)

    test_cases = load_dataset()

    print(
        f"\nLoaded {len(test_cases)} test cases."
    )

    print("\nInitializing RAG pipeline...")

    # Initialize BGE-M3, Qdrant, BM25 and
    # the complete query pipeline only once.

    pipeline = build_pipeline()

    results = []

    for index, test_case in enumerate(
        test_cases,
        start=1,
    ):

        print("\n" + "-" * 65)

        print(
            f"[{index}/{len(test_cases)}] "
            f"{test_case['id']}"
        )

        print(
            "Question:",
            test_case["question"],
        )

        started = time.perf_counter()

        try:

            response = pipeline.run(
                question=test_case["question"],
                top_k=TOP_K,
                debug=True,
            )

            evaluation = evaluate_case(
                test_case=test_case,
                result=response,
            )

        except Exception as exc:

            evaluation = {
                "id": test_case["id"],
                "question": test_case["question"],
                "passed": False,
                "checks": {
                    "pipeline_execution": False,
                },
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }

        evaluation["duration_seconds"] = round(
            time.perf_counter() - started,
            3,
        )

        results.append(evaluation)

        status = (
            "PASS"
            if evaluation["passed"]
            else "FAIL"
        )

        print("Status:", status)

        for name, passed in evaluation[
            "checks"
        ].items():

            print(
                f"  {name}: "
                f"{'PASS' if passed else 'FAIL'}"
            )

        if "error" in evaluation:

            print(
                "Error:",
                evaluation["error"],
            )

        print(
            "Duration:",
            evaluation["duration_seconds"],
            "seconds",
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    passed_count = sum(
        item["passed"]
        for item in results
    )

    failed_count = (
        len(results) - passed_count
    )

    metrics = calculate_metrics(results)

    report = {
        "name": "VietTraffic RAG E2E Evaluation",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "top_k": TOP_K,
        "total_tests": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "metrics": metrics,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 65)
    print("E2E TEST SUMMARY")
    print("=" * 65)

    print("Total:", len(results))
    print("Passed:", passed_count)
    print("Failed:", failed_count)

    print("\nMetrics:")

    for name, metric in metrics.items():

        accuracy = metric["accuracy"]

        accuracy_text = (
            f"{accuracy * 100:.2f}%"
            if accuracy is not None
            else "N/A"
        )

        print(
            f"  {name}: {accuracy_text} "
            f"({metric['passed']}/{metric['total']})"
        )

    print(
        "\nReport saved to:",
        REPORT_PATH,
    )

    if failed_count:
        sys.exit(1)


if __name__ == "__main__":
    main()