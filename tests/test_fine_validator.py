import pytest
from src.validation.fine_validator import FineValidator


@pytest.fixture
def validator():
    return FineValidator()


def test_single_fine(validator):
    r = validator.validate("Phạt tiền từ 150.000 đồng đến 250.000 đồng")
    assert r["status"] == "extracted_unverified"
    assert r["fine_ranges"][0]["min_vnd"] == 150000
    assert r["verified"] is False


def test_multiple_fines(validator):
    text = ("Phạt tiền từ 500.000 đồng đến 1.000.000 đồng đối với cá nhân, "
            "từ 1.000.000 đồng đến 2.000.000 đồng đối với tổ chức")
    r = validator.validate(text)
    assert r["status"] == "multiple_fines"
    assert len(r["fine_ranges"]) == 2
    assert [x["recipient_hint"] for x in r["fine_ranges"]] == ["individual", "organization"]


def test_broken_separator(validator):
    r = validator.validate("Phạt tiền từ 500.000 đồng đến 1. 000.000 đồng")
    assert r["status"] == "suspicious_ocr"


def test_stray_digit(validator):
    r = validator.validate("Phạt tiền từ 800.000 đồng đến 1.000.000\n0\nđồng")
    assert r["status"] == "suspicious_ocr"


def test_non_monetary(validator):
    r = validator.validate("Ngoài việc bị phạt tiền, người điều khiển xe còn bị áp dụng các hình thức xử phạt bổ sung")
    assert r["status"] == "non_monetary_penalty"


def test_missing(validator):
    assert validator.validate("Không chấp hành đèn tín hiệu giao thông")["status"] == "fine_not_found"


def test_invalid_range(validator):
    assert validator.validate("Phạt tiền từ 8.000.000 đồng đến 6.000.000 đồng")["status"] == "suspicious_ocr"


def test_ocr_text_labels(validator):
    assert validator.validate("Phạt.tiền từ 150.000 đồng đến 250.000 đồng")["status"] == "extracted_unverified"

