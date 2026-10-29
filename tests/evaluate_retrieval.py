from __future__ import annotations

import json
from pathlib import Path

from src.embeddings.embedder import LegalEmbedder
from src.eval.retrieval_metrics import RetrievalMetrics
from src.lexical.bm25_index import BM25Index
from src.preprocessing.vehicle_metadata import VehicleMetadataEnricher
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.vector_retriever import VectorRetriever
from src.retrieval.vehicle_aware_retriever import VehicleAwareRetriever
from src.vectordb.qdrant_store import QdrantStore


CHUNKS_PATH = Path(
    "data/processed/embeddings/dbc075dd322c83ac.json"
)

EVAL_PATH = Path(
    "data/evaluation/retrieval_eval.json"
)

REPORT_PATH = Path(
    "data/evaluation/vehicle_aware_results.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_retriever():
    chunks = load_json(CHUNKS_PATH)

    chunks = VehicleMetadataEnricher().enrich(chunks)

    vehicle_metadata = {
        chunk["chunk_id"]: chunk.get("vehicle_type")
        for chunk in chunks
    }

    bm25 = BM25Index(chunks)

    embedder = LegalEmbedder(
        model_name="BAAI/bge-m3",
        batch_size=8,
    )

    store = QdrantStore(
        collection_name="viettraffic_legal",
        vector_size=embedder.dimension,
    )

    vector_retriever = VectorRetriever(
        embedder=embedder,
        store=store,
    )

    hybrid = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_index=bm25,
    )

    return VehicleAwareRetriever(
        hybrid_retriever=hybrid,
        vehicle_metadata=vehicle_metadata,
        vehicle_boost=0.005,
        mismatch_penalty=0.005,
    )


def main():
    dataset = load_json(EVAL_PATH)

    if not dataset:
        raise ValueError("Evaluation dataset is empty")

    retriever = build_retriever()

    metrics = RetrievalMetrics()

    all_results = []

    for item in dataset:
        question = item["question"]
        expected_ids = item["expected_chunk_ids"]

        print("\n" + "=" * 70)
        print(f"Question: {question}")

        results = retriever.retrieve(
            query=question,
            top_k=10,
            candidate_k=30,
        )

        retrieved_ids = [
            result["chunk_id"]
            for result in results
        ]

        scores = metrics.evaluate(
            retrieved_ids=retrieved_ids,
            relevant_ids=expected_ids,
        )

        print("Metrics:", scores)

        all_results.append(
            {
                "id": item["id"],
                "question": question,
                "expected_chunk_ids": expected_ids,
                "retrieved_chunk_ids": retrieved_ids,
                "metrics": scores,
            }
        )

    metric_names = [
        "hit@1",
        "hit@5",
        "recall@5",
        "precision@5",
        "mrr@10",
    ]

    summary = {
        name: sum(
            result["metrics"][name]
            for result in all_results
        ) / len(all_results)
        for name in metric_names
    }

    print("\n" + "=" * 70)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 70)

    for name, value in summary.items():
        print(f"{name:15}: {value:.4f}")

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "method": "vehicle_aware_hybrid",
                "total_questions": len(dataset),
                "summary": summary,
                "results": all_results,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()