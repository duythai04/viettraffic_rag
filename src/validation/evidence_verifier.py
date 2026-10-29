"""Validate a human-reviewed legal fine record's structure, not its legal truth."""
from __future__ import annotations

import re
from datetime import date
from typing import Any


CLAUSE_ID = re.compile(r"^.+_dieu-\d+_khoan-\d+$")
RECIPIENTS = {"individual", "organization", "driver", "other"}


class EvidenceVerifier:
    REQUIRED = (
        "clause_id", "fine_ranges", "source_reference", "source_document",
        "verified_by", "verification_note", "review_confirmed",
        "effective_from",
    )

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        if not isinstance(record, dict):
            return {"valid": False, "issues": ["record_must_be_object"]}

        for key in self.REQUIRED:
            if key not in record:
                issues.append(f"missing_{key}")

        clause_id = record.get("clause_id")
        if not isinstance(clause_id, str) or not CLAUSE_ID.fullmatch(clause_id):
            issues.append("invalid_clause_id")

        for key in ("source_reference", "source_document", "verified_by", "verification_note"):
            value = record.get(key)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"invalid_{key}")

        if record.get("review_confirmed") is not True:
            issues.append("human_review_not_confirmed")

        for key in ("effective_from", "effective_to"):
            value = record.get(key)
            if value is None and key == "effective_to":
                continue
            if not isinstance(value, str):
                issues.append(f"invalid_{key}")
                continue
            try:
                date.fromisoformat(value)
            except ValueError:
                issues.append(f"invalid_{key}")

        start = record.get("effective_from")
        end = record.get("effective_to")
        try:
            if end is not None and date.fromisoformat(end) < date.fromisoformat(start):
                issues.append("invalid_effective_period")
        except (TypeError, ValueError):
            pass

        fines = record.get("fine_ranges")
        if not isinstance(fines, list) or not fines:
            issues.append("invalid_fine_ranges")
        else:
            for i, fine in enumerate(fines):
                if not isinstance(fine, dict):
                    issues.append(f"invalid_fine_{i}")
                    continue
                low, high = fine.get("min_vnd"), fine.get("max_vnd")
                if (type(low) is not int or type(high) is not int
                        or low <= 0 or high < low):
                    issues.append(f"invalid_amount_{i}")
                if fine.get("recipient") not in RECIPIENTS:
                    issues.append(f"invalid_recipient_{i}")

        return {"valid": not issues, "issues": issues}
