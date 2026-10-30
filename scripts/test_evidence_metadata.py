from src.evidence.legal_evidence_selector import (
    LegalEvidenceSelector,
)


def make_context(
    chunk_id: str,
    content: str,
    vehicle_type: str = "motorcycle",
) -> dict:
    return {
        "chunk_id": chunk_id,
        "vehicle_type": vehicle_type,
        "content": content,
        "retrieval_score": 0.08,
    }


def main():
    selector = LegalEvidenceSelector()

    contexts = [
        make_context(
            "168-2024-ND-CP_dieu-7_khoan-2_diem-h",
            (
                "Không đội mũ bảo hiểm khi điều khiển "
                "xe tham gia giao thông."
            ),
        ),
        make_context(
            "168-2024-ND-CP_dieu-7_khoan-2_diem-i",
            (
                "Chở người ngồi trên xe không đội "
                "mũ bảo hiểm."
            ),
        ),
        make_context(
            "168-2024-ND-CP_dieu-12_khoan-5_diem-b",
            (
                "Người được chở không đội mũ bảo hiểm."
            ),
        ),
    ]

    tests = [
        {
            "question": (
                "Người điều khiển xe máy không đội "
                "mũ bảo hiểm bị phạt bao nhiêu?"
            ),
            "expected": "helmet_driver",
        },
        {
            "question": (
                "Người lái xe máy chở người ngồi sau "
                "không đội mũ bảo hiểm bị phạt bao nhiêu?"
            ),
            "expected": (
                "helmet_driver_responsible_for_passenger"
            ),
        },
        {
            "question": (
                "Người ngồi sau xe máy không đội "
                "mũ bảo hiểm bị phạt bao nhiêu?"
            ),
            "expected": "helmet_passenger",
        },
    ]

    for test in tests:
        result = selector.select(
            question=test["question"],
            contexts=contexts,
        )

        selected = result["selected_evidence"]

        assert selected, (
            "No evidence selected: "
            + test["question"]
        )

        best = selected[0]

        print("\nQuestion:", test["question"])
        print("Citation:", best.get("chunk_id"))
        print("Role:", best.get("role"))
        print(
            "Violation Key:",
            best.get("violation_key"),
        )

        assert (
            best["violation_key"]
            == test["expected"]
        ), (
            f"Expected {test['expected']}, "
            f"got {best['violation_key']}"
        )

    print(
        "\nPASS: All evidence metadata tests passed."
    )


if __name__ == "__main__":
    main()
