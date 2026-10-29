import json
from pathlib import Path

from src.eval.retrieval_metrics import RetrievalMetrics
from tests.evaluate_retrieval import build_retriever


EVAL_PATH = Path("data/evaluation/retrieval_eval.json")
OUTPUT_PATH = Path("data/evaluation/benchmark_results.json")


def load_dataset():
    with EVAL_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_chunk_ids(results):
    return [result["chunk_id"] for result in results]


def evaluate_method(name, retrieve_fn, dataset):
    print(f"\n{'=' * 70}")
    print(f"EVALUATING: {name}")
    print("=" * 70)

    query_results = []

    for item in dataset:
        question = item["question"]
        expected = item["expected_chunk_ids"]

        results = retrieve_fn(question)

        retrieved_ids = extract_chunk_ids(results)

        scores = RetrievalMetrics.evaluate(
            retrieved_ids,
            expected,
        )

        query_results.append({
            "question": question,
            "expected_chunk_ids": expected,
            "retrieved_chunk_ids": retrieved_ids,
            "metrics": scores,
        })

        print(
            f"{item['id']} | "
            f"Hit@1={scores['hit@1']:.0f} | "
            f"MRR@10={scores['mrr@10']:.3f}"
        )

    summary = {
        metric: sum(
            result["metrics"][metric]
            for result in query_results
        ) / len(query_results)
        for metric in [
            "hit@1",
            "hit@5",
            "recall@5",
            "precision@5",
            "mrr@10",
        ]
    }

    return {
        "method": name,
        "summary": summary,
        "results": query_results,
    }


def main():
    dataset = load_dataset()

    if not dataset:
        raise ValueError("Evaluation dataset is empty")

    vehicle_retriever = build_retriever()

    hybrid_retriever = vehicle_retriever.hybrid_retriever
    vector_retriever = hybrid_retriever.vector_retriever

    methods = {
        "dense": lambda q: vector_retriever.retrieve(
            query=q,
            top_k=10,
        ),

        "hybrid": lambda q: hybrid_retriever.retrieve(
            query=q,
            top_k=10,
        ),

        "vehicle_aware": lambda q: vehicle_retriever.retrieve(
            query=q,
            top_k=10,
            candidate_k=30,
        ),
    }

    benchmark = {}

    for name, retrieve_fn in methods.items():
        benchmark[name] = evaluate_method(
            name,
            retrieve_fn,
            dataset,
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            benchmark,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"{'Method':<20}"
        f"{'Hit@1':<12}"
        f"{'Recall@5':<12}"
        f"{'MRR@10':<12}"
    )

    for name, result in benchmark.items():
        summary = result["summary"]

        print(
            f"{name:<20}"
            f"{summary['hit@1']:<12.4f}"
            f"{summary['recall@5']:<12.4f}"
            f"{summary['mrr@10']:<12.4f}"
        )

    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()