

import pytest

from src.validation.ocr_auditor import OCRAuditor
from src.validation.verified_fine_store import (
    VerifiedFineStore,
)


def make_chunk(
    point: str,
    preamble: str,
):
    return {
        "chunk_id": (
            "168-2024-ND-CP_dieu-7_khoan-7_"
            f"diem-{point}"
        ),
        "content": f"Hành vi vi phạm điểm {point}",
        "clause_preamble": preamble,
    }


def test_group_chunks_by_clause():
    preamble = (
        "Phạt tiền từ 4.000.000 đồng "
        "đến 6.000.000 đồng"
    )

    chunks = [
        make_chunk("a", preamble),
        make_chunk("b", preamble),
        make_chunk("c", preamble),
    ]

    report = OCRAuditor().audit(chunks)

    assert report["summary"]["total_chunks"] == 3
    assert report["summary"]["total_clauses"] == 1

    record = report["records"][0]

    assert record["chunk_count"] == 3
    assert record["status"] == "extracted_unverified"
    assert record["verified"] is False


def test_detect_suspicious_ocr():
    chunks = [
        make_chunk(
            "a",
            "Phạt tiền từ 500.000 đồng "
            "đến 1. 000.000 đồng",
        )
    ]

    report = OCRAuditor().audit(chunks)

    record = report["records"][0]

    assert record["status"] == "suspicious_ocr"


def test_detect_conflicting_preambles():
    chunks = [
        make_chunk(
            "a",
            "Phạt tiền từ 100.000 đồng "
            "đến 200.000 đồng",
        ),
        make_chunk(
            "b",
            "Phạt tiền từ 300.000 đồng "
            "đến 400.000 đồng",
        ),
    ]

    report = OCRAuditor().audit(chunks)

    record = report["records"][0]

    assert record["status"] == "suspicious_ocr"
    assert (
        "conflicting_clause_preambles"
        in record["issues"]
    )


def test_verified_store(tmp_path):
    path = tmp_path / "verified_fines.json"

    store = VerifiedFineStore(str(path))

    clause_id = (
        "168-2024-ND-CP_dieu-7_khoan-7"
    )

    # Dữ liệu giả lập cho unit test.
    store.add_verified(
        clause_id=clause_id,
        fine_ranges=[
            {
                "min_vnd": 100000,
                "max_vnd": 200000,
                "recipient": "driver",
            }
        ],
        source_reference="Nguồn kiểm thử, khoản 7",
        source_document="test-fixture",
        verified_by="test-reviewer",
        verification_note="Dữ liệu giả lập",
    )

    assert store.is_verified(clause_id)

    record = store.get(clause_id)

    assert record["status"] == "verified"
    assert record["fine_ranges"][0]["min_vnd"] == 100000

    # Kiểm tra khả năng đọc lại từ ổ đĩa.
    reloaded = VerifiedFineStore(str(path))
    assert reloaded.is_verified(clause_id)


def test_verified_store_rejects_invalid_range(tmp_path):
    store = VerifiedFineStore(
        str(tmp_path / "verified_fines.json")
    )

    with pytest.raises(ValueError):
        store.add_verified(
            clause_id="168-2024-ND-CP_dieu-7_khoan-7",
            fine_ranges=[
                {
                    "min_vnd": 300000,
                    "max_vnd": 100000,
                    "recipient": "driver",
                }
            ],
            source_reference="Test",
            source_document="test-fixture",
            verified_by="test-reviewer",
            verification_note="Dữ liệu giả lập",
        )


def test_verified_store_rejects_overwrite(tmp_path):
    store = VerifiedFineStore(
        str(tmp_path / "verified_fines.json")
    )

    kwargs = {
        "clause_id": "168-2024-ND-CP_dieu-7_khoan-7",
        "fine_ranges": [
            {
                "min_vnd": 100000,
                "max_vnd": 200000,
                "recipient": "driver",
            }
        ],
        "source_reference": "Test",
        "source_document": "test-fixture",
        "verified_by": "test-reviewer",
        "verification_note": "Dữ liệu giả lập",
    }

    store.add_verified(**kwargs)

    with pytest.raises(ValueError):
        store.add_verified(**kwargs)