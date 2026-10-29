"""Import explicitly confirmed human reviews into VerifiedFineStore."""
import argparse
import json
from pathlib import Path

from src.validation.evidence_verifier import EvidenceVerifier
from src.validation.verified_fine_store import VerifiedFineStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Human-reviewed JSON array")
    parser.add_argument("--store", default="data/verified/verified_fines.json")
    parser.add_argument("--apply", action="store_true", help="Persist after dry-run")
    args = parser.parse_args()

    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Input must be a JSON array")

    verifier = EvidenceVerifier()
    store = VerifiedFineStore(args.store)
    errors = []
    seen = set()
    for index, record in enumerate(records):
        result = verifier.validate(record)
        if not result["valid"]:
            errors.append((index, result["issues"]))
            continue
        clause_id = record["clause_id"]
        if clause_id in seen:
            errors.append((index, ["duplicate_clause_in_input"]))
        if store.is_verified(clause_id):
            errors.append((index, ["already_in_verified_store"]))
        seen.add(clause_id)

    if errors:
        for index, issues in errors:
            print(f"Record {index}: {', '.join(issues)}")
        raise SystemExit(f"Import aborted: {len(errors)} invalid/conflicting records")

    print(f"Preflight passed: {len(records)} records")
    if not args.apply:
        print("DRY RUN only. Re-run with --apply after checking the reviewed file.")
        return

    for record in records:
        store.add_verified(
            clause_id=record["clause_id"],
            fine_ranges=record["fine_ranges"],
            source_reference=record["source_reference"],
            source_document=record["source_document"],
            verified_by=record["verified_by"],
            verification_note=(
                record["verification_note"]
                + f" | Effective: {record['effective_from']}"
                + f" to {record.get('effective_to') or 'open'}"
            ),
        )
    print(f"Imported {len(records)} records into {args.store}")


if __name__ == "__main__":
    main()
