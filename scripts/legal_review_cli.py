"""Interactive human review of OCR legal fines; never auto-verifies OCR output."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from src.validation.evidence_verifier import EvidenceVerifier


def load_array(path: Path, *, required: bool = False) -> list[dict]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Review queue not found: {path}")
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"Expected a JSON array of objects: {path}")
    return value


def atomic_write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(records, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def ask_nonempty(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Không được để trống.")


def ask_money(label: str) -> int:
    while True:
        value = input(f"{label} (VND, chỉ nhập chữ số): ").strip()
        if value.isascii() and value.isdecimal() and int(value) > 0:
            return int(value)
        print("Nhập số nguyên dương, ví dụ: 4000000")


def ask_recipient() -> str:
    options = {"1": "individual", "2": "organization", "3": "driver", "4": "other"}
    while True:
        print("Đối tượng: 1=cá nhân, 2=tổ chức, 3=người điều khiển, 4=khác")
        value = input("Chọn đối tượng: ").strip()
        if value in options:
            return options[value]
        print("Lựa chọn không hợp lệ.")


def collect_review(item: dict) -> dict:
    print("\nĐỐI CHIẾU VỚI VĂN BẢN PHÁP LUẬT CÓ THẨM QUYỀN TRƯỚC KHI NHẬP.")
    fines = []
    while True:
        low = ask_money("Mức tối thiểu")
        high = ask_money("Mức tối đa")
        if high < low:
            print("Mức tối đa không được nhỏ hơn mức tối thiểu. Nhập lại.")
            continue
        fines.append({"min_vnd": low, "max_vnd": high, "recipient": ask_recipient()})
        if input("Thêm mức phạt khác? [y/N]: ").strip().lower() != "y":
            break

    record = {
        "clause_id": item["clause_id"],
        "fine_ranges": fines,
        "source_reference": ask_nonempty("Điều/khoản/điểm đối chiếu"),
        "source_document": ask_nonempty("Tên, số hiệu văn bản nguồn"),
        "verified_by": ask_nonempty("Người kiểm duyệt"),
        "verification_note": ask_nonempty("Ghi chú đối chiếu (bao gồm nguồn tra cứu)"),
        "effective_from": ask_nonempty("Ngày bắt đầu hiệu lực YYYY-MM-DD"),
        "effective_to": input("Ngày kết thúc hiệu lực YYYY-MM-DD (Enter nếu chưa xác định): ").strip() or None,
        "review_confirmed": False,
    }
    return record


def save_review(record: dict, output: Path, verifier: EvidenceVerifier) -> bool:
    record = dict(record)
    record["review_confirmed"] = True
    check = verifier.validate(record)
    if not check["valid"]:
        print("Hồ sơ chưa hợp lệ:", ", ".join(check["issues"]))
        return False
    existing = load_array(output)
    if any(row.get("clause_id") == record["clause_id"] for row in existing):
        print("Khoản này đã có trong reviewed_fines.json; không ghi đè.")
        return False
    existing.append(record)
    atomic_write(output, existing)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI kiểm duyệt thủ công mức phạt OCR")
    parser.add_argument("--queue", default="data/evaluation/legal_review_queue.json")
    parser.add_argument("--output", default="data/verified/reviewed_fines.json")
    args = parser.parse_args()
    queue_path, output = Path(args.queue), Path(args.output)
    if queue_path.resolve() == output.resolve():
        parser.error("--queue và --output phải là hai file khác nhau")
    queue = load_array(queue_path, required=True)
    verifier = EvidenceVerifier()
    seen_queue = set()
    for item in queue:
        cid = item.get("clause_id")
        if not isinstance(cid, str) or cid in seen_queue:
            raise ValueError("Review queue có clause_id thiếu, sai kiểu hoặc trùng lặp")
        seen_queue.add(cid)
    position = 0
    while True:
        reviewed = {x.get("clause_id") for x in load_array(output)}
        pending = [x for x in queue if x["clause_id"] not in reviewed]
        if not pending:
            print("Không còn khoản nào trong hàng đợi chưa được lưu kiểm duyệt.")
            break
        position %= len(pending)
        item = pending[position]
        print("\n" + "=" * 65)
        print(f"Đã lưu: {len(queue) - len(pending)}/{len(queue)} | Còn lại: {len(pending)}")
        print(f"Khoản: {item['clause_id']}")
        print(f"OCR status: {item.get('audit_status', '?')} | Issues: {item.get('issues', [])}")
        print("NỘI DUNG OCR (CHƯA KIỂM CHỨNG):\n", item.get("ocr_text", ""))
        print("Gợi ý trích xuất (CHƯA KIỂM CHỨNG):", item.get("suggested_fines_unverified", []))
        print("[1] Kiểm duyệt | [2] Bỏ qua/tiếp | [3] Tiến độ | [0] Thoát")
        choice = input("Chọn: ").strip()
        if choice == "0":
            break
        if choice == "3":
            print(f"Đã lưu {len(queue) - len(pending)}, còn {len(pending)}")
            continue
        if choice == "2":
            position += 1
            continue
        if choice != "1":
            print("Lựa chọn không hợp lệ")
            continue
        draft = collect_review(item)
        print("\nHỒ SƠ DỰ KIẾN:\n", json.dumps(draft, ensure_ascii=False, indent=2))
        print("Xác nhận CHỈ KHI đã đối chiếu văn bản chính thức và nội dung chính xác.")
        confirmation = input("Gõ chính xác XAC_NHAN để lưu: ").strip()
        if confirmation != "XAC_NHAN":
            print("Đã hủy lưu. Không đánh dấu đã kiểm duyệt.")
            continue
        if save_review(draft, output, verifier):
            print(f"Đã lưu hồ sơ vào {output} (chưa nhập VerifiedFineStore).")
            position = 0


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nĐã thoát, các hồ sơ đã lưu trước đó vẫn được giữ nguyên.")
