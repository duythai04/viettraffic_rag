from src.query.clarification_detector import (
    ClarificationDetector,
)


def test_missing_speed_excess():
    detector = ClarificationDetector()

    result = detector.detect(
        "Xe máy chạy quá tốc độ bị phạt bao nhiêu?"
    )

    assert result["requires_clarification"] is True
    assert result["reason"] == "missing_speed_excess"


def test_speed_excess_provided():
    detector = ClarificationDetector()

    result = detector.detect(
        "Xe máy vượt tốc độ 10 km/h bị phạt bao nhiêu?"
    )

    assert result["requires_clarification"] is False


def test_unrelated_question():
    detector = ClarificationDetector()

    result = detector.detect(
        "Ô tô vượt đèn đỏ bị phạt bao nhiêu?"
    )

    assert result["requires_clarification"] is False
