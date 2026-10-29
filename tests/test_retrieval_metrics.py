import pytest

from src.eval.retrieval_metrics import RetrievalMetrics


def test_hit_at_1():
    retrieved = ["A", "B", "C"]
    relevant = ["A"]

    assert RetrievalMetrics.hit_at_k(
        retrieved, relevant, k=1
    ) == 1.0


def test_hit_at_1_failure():
    retrieved = ["A", "B", "C"]
    relevant = ["B"]

    assert RetrievalMetrics.hit_at_k(
        retrieved, relevant, k=1
    ) == 0.0


def test_recall_at_5():
    retrieved = ["A", "B", "C", "D", "E"]
    relevant = ["A", "C"]

    assert RetrievalMetrics.recall_at_k(
        retrieved, relevant, k=5
    ) == 1.0


def test_partial_recall():
    retrieved = ["A", "B", "C"]
    relevant = ["A", "D"]

    assert RetrievalMetrics.recall_at_k(
        retrieved, relevant, k=3
    ) == 0.5


def test_precision_at_5():
    retrieved = ["A", "B", "C", "D", "E"]
    relevant = ["A", "C"]

    assert RetrievalMetrics.precision_at_k(
        retrieved, relevant, k=5
    ) == 0.4


def test_mrr_at_10():
    retrieved = ["A", "B", "C", "D"]
    relevant = ["C"]

    assert RetrievalMetrics.mrr_at_k(
        retrieved, relevant, k=10
    ) == pytest.approx(1 / 3)


def test_no_relevant_results():
    retrieved = ["A", "B", "C"]
    relevant = ["X"]

    metrics = RetrievalMetrics.evaluate(
        retrieved, relevant
    )

    assert metrics["hit@1"] == 0.0
    assert metrics["recall@5"] == 0.0
    assert metrics["mrr@10"] == 0.0


def test_empty_retrieved_results():
    metrics = RetrievalMetrics.evaluate(
        retrieved_ids=[],
        relevant_ids=["A"],
    )

    assert all(
        value == 0.0
        for value in metrics.values()
    )


def test_invalid_k():
    with pytest.raises(ValueError):
        RetrievalMetrics.hit_at_k(
            ["A"], ["A"], k=0
        )