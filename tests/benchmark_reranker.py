import json
from pathlib import Path

from src.eval.retrieval_metrics import RetrievalMetrics
from src.rerank.cross_encoder_reranker import CrossEncoderReranker
from src.retrieval.reranked_retriever import RerankedRetriever

from tests.evaluate_retrieval import build_retriever


# ============================================================
# CONFIG
# ============================================================

EVAL_PATH = Path("data/evaluation/retrieval_eval.json")

OUTPUT_PATH = Path(
    "data/evaluation/reranker_results.json"
)

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

CANDIDATE_K = 20
TOP_K = 10
BATCH_SIZE = 8

METRIC_NAMES = [
    "hit@1",
    "hit@5",
    "recall@5",
    "precision@5",
    "mrr@10",
]


# ============================================================
# UTILS
# ============================================================

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_chunk_text(chunk: dict) -> str:
    """
    Extract text from a retrieved chunk.
    """
    text = chunk.get("text") or chunk.get("content")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            f"Missing text for chunk: {chunk.get('chunk_id')}"
        )

    return text


def enrich_candidates(
    candidates: list[dict],
    vehicle_metadata: dict,
) -> list[dict]:
    """
    Add vehicle metadata to candidates when missing.

    Does not modify the original retrieval results.
    """
    enriched = []

    for candidate in candidates:
        item = candidate.copy()

        chunk_id = item.get("chunk_id")

        if not chunk_id:
            raise ValueError(
                "Retrieved candidate is missing chunk_id"
            )

        if item.get("vehicle_type") is None:
            item["vehicle_type"] = vehicle_metadata.get(
                chunk_id
            )

        # Validate text before reranking
        get_chunk_text(item)

        enriched.append(item)

    return enriched


def print_candidates(
    candidates: list[dict],
    title: str,
    top_k: int = 5,
):
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)

    for rank, item in enumerate(
        candidates[:top_k],
        start=1,
    ):
        chunk_id = item.get("chunk_id")
        vehicle = item.get("vehicle_type")
        citation = item.get("citation")

        score = item.get(
            "rerank_score",
            item.get(
                "adjusted_score",
                item.get("rrf_score"),
            ),
        )

        text = get_chunk_text(item)
        preview = " ".join(text.split())[:140]

        print(f"\nRank {rank}")
        print(f"Chunk ID : {chunk_id}")
        print(f"Vehicle  : {vehicle}")
        print(f"Citation : {citation}")
        print(f"Score    : {score}")
        print(f"Text     : {preview}")


def evaluate_results(
    retrieved: list[dict],
    expected_ids: list[str],
) -> dict:
    retrieved_ids = [
        item["chunk_id"]
        for item in retrieved
    ]

    return RetrievalMetrics.evaluate(
        retrieved_ids,
        expected_ids,
    )


