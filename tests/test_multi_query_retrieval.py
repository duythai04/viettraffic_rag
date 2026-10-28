from src.embeddings.embedder import LegalEmbedder
from src.vectordb.qdrant_store import QdrantStore
from src.retrieval.vector_retriever import VectorRetriever
from src.retrieval.multi_query_retriever import MultiQueryRetriever


def main():
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

    retriever = MultiQueryRetriever(
        vector_retriever=vector_retriever,
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

        results = retriever.retrieve(
            query=question,
            top_k=10,
            candidate_k=30,
        )

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print(f"RRF Score: {result['rrf_score']:.5f}")
            print(f"Citation: {result['citation']}")
            print(f"Content: {result['content'][:300]}")
            print("-" * 70)

        if "vượt đèn đỏ" in question.lower():
            expected_chunk_id = (
                "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
            )

            ranks = [
                rank
                for rank, result in enumerate(results, start=1)
                if result["chunk_id"] == expected_chunk_id
            ]

            print(
                "\nExpected motorcycle traffic-light chunk rank:",
                ranks[0] if ranks else "NOT IN TOP 10",
            )


if __name__ == "__main__":
    main()