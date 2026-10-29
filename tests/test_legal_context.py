from src.context.legal_chunk_index import LegalChunkIndex
from src.context.fine_extractor import FineExtractor
from src.context.legal_context_reconstructor import (
    LegalContextReconstructor,
)


# ============================================================
# TEST DATA
# ============================================================

def build_test_chunks():
    """
    Dữ liệu giả lập để kiểm thử Legal Context Reconstruction.
    Các mức phạt chỉ phục vụ unit test, không phải dữ liệu pháp lý đã xác minh.
    """
    return [
        {
            "chunk_id": "168-2024-ND-CP_dieu-7_khoan-7",
            "text": (
                "Phạt tiền từ 4.000.000 đồng "
                "đến 6.000.000 đồng đối với "
                "người điều khiển xe thực hiện "
                "một trong các hành vi sau đây:"
            ),
        },
        {
            "chunk_id": (
                "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
            ),
            "text": (
                "Không chấp hành hiệu lệnh "
                "của đèn tín hiệu giao thông;"
            ),
        },
        {
            "chunk_id": (
                "168-2024-ND-CP_dieu-7_khoan-7_diem-d"
            ),
            "text": (
                "Không chấp hành hiệu lệnh "
                "của người điều khiển giao thông;"
            ),
        },
    ]


# ============================================================
# 1. LEGAL CHUNK INDEX TESTS
# ============================================================

def test_parse_chunk_id():
    """Kiểm tra phân tích chunk_id."""

    result = LegalChunkIndex.parse_chunk_id(
        "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
    )

    assert result["document_id"] == "168-2024-ND-CP"
    assert result["article"] == 7
    assert result["clause"] == 7
    assert result["point"] == "c"


# ============================================================
# 2. FINE EXTRACTOR TESTS
# ============================================================

def test_fine_extractor():
    """Kiểm tra trích xuất mức phạt thông thường."""

    extractor = FineExtractor()

    result = extractor.extract(
        "Phạt tiền từ 4.000.000 đồng "
        "đến 6.000.000 đồng"
    )

    assert result is not None
    assert result["min_vnd"] == 4000000
    assert result["max_vnd"] == 6000000


def test_fine_extractor_ocr_dot():
    """Kiểm tra lỗi OCR: Phạt.tiền."""

    extractor = FineExtractor()

    result = extractor.extract(
        "Phạt.tiền từ 150.000 đồng đến 250.000 đồng"
    )

    assert result is not None
    assert result["min_vnd"] == 150000
    assert result["max_vnd"] == 250000


def test_fine_extractor_missing_accents():
    """Kiểm tra lỗi OCR: Phat tiền."""

    extractor = FineExtractor()

    result = extractor.extract(
        "Phat tiền từ 6.000.000 đồng đến 8.000.000 đồng"
    )

    assert result is not None
    assert result["min_vnd"] == 6000000
    assert result["max_vnd"] == 8000000


def test_fine_extractor_rejects_broken_amount():
    """Không tự động sửa mức phạt có chữ số bị ngắt dòng."""

    extractor = FineExtractor()

    result = extractor.extract(
        "Phạt tiền từ 800.000 đồng đến 1.000.000\n0\nđồng"
    )

    assert result is None


def test_fine_extractor_rejects_reversed_range():
    """Từ chối khoảng tiền phạt có min > max."""

    extractor = FineExtractor()

    result = extractor.extract(
        "Phạt tiền từ 8.000.000 đồng đến 6.000.000 đồng"
    )

    assert result is None


# ============================================================
# 3. LEGAL CONTEXT RECONSTRUCTION TESTS
# ============================================================

def test_reconstruct_with_parent():
    """Kiểm tra tái tạo ngữ cảnh khi có khoản cha."""

    index = LegalChunkIndex(
        build_test_chunks()
    )

    reconstructor = LegalContextReconstructor(
        index
    )

    result = reconstructor.reconstruct(
        "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
    )

    assert result["parent_found"] is True
    assert result["fine"] is not None
    assert result["fine"]["min_vnd"] == 4000000
    assert result["fine"]["max_vnd"] == 6000000


def test_reconstruct_without_parent():
    """Kiểm tra trường hợp không tìm thấy khoản cha."""

    chunks = [
        {
            "chunk_id": (
                "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
            ),
            "text": (
                "Không chấp hành hiệu lệnh "
                "của đèn tín hiệu giao thông;"
            ),
        },
    ]

    index = LegalChunkIndex(chunks)

    reconstructor = LegalContextReconstructor(
        index
    )

    result = reconstructor.reconstruct(
        "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
    )

    assert result["parent_found"] is False
    assert result["fine"] is None


def test_reconstruct_many():
    """Kiểm tra tái tạo ngữ cảnh cho nhiều chunks."""

    index = LegalChunkIndex(
        build_test_chunks()
    )

    reconstructor = LegalContextReconstructor(
        index
    )

    results = reconstructor.reconstruct_many([
        {
            "chunk_id": (
                "168-2024-ND-CP_dieu-7_khoan-7_diem-c"
            ),
            "adjusted_score": 0.05,
        },
    ])

    assert len(results) == 1
    assert results[0]["retrieval_score"] == 0.05
    assert results[0]["fine"] is not None
    assert results[0]["fine"]["min_vnd"] == 4000000