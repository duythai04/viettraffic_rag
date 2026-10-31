from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from src.validation.evidence_verifier import EvidenceVerifier


PENDING = Path("data/verified/pending/speed_10_to_20.json")
REVIEWED = Path("data/verified/reviewed_fines.json")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--reviewer",
        required=True,
        help="Tên người thực sự kiểm duyệt hồ sơ",
    )

    parser.add_argument(
        "--note",
        required=True,
        help="Ghi chú về nguồn và việc kiểm tra hiệu lực",
    )

    args = parser.parse_args()

    reviewer = args.reviewer.strip()
    note = args.note.strip()

    if not reviewer or not note:
        raise SystemExit(
            "Reviewer và ghi chú kiểm duyệt không được để trống."
        )

    candidates = json.loads(
        PENDING.read_text(encoding="utf-8")
    )

    if len(candidates) != 1:
        raise SystemExit(
            "Cần đúng một hồ sơ ứng viên."
        )

    record = candidates[0].copy()

    print("Hồ sơ chuẩn bị phê duyệt:")
    print(json.dumps(
        record,
        ensure_ascii=False,
        indent=2,
    ))

    confirmation = input(
        "\nBạn đã tự đối chiếu số tiền, căn cứ và "
        "hiệu lực pháp luật? Nhập APPROVE: "
    )

    if confirmation != "APPROVE":
        raise SystemExit("Đã hủy phê duyệt.")

    record["verified_by"] = reviewer
    record["verification_note"] = (
        f"{note} | Reviewed on {date.today().isoformat()}"
    )
    record["review_confirmed"] = True

    verifier = EvidenceVerifier()
    result = verifier.validate(record)

    if not result["valid"]:
        raise SystemExit(
            f"Hồ sơ không hợp lệ: {result['issues']}"
        )

    if REVIEWED.exists():
        records = json.loads(
            REVIEWED.read_text(encoding="utf-8")
        )
    else:
        records = []

    if not isinstance(records, list):
        raise SystemExit("reviewed_fines.json không hợp lệ.")

    for existing in records:
        if existing.get("chunk_id") == record["chunk_id"]:
            raise SystemExit(
                "Đã có hồ sơ cho chunk này. "
                "Không tự động ghi đè."
            )

    records.append(record)

    REVIEWED.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REVIEWED.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nĐã lưu hồ sơ vào:", REVIEWED)


if __name__ == "__main__":
    main()
