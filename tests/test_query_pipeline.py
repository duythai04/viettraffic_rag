from src.pipelines.query_pipeline import QueryPipeline
from src.generation.grounded_answer import (
    GroundedAnswerGenerator,
)


class FakeRetriever:
    def retrieve(self, question, top_k=5):
        return [
            {
                "chunk_id": (
                    "168-2024-ND-CP_dieu-12"
                    "_khoan-10"
                ),
                "citation": (
                    "Điều 12 khoản 10 "
                    "Nghị định 168/2024/NĐ-CP"
                ),
                "content": "Nội dung OCR thử nghiệm",
            }
        ]


class FakeFineResolver:
    def resolve(self, clause_id, recipient=None, as_of=None):
        return None


def test_query_pipeline_without_verified_fine():
    pipeline = QueryPipeline(
        retriever=FakeRetriever(),
        answer_generator=GroundedAnswerGenerator(
            fine_resolver=FakeFineResolver()
        ),
    )

    result = pipeline.run(
        "Hành vi vi phạm bị phạt bao nhiêu?"
    )

    assert result["verified"] is False
    assert result["retrieved_chunks"] == 1
    assert len(result["citations"]) == 1
    assert "chưa có" in result["answer"]


def test_query_pipeline_empty_question():
    pipeline = QueryPipeline(
        retriever=FakeRetriever(),
        answer_generator=GroundedAnswerGenerator(
            fine_resolver=FakeFineResolver()
        ),
    )

    try:
        pipeline.run("   ")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_grounded_answer_without_context():
    generator = GroundedAnswerGenerator(
        fine_resolver=FakeFineResolver()
    )

    result = generator.generate(
        question="Vi phạm giao thông?",
        contexts=[],
    )

    assert result["verified"] is False
    assert result["citations"] == []