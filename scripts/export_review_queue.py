"""Export clause-level records for human review; never mark them verified."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/evaluation/ocr_audit_report.json")
    parser.add_argument("--output", default="data/evaluation/legal_review_queue.json")
    args = parser.parse_args()

    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    priorities = {"suspicious_ocr": 0, "multiple_fines": 1}
    queue = []
    for item in report["records"]:
        if item["status"] not in priorities:
            continue
        queue.append({
            "clause_id": item["clause_id"],
            "audit_status": item["status"],
            "issues": item.get("issues", []),
            "ocr_text": item.get("source_text", ""),
            "suggested_fines_unverified": item.get("fine_ranges", []),
            "fine_ranges": [],
            "source_reference": "",
            "source_document": "",
            "verified_by": "",
            "verification_note": "",
            "effective_from": "",
            "effective_to": None,
            "review_confirmed": False,
        })
    queue.sort(key=lambda r: (priorities[r["audit_status"]], r["clause_id"]))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(queue)} clauses to {path}")
    print("Review each entry against an authoritative legal source before confirming.")


if __name__ == "__main__":
    main()
