"""
Validate the structure and consistency of human-reviewed
legal fine records.

IMPORTANT:
This module does NOT independently verify legal truth.
A valid record only means its metadata and review fields
meet the required schema.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any


CLAUSE_ID_PATTERN = re.compile(
    r"^.+_dieu-\d+_khoan-\d+$"
)

CHUNK_ID_PATTERN = re.compile(
    r"^.+_dieu-\d+_khoan-\d+(?:_diem-[a-zđ])?$",
    re.IGNORECASE,
)

VIOLATION_KEY_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)

RECIPIENTS = {
    "individual",
    "organization",
    "driver",
    "passenger",
    "other",
}

VEHICLE_TYPES = {
    "motorcycle",
    "car",
    "bicycle",
    "pedestrian",
    "specialized_vehicle",
    "other",
}

ROLES = {
    "driver",
    "driver_responsible_for_passenger",
    "passenger",
    "pedestrian",
    "owner",
    "organization",
    "other",
}


class EvidenceVerifier:
    """
    Validate human-reviewed legal fine records.

    This validator checks:
        - Required fields
        - Legal evidence identifiers
        - Vehicle and role metadata
        - Fine ranges
        - Effective dates
        - Human review metadata

    It does not establish that the legal interpretation
    or monetary amount is legally correct.
    """

    REQUIRED_FIELDS = (
        "clause_id",
        "chunk_id",
        "vehicle_type",
        "role",
        "violation_key",
        "fine_ranges",
        "source_reference",
        "source_document",
        "verified_by",
        "verification_note",
        "review_confirmed",
        "effective_from",
    )

    @staticmethod
    def _is_non_empty_string(value: Any) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None

        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _validate_identifiers(
        self,
        record: dict,
        issues: list[str],
    ) -> None:

        clause_id = record.get("clause_id")
        chunk_id = record.get("chunk_id")

        if (
            not isinstance(clause_id, str)
            or not CLAUSE_ID_PATTERN.fullmatch(clause_id)
        ):
            issues.append("invalid_clause_id")

        if (
            not isinstance(chunk_id, str)
            or not CHUNK_ID_PATTERN.fullmatch(chunk_id)
        ):
            issues.append("invalid_chunk_id")

        if (
            isinstance(clause_id, str)
            and isinstance(chunk_id, str)
            and CLAUSE_ID_PATTERN.fullmatch(clause_id)
            and CHUNK_ID_PATTERN.fullmatch(chunk_id)
        ):
            if (
                chunk_id != clause_id
                and not chunk_id.startswith(
                    clause_id + "_diem-"
                )
            ):
                issues.append(
                    "chunk_id_clause_id_mismatch"
                )

    def _validate_metadata(
        self,
        record: dict,
        issues: list[str],
    ) -> None:

        vehicle_type = record.get("vehicle_type")

        if vehicle_type not in VEHICLE_TYPES:
            issues.append("invalid_vehicle_type")

        role = record.get("role")

        if role not in ROLES:
            issues.append("invalid_role")

        violation_key = record.get("violation_key")

        if (
            not isinstance(violation_key, str)
            or not VIOLATION_KEY_PATTERN.fullmatch(
                violation_key
            )
        ):
            issues.append("invalid_violation_key")

    def _validate_source(
        self,
        record: dict,
        issues: list[str],
    ) -> None:

        fields = (
            "source_reference",
            "source_document",
            "verified_by",
            "verification_note",
        )

        for field in fields:
            if not self._is_non_empty_string(
                record.get(field)
            ):
                issues.append(f"invalid_{field}")

        if record.get("review_confirmed") is not True:
            issues.append(
                "human_review_not_confirmed"
            )

    def _validate_dates(
        self,
        record: dict,
        issues: list[str],
    ) -> None:

        start_value = record.get("effective_from")
        end_value = record.get("effective_to")

        start = self._parse_date(start_value)

        if start is None:
            issues.append("invalid_effective_from")

        end = None

        if end_value is not None:
            end = self._parse_date(end_value)

            if end is None:
                issues.append("invalid_effective_to")

        if (
            start is not None
            and end is not None
            and end < start
        ):
            issues.append("invalid_effective_period")

    def _validate_fine_ranges(
        self,
        record: dict,
        issues: list[str],
    ) -> None:

        fines = record.get("fine_ranges")

        if (
            not isinstance(fines, list)
            or not fines
        ):
            issues.append("invalid_fine_ranges")
            return

        seen_recipients = set()

        for index, fine in enumerate(fines):

            if not isinstance(fine, dict):
                issues.append(
                    f"invalid_fine_{index}"
                )
                continue

            minimum = fine.get("min_vnd")
            maximum = fine.get("max_vnd")

            if (
                type(minimum) is not int
                or type(maximum) is not int
                or minimum <= 0
                or maximum < minimum
            ):
                issues.append(
                    f"invalid_amount_{index}"
                )

            recipient = fine.get("recipient")

            if recipient not in RECIPIENTS:
                issues.append(
                    f"invalid_recipient_{index}"
                )
                continue

            if recipient in seen_recipients:
                issues.append(
                    f"duplicate_recipient_{index}"
                )

            seen_recipients.add(recipient)

    def validate(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:

        issues: list[str] = []

        if not isinstance(record, dict):
            return {
                "valid": False,
                "issues": [
                    "record_must_be_object"
                ],
            }

        for field in self.REQUIRED_FIELDS:
            if field not in record:
                issues.append(
                    f"missing_{field}"
                )

        self._validate_identifiers(
            record,
            issues,
        )

        self._validate_metadata(
            record,
            issues,
        )

        self._validate_source(
            record,
            issues,
        )

        self._validate_dates(
            record,
            issues,
        )

        self._validate_fine_ranges(
            record,
            issues,
        )

        return {
            "valid": len(issues) == 0,
            "issues": list(dict.fromkeys(issues)),
        }