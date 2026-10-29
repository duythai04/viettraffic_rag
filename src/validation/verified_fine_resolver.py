import json
from datetime import date
from pathlib import Path

from src.validation.evidence_verifier import EvidenceVerifier


class VerifiedFineResolver:
    def __init__(
        self,
        path="data/verified/reviewed_fines.json",
    ):
        self.path = Path(path)
        self.verifier = EvidenceVerifier()

    def resolve(
        self,
        clause_id: str,
        recipient: str | None = None,
        as_of: str | None = None,
    ):
        if not self.path.exists():
            return None

        try:
            records = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return None

        if not isinstance(records, list):
            return None

        try:
            target_date = (
                date.fromisoformat(as_of)
                if as_of is not None
                else date.today()
            )
        except ValueError:
            return None

        matches = []

        for record in records:
            if not isinstance(record, dict):
                continue

            if record.get("clause_id") != clause_id:
                continue

            result = self.verifier.validate(record)

            if not result["valid"]:
                continue

            start = date.fromisoformat(
                record["effective_from"]
            )

            end_value = record.get("effective_to")
            end = (
                date.fromisoformat(end_value)
                if end_value
                else None
            )

            if target_date < start:
                continue

            if end is not None and target_date > end:
                continue

            matches.append(record)

        # Không tự lựa chọn giữa các hồ sơ xung đột.
        if len(matches) != 1:
            return None

        record = matches[0]

        fines = record["fine_ranges"]

        if recipient is not None:
            fines = [
                fine for fine in fines
                if fine["recipient"] == recipient
            ]

        if not fines:
            return None

        return {
            "clause_id": clause_id,
            "fine_ranges": fines,
            "source_reference": record["source_reference"],
            "source_document": record["source_document"],
            "verified_by": record["verified_by"],
            "effective_from": record["effective_from"],
            "effective_to": record.get("effective_to"),
            "status": "review_confirmed",
        }