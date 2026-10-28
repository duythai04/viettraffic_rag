import json
from pathlib import Path

from src.embeddings.embedder import LegalEmbedder
from src.lexical.bm25_index import BM25Index
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.vector_retriever import VectorRetriever
from src.vectordb.qdrant_store import QdrantStore


def main():
    print("=" * 70)
    print("HYBRID RETRIEVAL TEST")
    print("=" * 70)

    metadata_path = Path(
        "data/processed/embeddings/"
        "dbc075dd322c83ac.json"
    )

    with metadata_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("Loaded chunks:", len(chunks))

    assert len(chunks) == 1036

    print("Building BM25 index...")

    bm25_index = BM25Index(chunks)

    print("BM25 ready")

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

    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_index=bm25_index,
    )

    questions = [
        "Đi xe máy vượt đèn đỏ bị phạt bao nhiêu tiền?",
        "Không đội mũ bảo hiểm bị xử phạt thế nào?",
        "Điều khiển ô tô vượt quá tốc độ bị phạt bao nhiêu?",
    ]

    for question in questions:
        print("\n" + "=" * 70)
        print("QUESTION:", question)
        print("=" * 70)

        results = hybrid_retriever.retrieve(
            query=question,
            top_k=10,
            candidate_k=30,
        )

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print(f"RRF Score: {result['rrf_score']:.5f}")
            print(f"Citation: {result['citation']}")
            print(f"Content: {result['content'][:250]}")
            print("-" * 70)

        if "vượt đèn đỏ" in question.lower():
            expected_citation = "Điểm c Khoản 7 Điều 7"

            expected_ranks = [
                rank
                for rank, result in enumerate(results, start=1)
                if result["citation"] == expected_citation
            ]

            print(
                "\nExpected traffic-light chunk rank:",
                expected_ranks[0]
                if expected_ranks
                else "NOT IN TOP 10",
            )


if __name__ == "__main__":
    main()