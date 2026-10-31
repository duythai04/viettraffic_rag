from src.evidence.fine_evidence_enricher import (
    FineEvidenceEnricher,
)


CHUNK_ID = (
    "168-2024-ND-CP_dieu-7_khoan-4_diem-a"
)


def make_context():
    return {
        "chunk_id": CHUNK_ID,
        "citation": "Điểm a Khoản 4 Điều 7",
        "content": (
            "Điều khiển xe chạy quá tốc độ quy định "
            "từ 10 km/h đến 20 km/h;"
        ),
    }


def test_motorcycle_speed_15():
    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        make_context(),
    )

    assert result["vehicle_type"] == "motorcycle"
    assert result["role"] == "driver"
    assert result["violation_key"] == "speed_10_to_20"
    assert result["clause_id"] == (
        "168-2024-ND-CP_dieu-7_khoan-4"
    )


def test_motorcycle_speed_10():
    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 10 km/h bị phạt bao nhiêu?",
        make_context(),
    )

    assert result["violation_key"] == "speed_10_to_20"


def test_motorcycle_speed_20():
    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 20 km/h bị phạt bao nhiêu?",
        make_context(),
    )

    assert result["violation_key"] == "speed_10_to_20"


def test_motorcycle_speed_25():
    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 25 km/h bị phạt bao nhiêu?",
        make_context(),
    )

    assert "violation_key" not in result


def test_car_not_enriched():
    result = FineEvidenceEnricher.enrich(
        "Ô tô vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        make_context(),
    )

    assert "violation_key" not in result


def test_wrong_chunk_not_enriched():
    context = make_context()

    context["chunk_id"] = (
        "168-2024-ND-CP_dieu-7_khoan-2_diem-b"
    )

    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        context,
    )

    assert "violation_key" not in result


def test_wrong_vehicle_metadata_not_overwritten():
    context = make_context()
    context["vehicle_type"] = "car"

    result = FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        context,
    )

    assert result["vehicle_type"] == "car"
    assert "violation_key" not in result


def test_missing_speed_not_enriched():
    result = FineEvidenceEnricher.enrich(
        "Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        make_context(),
    )

    assert "violation_key" not in result


def test_original_context_not_modified():
    context = make_context()

    FineEvidenceEnricher.enrich(
        "Xe máy vượt tốc độ 15 km/h bị phạt bao nhiêu?",
        context,
    )

    assert "violation_key" not in context
