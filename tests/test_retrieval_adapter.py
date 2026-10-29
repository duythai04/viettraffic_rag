from src.pipelines.query_pipeline import QueryPipeline


class FakeRetriever:
    def retrieve(self, query, top_k=5):
        return []


def make_pipeline():
    return QueryPipeline(
        retriever=FakeRetriever(),
    )


def test_vehicle_aware_result():

    pipeline = make_pipeline()

    results = [
        {
            "chunk_id": (
                "168-2024-ND-CP_dieu-7_khoan-4_diem-a"
            ),
            "citation": (
                "Điểm a khoản 4 Điều 7"
            ),
            "content": "Nội dung quy định thử nghiệm",
            "metadata": {
                "article": 7,
                "clause": 4,
                "point": "a",
                "clause_preamble": "Nội dung khoản",
            },
            "vehicle_type": "motorcycle",
            "rrf_score": 0.035,
            "adjusted_score": 0.040,
        }
    ]

    contexts = pipeline._build_contexts(results)

    assert len(contexts) == 1

    context = contexts[0]

    assert context["article"] == 7
    assert context["clause"] == 4
    assert context["point"] == "a"

    assert context["vehicle_type"] == "motorcycle"
    assert context["retrieval_score"] == 0.040

    assert context["clause_id"] == (
        "168-2024-ND-CP_dieu-7_khoan-4"
    )


def test_duplicate_chunks():

    pipeline = make_pipeline()

    chunk = {
        "chunk_id": (
            "168-2024-ND-CP_dieu-7_khoan-4_diem-a"
        ),
        "content": "Nội dung thử nghiệm",
    }

    contexts = pipeline._build_contexts([
        chunk,
        chunk,
    ])

    assert len(contexts) == 1


def test_empty_results():

    pipeline = make_pipeline()

    contexts = pipeline._build_contexts([])

    assert contexts == []


def test_qdrant_style_payload():

    pipeline = make_pipeline()

    results = [
        {
            "payload": {
                "chunk_id": (
                    "168-2024-ND-CP_dieu-7_khoan-4"
                ),
                "article": 7,
                "clause": 4,
                "content": "Nội dung thử nghiệm",
            }
        }
    ]

    contexts = pipeline._build_contexts(results)

    assert len(contexts) == 1
    assert contexts[0]["article"] == 7
    assert contexts[0]["clause"] == 4