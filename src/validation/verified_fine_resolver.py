"""
Resolve human-reviewed traffic fine records.

Safety rules:
- Never use unverified OCR fine amounts.
- Require an exact legal evidence match.
- Require vehicle, role and violation metadata.
- Respect effective dates.
- Reject ambiguous or conflicting records.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from src.validation.evidence_verifier import (
    EvidenceVerifier,
)


class VerifiedFineResolver:

    def __init__(
        self,
        path: str = "data/verified/reviewed_fines.json",
    ):
        self.path = Path(path)

        self.verifier = EvidenceVerifier()

    def _load_records(self) -> list[dict]:

        if not self.path.exists():
            return []

        try:
            content = self.path.read_text(
                encoding="utf-8"
            )

            records = json.loads(content)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

        if not isinstance(records, list):
            return []

        return [
            record
            for record in records
            if isinstance(record, dict)
        ]

    @staticmethod
    def _parse_target_date(
        as_of: str | None,
    ) -> date | None:

        if as_of is None:
            return date.today()

        try:
            return date.fromisoformat(as_of)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _is_effective(
        record: dict,
        target_date: date,
    ) -> bool:

        try:
            start = date.fromisoformat(
                record["effective_from"]
            )

            end_value = record.get(
                "effective_to"
            )

            end = (
                date.fromisoformat(end_value)
                if end_value is not None
                else None
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return False

        if target_date < start:
            return False

        if (
            end is not None
            and target_date > end
        ):
            return False

        return True

    @staticmethod
    def _matches_evidence(
        record: dict,
        clause_id: str,
        chunk_id: str,
        vehicle_type: str,
        role: str,
        violation_key: str,
    ) -> bool:

        expected = {
            "clause_id": clause_id,
            "chunk_id": chunk_id,
            "vehicle_type": vehicle_type,
            "role": role,
            "violation_key": violation_key,
        }

        for key, value in expected.items():

            if record.get(key) != value:
                return False

        return True

    @staticmethod
    def _filter_fines(
        record: dict,
        recipient: str | None,
    ) -> list[dict]:

        fines = record.get(
            "fine_ranges",
            [],
        )

        if recipient is None:
            return list(fines)

        return [
            fine
            for fine in fines
            if fine.get("recipient") == recipient
        ]

    def resolve(
        self,
        clause_id: str,
        recipient: str | None = None,
        as_of: str | None = None,
        *,
        chunk_id: str | None = None,
        vehicle_type: str | None = None,
        role: str | None = None,
        violation_key: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Return a reviewed fine only when all required
        evidence metadata matches exactly.

        Backward compatibility:
        Existing calls with only clause_id, recipient
        and as_of remain syntactically valid, but
        return None because the evidence is incomplete.
        """

        required_values = (
            clause_id,
            chunk_id,
            vehicle_type,
            role,
            violation_key,
        )

        if any(
            not isinstance(value, str)
            or not value.strip()
            for value in required_values
        ):
            return None

        target_date = self._parse_target_date(
            as_of
        )

        if target_date is None:
            return None

        records = self._load_records()

        matches = []

        for record in records:

            verification = self.verifier.validate(
                record
            )

            if not verification["valid"]:
                continue

            if not self._matches_evidence(
                record=record,
                clause_id=clause_id,
                chunk_id=chunk_id,
                vehicle_type=vehicle_type,
                role=role,
                violation_key=violation_key,
            ):
                continue

            if not self._is_effective(
                record,
                target_date,
            ):
                continue

            matches.append(record)

        # Do not select between ambiguous records.
        if len(matches) != 1:
            return None

        record = matches[0]

        fines = self._filter_fines(
            record=record,
            recipient=recipient,
        )

        if not fines:
            return None

        return {
            "clause_id": record["clause_id"],
            "chunk_id": record["chunk_id"],
            "vehicle_type": record["vehicle_type"],
            "role": record["role"],
            "violation_key": record["violation_key"],
            "fine_ranges": fines,
            "source_reference": record["source_reference"],
            "source_document": record["source_document"],
            "verified_by": record["verified_by"],
            "verification_note": record["verification_note"],
            "effective_from": record["effective_from"],
            "effective_to": record.get("effective_to"),
            "review_confirmed": True,
            "status": "review_confirmed",
        }