def calculate_summary(results: list[dict]) -> dict:
    if not results:
        raise ValueError(
            "Cannot calculate summary for empty results"
        )

    return {
        metric: sum(
            result["metrics"][metric]
            for result in results
        ) / len(results)
        for metric in METRIC_NAMES
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VIETTRAFFIC RAG - CROSS-ENCODER BENCHMARK")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load evaluation dataset
    # --------------------------------------------------------

    dataset = load_json(EVAL_PATH)

    if not dataset:
        raise ValueError(
            "Evaluation dataset is empty"
        )

    print(f"\nLoaded {len(dataset)} evaluation questions")

    # --------------------------------------------------------
    # 2. Initialize base retriever
    # --------------------------------------------------------

    print("\nInitializing Vehicle-aware Retriever...")

    base_retriever = build_retriever()

    vehicle_metadata = getattr(
        base_retriever,
        "vehicle_metadata",
        {},
    )

    if not isinstance(vehicle_metadata, dict):
        raise TypeError(
            "Vehicle metadata must be a dictionary"
        )

    print(
        f"Vehicle metadata entries: {len(vehicle_metadata)}"
    )

    # --------------------------------------------------------
    # 3. Initialize Cross-Encoder
    # --------------------------------------------------------

    print("\nInitializing Cross-Encoder Reranker...")

    reranker = CrossEncoderReranker(
        model_name=MODEL_NAME,
        batch_size=BATCH_SIZE,
    )

    # --------------------------------------------------------
    # 4. Initialize Reranked Retriever
    # --------------------------------------------------------

    retriever = RerankedRetriever(
        base_retriever=base_retriever,
        reranker=reranker,
        candidate_k=CANDIDATE_K,
    )

    # --------------------------------------------------------
    # 5. Evaluate each question
    # --------------------------------------------------------

    results = []
    baseline_results = []

    for index, item in enumerate(dataset, start=1):

        question_id = item["id"]
        question = item["question"]
        expected_ids = item["expected_chunk_ids"]

        print("\n" + "=" * 70)
        print(
            f"[{index}/{len(dataset)}] "
            f"{question_id}: {question}"
        )
        print("=" * 70)

        print(f"Expected chunks: {expected_ids}")

        # ----------------------------------------------------
        # Retrieve original candidates
        # ----------------------------------------------------

        original_candidates = base_retriever.retrieve(
            query=question,
            top_k=CANDIDATE_K,
            candidate_k=CANDIDATE_K,
        )

        # ----------------------------------------------------
        # Enrich metadata
        # ----------------------------------------------------

        enriched_candidates = enrich_candidates(
            original_candidates,
            vehicle_metadata,
        )

        # ----------------------------------------------------
        # Print candidates before reranking
        # ----------------------------------------------------

        print_candidates(
            enriched_candidates,
            title="BEFORE RERANKING - TOP 5",
            top_k=5,
        )

        # ----------------------------------------------------
        # Baseline evaluation
        # ----------------------------------------------------

        baseline_top_k = enriched_candidates[:TOP_K]

        baseline_metrics = evaluate_results(
            baseline_top_k,
            expected_ids,
        )

        baseline_results.append({
            "id": question_id,
            "question": question,
            "expected_chunk_ids": expected_ids,
            "retrieved_chunk_ids": [
                chunk["chunk_id"]
                for chunk in baseline_top_k
            ],
            "metrics": baseline_metrics,
        })

        # ----------------------------------------------------
        # Cross-Encoder reranking
        # ----------------------------------------------------
        # Important:
        # Rerank enriched candidates directly so metadata
        # is not lost.
        # ----------------------------------------------------

        reranked = reranker.rerank(
            query=question,
            candidates=enriched_candidates,
            top_k=TOP_K,
        )

        # ----------------------------------------------------
        # Print candidates after reranking
        # ----------------------------------------------------

        print_candidates(
            reranked,
            title="AFTER RERANKING - TOP 5",
            top_k=5,
        )

        # ----------------------------------------------------
        # Evaluate reranked results
        # ----------------------------------------------------

        metrics = evaluate_results(
            reranked,
            expected_ids,
        )

        retrieved_ids = [
            chunk["chunk_id"]
            for chunk in reranked
        ]

        results.append({
            "id": question_id,
            "question": question,
            "expected_chunk_ids": expected_ids,
            "retrieved_chunk_ids": retrieved_ids,
            "metrics": metrics,
            "top_results": [
                {
                    "rank": rank,
                    "chunk_id": chunk["chunk_id"],
                    "vehicle_type": chunk.get(
                        "vehicle_type"
                    ),
                    "citation": chunk.get(
                        "citation"
                    ),
                    "rerank_score": chunk.get(
                        "rerank_score"
                    ),
                }
                for rank, chunk in enumerate(
                    reranked,
                    start=1,
                )
            ],
        })

        print("\n" + "-" * 70)
        print("QUERY EVALUATION")
        print("-" * 70)

        print(
            f"Baseline Hit@1 : "
            f"{baseline_metrics['hit@1']:.0f}"
        )

        print(
            f"Reranked Hit@1 : "
            f"{metrics['hit@1']:.0f}"
        )

        print(
            f"Baseline MRR@10: "
            f"{baseline_metrics['mrr@10']:.4f}"
        )

        print(
            f"Reranked MRR@10: "
            f"{metrics['mrr@10']:.4f}"
        )

    # --------------------------------------------------------
    # 6. Calculate summaries
    # --------------------------------------------------------

    baseline_summary = calculate_summary(
        baseline_results
    )

    reranker_summary = calculate_summary(
        results
    )

    # --------------------------------------------------------
    # 7. Print benchmark comparison
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("BENCHMARK COMPARISON")
    print("=" * 70)

    print(
        f"{'Metric':<18}"
        f"{'Vehicle-aware':<18}"
        f"{'Cross-Encoder':<18}"
        f"{'Difference':<18}"
    )

    print("-" * 72)

    for metric in METRIC_NAMES:

        baseline_score = baseline_summary[metric]
        reranker_score = reranker_summary[metric]

        difference = reranker_score - baseline_score

        print(
            f"{metric:<18}"
            f"{baseline_score:<18.4f}"
            f"{reranker_score:<18.4f}"
            f"{difference:+.4f}"
        )

    # --------------------------------------------------------
    # 8. Save results
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "model": MODEL_NAME,
        "candidate_k": CANDIDATE_K,
        "top_k": TOP_K,
        "total_questions": len(dataset),
        "baseline": {
            "method": "vehicle_aware",
            "summary": baseline_summary,
            "results": baseline_results,
        },
        "reranker": {
            "method": "metadata_aware_cross_encoder",
            "summary": reranker_summary,
            "results": results,
        },
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
    print("BENCHMARK COMPLETED")
    print("=" * 70)

    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()