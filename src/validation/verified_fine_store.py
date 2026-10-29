

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


class VerifiedFineStore:
    """
    Lưu mức phạt đã được kiểm duyệt.

    Không tự động xác minh từ OCR.
    Không tự động ghi đè bản ghi đã xác minh.
    """

    CLAUSE_ID_RE = re.compile(
        r"^.+_dieu-\d+_khoan-\d+$"
    )

    def __init__(
        self,
        path: str = (
            "data/verified/verified_fines.json"
        ),
    ):
        self.path = Path(path)
        self.records = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                "Verified Fine Store phải là JSON object"
            )

        return data

    def _save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Ghi vào file tạm rồi thay thế để hạn chế
        # nguy cơ làm hỏng dữ liệu khi ghi.
        temp_path = self.path.with_suffix(
            ".json.tmp"
        )

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.records,
                f,
                ensure_ascii=False,
                indent=2,
            )

        temp_path.replace(self.path)

    def add_verified(
        self,
        clause_id: str,
        fine_ranges: list[dict],
        source_reference: str,
        verified_by: str,
        source_document: str,
        verification_note: str,
    ) -> dict:
        """
        Chỉ ghi dữ liệu sau khi người kiểm duyệt
        đã đối chiếu với văn bản pháp luật.

        source_reference: vị trí cụ thể trong nguồn.
        source_document: tài liệu hoặc URL nguồn.
        """

        if not self.CLAUSE_ID_RE.fullmatch(clause_id):
            raise ValueError(
                "clause_id không hợp lệ"
            )

        if clause_id in self.records:
            raise ValueError(
                "Khoản đã được xác minh. "
                "Không được ghi đè tự động."
            )

        required_strings = {
            "source_reference": source_reference,
            "verified_by": verified_by,
            "source_document": source_document,
            "verification_note": verification_note,
        }

        for name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Thiếu thông tin: {name}"
                )

        if not fine_ranges:
            raise ValueError(
                "fine_ranges không được rỗng"
            )

        allowed_recipients = {
            "individual",
            "organization",
            "driver",
            "other",
        }

        normalized_ranges = []

        for fine in fine_ranges:
            minimum = fine.get("min_vnd")
            maximum = fine.get("max_vnd")
            recipient = fine.get("recipient")

            if (
                type(minimum) is not int
                or type(maximum) is not int
                or minimum <= 0
                or maximum < minimum
            ):
                raise ValueError(
                    "Khoảng tiền phạt không hợp lệ"
                )

            if recipient not in allowed_recipients:
                raise ValueError(
                    "Đối tượng áp dụng không hợp lệ"
                )

            normalized_ranges.append({
                "min_vnd": minimum,
                "max_vnd": maximum,
                "recipient": recipient,
            })

        record = {
            "clause_id": clause_id,
            "fine_ranges": normalized_ranges,
            "status": "verified",
            "source_reference": source_reference,
            "source_document": source_document,
            "verified_by": verified_by,
            "verification_note": verification_note,
            "verified_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self.records[clause_id] = record
        self._save()

        return record

    def get(self, clause_id: str) -> dict | None:
        return self.records.get(clause_id)

    def is_verified(self, clause_id: str) -> bool:
        record = self.get(clause_id)

        return bool(
            record
            and record.get("status") == "verified"
        )

    def list_verified(self) -> list[dict]:
        return list(self.records.values())