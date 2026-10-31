from src.evidence.speed_range_validator import SpeedRangeValidator
from src.evidence.legal_evidence_selector import LegalEvidenceSelector


def test_extract_query_speed():
    validator = SpeedRangeValidator()

    question = (
        "Xe máy chạy quá tốc độ bị phạt bao nhiêu? "
        "Mức vượt quá tốc độ cho phép là 15 km/h."
    )

    assert validator.extract_query_speed(question) == 15.0


def test_speed_15_rejects_5_to_10():
    validator = SpeedRangeValidator()

    content = (
        "Điều khiển xe chạy quá tốc độ quy định "
        "từ 05 km/h đến dưới 10 km/h."
    )

    assert validator.validate(15, content) is False


def test_speed_7_matches_5_to_10():
    validator = SpeedRangeValidator()

    content = (
        "Điều khiển xe chạy quá tốc độ quy định "
        "từ 05 km/h đến dưới 10 km/h."
    )

    assert validator.validate(7, content) is True


def test_speed_15_matches_10_to_20():
    validator = SpeedRangeValidator()

    content = (
        "Điều khiển xe chạy quá tốc độ quy định "
        "từ 10 km/h đến 20 km/h."
    )

    assert validator.validate(15, content) is True


def test_speed_20_matches_inclusive_upper_bound():
    validator = SpeedRangeValidator()

    content = (
        "Điều khiển xe chạy quá tốc độ quy định "
        "từ 10 km/h đến 20 km/h."
    )

    assert validator.validate(20, content) is True


def test_speed_35_matches_above_20():
    validator = SpeedRangeValidator()

    content = (
        "Điều khiển xe chạy quá tốc độ quy định "
        "trên 20 km/h."
    )

    assert validator.validate(35, content) is True


def test_unknown_speed_range_rejected():
    validator = SpeedRangeValidator()

    content = "Vi phạm quy định về tốc độ."

    assert validator.validate(15, content) is False


def test_evidence_selector_rejects_wrong_speed_range():
    selector = LegalEvidenceSelector()

    contexts = [
        {
            "chunk_id": "speed_5_10",
            "vehicle_type": "motorcycle",
            "content": (
                "Điều khiển xe chạy quá tốc độ quy định "
                "từ 05 km/h đến dưới 10 km/h."
            ),
            "retrieval_score": 0.9,
        },
        {
            "chunk_id": "speed_10_20",
            "vehicle_type": "motorcycle",
            "content": (
                "Điều khiển xe chạy quá tốc độ quy định "
                "từ 10 km/h đến 20 km/h."
            ),
            "retrieval_score": 0.8,
        },
    ]

    result = selector.select(
        question="Xe máy vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        contexts=contexts,
    )

    selected_ids = [
        item["chunk_id"]
        for item in result["selected_evidence"]
    ]

    assert "speed_5_10" not in selected_ids
    assert "speed_10_20" in selected_ids
    assert result["query_speed_excess"] == 15.0