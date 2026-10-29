from src.rerank.cross_encoder_reranker import CrossEncoderReranker


def main():
    reranker = CrossEncoderReranker()

    query = "Ô tô chạy quá tốc độ trên 35 km/h bị phạt thế nào?"

    candidates = [
        {
            "chunk_id": "chunk_1",
            "text": "Điều khiển xe ô tô chạy quá tốc độ quy định trên 20 km/h đến 35 km/h.",
        },
        {
            "chunk_id": "chunk_2",
            "text": "Điều khiển xe ô tô chạy quá tốc độ quy định trên 35 km/h.",
        },
        {
            "chunk_id": "chunk_3",
            "text": "Điều khiển xe ô tô chạy quá tốc độ quy định từ 05 km/h đến dưới 10 km/h.",
        },
    ]

    results = reranker.rerank(
        query=query,
        candidates=candidates,
        top_k=3,
    )

    print("\nCROSS-ENCODER RERANKING RESULTS")

    for rank, item in enumerate(results, start=1):
        print(
            f"Rank {rank}: "
            f"{item['chunk_id']} | "
            f"Score: {item['rerank_score']:.4f}"
        )


if __name__ == "__main__":
    main()