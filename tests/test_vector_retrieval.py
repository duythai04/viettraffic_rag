from src.embeddings.embedder import LegalEmbedder
from src.vectordb.qdrant_store import QdrantStore
from src.retrieval.vector_retriever import VectorRetriever


def main():
    embedder = LegalEmbedder(
        model_name="BAAI/bge-m3",
        batch_size=8,
    )

    store = QdrantStore(
        collection_name="viettraffic_legal",
        vector_size=embedder.dimension,
    )

    retriever = VectorRetriever(
        embedder=embedder,
        store=store,
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
            top_k=5,
        )

        assert len(results) > 0

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print(f"Score: {result['score']:.4f}")
            print(f"Citation: {result['citation']}")
            print(f"Content: {result['content'][:400]}")
            print("-" * 70)


if __name__ == "__main__":
    main()