from src.pipelines.query_pipeline import QueryPipeline


class FakeRetriever:
    def __init__(self):
        self.called = False

    def retrieve(self, question, top_k=5):
        self.called = True
        return []


class FakeAnswerGenerator:
    def __init__(self):
        self.called = False

    def generate(self, **kwargs):
        self.called = True
        return {
            "answer": "Fake answer",
            "citations": [],
            "verified": False,
        }


def build_test_pipeline():
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    pipeline = QueryPipeline(
        retriever=retriever,
        answer_generator=generator,
    )

    return pipeline, retriever, generator


def test_missing_speed_skips_retrieval_and_llm():
    pipeline, retriever, generator = build_test_pipeline()

    result = pipeline.run(
        "Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        debug=True,
    )

    assert result["intent"] == "legal_fine"

    assert result["requires_clarification"] is True

    assert (
        result["clarification_reason"]
        == "missing_speed_excess"
    )

    assert retriever.called is False

    assert generator.called is False

    assert result["verified"] is False

    assert result["citations"] == []

    assert result["retrieved_chunks"] == 0

    assert result["selected_evidence_count"] == 0


def test_specific_speed_continues_to_retrieval():
    pipeline, retriever, generator = build_test_pipeline()

    result = pipeline.run(
        "Xe máy vượt tốc độ 10 km/h bị phạt bao nhiêu?"
    )

    assert retriever.called is True

    assert result["requires_clarification"] is False


def test_red_light_continues_to_retrieval():
    pipeline, retriever, generator = build_test_pipeline()

    result = pipeline.run(
        "Ô tô vượt đèn đỏ bị phạt bao nhiêu?"
    )

    assert retriever.called is True

    assert result["requires_clarification"] is False
