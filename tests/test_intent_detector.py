import pytest

from src.query.intent_detector import QueryIntentDetector
from src.pipelines.query_pipeline import QueryPipeline


@pytest.fixture
def detector():
    return QueryIntentDetector()


@pytest.mark.parametrize(
    "question, expected",
    [
        ("xin chào", "greeting"),
        ("Xin chào!", "greeting"),
        ("hello", "greeting"),
        ("Hello!", "greeting"),
        ("hi", "greeting"),
        ("chào bạn", "greeting"),

        ("bạn là ai?", "identity"),
        ("bạn tên gì", "identity"),

        (
            "Xe máy vượt đèn đỏ bị phạt bao nhiêu?",
            "legal_fine",
        ),
        (
            "Ô tô vi phạm nồng độ cồn bị phạt bao nhiêu?",
            "legal_fine",
        ),
        (
            "Mức phạt vượt đèn đỏ là bao nhiêu?",
            "legal_fine",
        ),

        (
            "Quy định về đội mũ bảo hiểm?",
            "legal_general",
        ),
        (
            "Giấy phép lái xe có những quy định gì?",
            "legal_general",
        ),

        ("Thời tiết hôm nay?", "out_of_scope"),
        ("Cách nấu cơm", "out_of_scope"),

        ("", "empty"),
        ("   ", "empty"),
    ],
)
def test_intent_detection(detector, question, expected):
    assert detector.detect(question) == expected


class FakeRetriever:
    def __init__(self):
        self.call_count = 0

    def retrieve(self, question, top_k=5):
        self.call_count += 1
        return []


def test_greeting_does_not_call_retriever():
    retriever = FakeRetriever()
    pipeline = QueryPipeline(retriever=retriever)

    result = pipeline.run("xin chào")

    assert result["intent"] == "greeting"
    assert result["retrieved_chunks"] == 0
    assert result["citations"] == []
    assert retriever.call_count == 0


def test_out_of_scope_does_not_call_retriever():
    retriever = FakeRetriever()
    pipeline = QueryPipeline(retriever=retriever)

    result = pipeline.run("Thời tiết hôm nay?")

    assert result["intent"] == "out_of_scope"
    assert retriever.call_count == 0


def test_legal_question_calls_retriever():
    retriever = FakeRetriever()
    pipeline = QueryPipeline(retriever=retriever)

    result = pipeline.run(
        "Xe máy vượt đèn đỏ bị phạt bao nhiêu?"
    )

    assert result["intent"] == "legal_fine"
    assert retriever.call_count == 1
    assert result["retrieved_chunks"] == 0


def test_empty_question_raises_error():
    retriever = FakeRetriever()
    pipeline = QueryPipeline(retriever=retriever)

    with pytest.raises(ValueError):
        pipeline.run("   ")

    assert retriever.call_count == 0