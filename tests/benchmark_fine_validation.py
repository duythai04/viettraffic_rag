import json
from collections import Counter
from pathlib import Path

from src.validation.fine_validator import FineValidator

SOURCE = Path("data/processed/chunks/legal_chunks.json")
OUTPUT = Path("data/evaluation/fine_validation_results.json")


def main():
    chunks = json.loads(SOURCE.read_text(encoding="utf-8"))
    validator = FineValidator()
    counts = Counter()
    results = []
    for chunk in chunks:
        preamble = chunk.get("clause_preamble") or ""
        # For clause-level chunks, the fine may appear in the content itself.
        text = preamble or (chunk.get("content") or chunk.get("text") or "")
        result = validator.validate(text)
        counts[result["status"]] += 1
        results.append({
            "chunk_id": chunk["chunk_id"],
            "citation": chunk.get("citation"),
            "preamble": text,
            **result,
        })

    report = {"total": len(results), "status_counts": dict(counts), "results": results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nFINE VALIDATION BENCHMARK")
    print("=" * 52)
    print("Total:", len(results))
    for status, count in sorted(counts.items()):
        print(f"{status:26} {count:5} ({count / len(results) * 100:.2f}%)")
    print("\nExamples for manual review:")
    for item in [r for r in results if r["status"] in ("suspicious_ocr", "multiple_fines")][:10]:
        print(f"- {item['chunk_id']}: {item['status']} | {item['preamble'][:130]!r}")
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()

