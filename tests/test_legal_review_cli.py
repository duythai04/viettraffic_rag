import json
import pytest
from scripts.legal_review_cli import atomic_write, load_array, save_review
from src.validation.evidence_verifier import EvidenceVerifier


def valid_record():
    return {
        "clause_id": "168-2024-ND-CP_dieu-12_khoan-10",
        "fine_ranges": [{"min_vnd": 100000, "max_vnd": 200000, "recipient": "individual"}],
        "source_reference": "Điều 12 khoản 10", "source_document": "Văn bản kiểm thử",
        "verified_by": "Người kiểm thử", "verification_note": "Dữ liệu giả lập để test",
        "effective_from": "2025-01-01", "effective_to": None, "review_confirmed": False,
    }


def test_load_missing_output_is_empty(tmp_path):
    assert load_array(tmp_path / "missing.json") == []


def test_required_queue_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_array(tmp_path / "missing.json", required=True)


def test_reject_non_array(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_array(path)


def test_atomic_write_unicode(tmp_path):
    path = tmp_path / "output.json"
    atomic_write(path, [{"note": "đối chiếu"}])
    assert json.loads(path.read_text(encoding="utf-8"))[0]["note"] == "đối chiếu"


def test_save_review_and_prevent_duplicate(tmp_path):
    output = tmp_path / "reviewed.json"
    verifier = EvidenceVerifier()
    assert save_review(valid_record(), output, verifier)
    assert load_array(output)[0]["review_confirmed"] is True
    assert not save_review(valid_record(), output, verifier)
    assert len(load_array(output)) == 1


def test_invalid_review_not_saved(tmp_path):
    output = tmp_path / "reviewed.json"
    record = valid_record()
    record["effective_from"] = "not-a-date"
    assert not save_review(record, output, EvidenceVerifier())
    assert not output.exists()
