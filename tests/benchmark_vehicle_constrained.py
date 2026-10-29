import json
from pathlib import Path

from src.eval.retrieval_metrics import RetrievalMetrics
from src.query.vehicle_detector import VehicleDetector
from src.rerank.cross_encoder_reranker import CrossEncoderReranker
from src.rerank.vehicle_constrained_reranker import (
    VehicleConstrainedReranker,
)
from src.retrieval.vehicle_constrained_retriever import (
    VehicleConstrainedRetriever,
)

from tests.evaluate_retrieval import build_retriever


EVAL_PATH = Path(
    "data/evaluation/retrieval_eval.json"
)

OUTPUT_PATH = Path(
    "data/evaluation/vehicle_constrained_results.json"
)

METRICS = [
    "hit@1",
    "hit@5",
    "recall@5",
    "precision@5",
    "mrr@10",
]


def evaluate_query(
    retrieved,
    expected_ids,
):
    retrieved_ids = [
        item["chunk_id"]
        for item in retrieved
    ]

    return RetrievalMetrics.evaluate(
        retrieved_ids,
        expected_ids,
    )


def calculate_summary(results):
    return {
        metric: sum(
            item["metrics"][metric]
            for item in results
        ) / len(results)
        for metric in METRICS
    }


def main():

    with EVAL_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        dataset = json.load(f)

    if not dataset:
        raise ValueError("Evaluation dataset is empty")

    print("\nInitializing Vehicle-aware Retriever...")

    base_retriever = build_retriever()

    print("\nInitializing Cross-Encoder...")

    cross_encoder = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-v2-m3",
        batch_size=8,
    )

    print("\nInitializing Vehicle-Constrained Reranker...")

    constrained_reranker = VehicleConstrainedReranker(
        reranker=cross_encoder,
        vehicle_detector=VehicleDetector(),
        vehicle_metadata=base_retriever.vehicle_metadata,
    )

    retriever = VehicleConstrainedRetriever(
        base_retriever=base_retriever,
        constrained_reranker=constrained_reranker,
        candidate_k=20,
    )

    results = []

    for item in dataset:

        question = item["question"]
        expected_ids = item["expected_chunk_ids"]

        retrieved = retriever.retrieve(
            query=question,
            top_k=10,
        )

        metrics = evaluate_query(
            retrieved,
            expected_ids,
        )

        retrieved_ids = [
            chunk["chunk_id"]
            for chunk in retrieved
        ]

        results.append({
            "id": item["id"],
            "question": question,
            "expected_chunk_ids": expected_ids,
            "retrieved_chunk_ids": retrieved_ids,
            "metrics": metrics,
        })

        print(
            f"{item['id']} | "
            f"Hit@1={metrics['hit@1']:.0f} | "
            f"MRR@10={metrics['mrr@10']:.3f}"
        )

    summary = calculate_summary(results)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "method": "vehicle_constrained_cross_encoder",
        "summary": summary,
        "results": results,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("VEHICLE-CONSTRAINED BENCHMARK")
    print("=" * 70)

    for metric, score in summary.items():
        print(f"{metric:15}: {score:.4f}")

    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()