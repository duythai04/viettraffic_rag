from src.validation.evidence_verifier import EvidenceVerifier


def example():
    return {
        "clause_id": "168-2024-ND-CP_dieu-7_khoan-7",
        "fine_ranges": [{"min_vnd": 100000, "max_vnd": 200000, "recipient": "driver"}],
        "source_reference": "Fixture, clause 7",
        "source_document": "test-fixture",
        "verified_by": "test-reviewer",
        "verification_note": "Test fixture only; not a real legal finding",
        "effective_from": "2025-01-01",
        "effective_to": None,
        "review_confirmed": True,
    }


def test_valid_fixture():
    assert EvidenceVerifier().validate(example())["valid"] is True


def test_requires_explicit_human_confirmation():
    item = example()
    item["review_confirmed"] = False
    assert "human_review_not_confirmed" in EvidenceVerifier().validate(item)["issues"]


def test_rejects_invalid_amount():
    item = example()
    item["fine_ranges"][0]["max_vnd"] = 1
    assert "invalid_amount_0" in EvidenceVerifier().validate(item)["issues"]


def test_rejects_missing_source():
    item = example()
    item["source_document"] = ""
    assert "invalid_source_document" in EvidenceVerifier().validate(item)["issues"]


def test_rejects_invalid_period():
    item = example()
    item["effective_to"] = "2024-01-01"
    assert "invalid_effective_period" in EvidenceVerifier().validate(item)["issues"]


def test_rejects_invalid_recipient():
    item = example()
    item["fine_ranges"][0]["recipient"] = "unknown"
    assert "invalid_recipient_0" in EvidenceVerifier().validate(item)["issues"]
