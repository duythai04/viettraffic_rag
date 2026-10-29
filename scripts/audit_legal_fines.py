

import csv
import json
from pathlib import Path

from src.validation.ocr_auditor import OCRAuditor


INPUT_PATH = Path(
    "data/processed/chunks/legal_chunks.json"
)

OUTPUT_DIR = Path("data/evaluation")

JSON_PATH = OUTPUT_DIR / "ocr_audit_report.json"
CSV_PATH = OUTPUT_DIR / "ocr_audit_report.csv"


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy dữ liệu: {INPUT_PATH}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not isinstance(chunks, list):
        raise ValueError(
            "legal_chunks.json phải chứa một danh sách chunks"
        )

    auditor = OCRAuditor()
    report = auditor.audit(chunks)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
        )

    fields = [
        "clause_id",
        "chunk_count",
        "status",
        "issues",
        "fine_ranges",
        "source_text",
    ]

    with CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )
        writer.writeheader()

        for record in report["records"]:
            writer.writerow({
                "clause_id": record["clause_id"],
                "chunk_count": record["chunk_count"],
                "status": record["status"],
                "issues": json.dumps(
                    record["issues"],
                    ensure_ascii=False,
                ),
                "fine_ranges": json.dumps(
                    record["fine_ranges"],
                    ensure_ascii=False,
                ),
                "source_text": record["source_text"],
            })

    summary = report["summary"]

    print("\n" + "=" * 60)
    print("OCR QUALITY AUDIT")
    print("=" * 60)

    print(
        f"Total chunks: {summary['total_chunks']}"
    )
    print(
        f"Unique clauses: {summary['total_clauses']}"
    )
    print(
        f"Skipped chunks: {summary['skipped_chunks']}"
    )

    print("\nStatus distribution:")

    for status, count in sorted(
        summary["status_counts"].items()
    ):
        print(f"{status:<25}: {count}")

    print("\nExamples requiring review:")

    examples = [
        record
        for record in report["records"]
        if record["status"] in {
            "suspicious_ocr",
            "multiple_fines",
        }
    ]

    for record in examples[:10]:
        print(
            f"\n- {record['clause_id']}"
            f" [{record['status']}]"
        )
        print(
            f"  Issues: {record['issues']}"
        )
        print(
            f"  Text: {record['source_text'][:160]!r}"
        )

    print(f"\nJSON: {JSON_PATH}")
    print(f"CSV:  {CSV_PATH}")


if __name__ == "__main__":
    main()