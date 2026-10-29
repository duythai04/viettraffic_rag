from src.pipelines.query_pipeline import QueryPipeline


class DemoRetriever:
    def retrieve(self, question, top_k=5):
        return [
            {
                "chunk_id": (
                    "168-2024-ND-CP_dieu-12_khoan-10"
                ),
                "citation": (
                    "Điều 12 khoản 10 "
                    "Nghị định 168/2024/NĐ-CP"
                ),
                "content": "Nội dung OCR chưa kiểm chứng",
            }
        ]


def main():
    pipeline = QueryPipeline(
        retriever=DemoRetriever()
    )

    question = input("Nhập câu hỏi: ")

    result = pipeline.run(question)

    print("\n========== RAG ANSWER ==========")
    print(result["answer"])

    print("\nCitations:")
    for citation in result["citations"]:
        print("-", citation)

    print("\nVerified:", result["verified"])
    print(
        "Retrieved chunks:",
        result["retrieved_chunks"],
    )


if __name__ == "__main__":
    main()