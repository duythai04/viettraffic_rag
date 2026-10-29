from src.validation.verified_fine_resolver import (
    VerifiedFineResolver,
)


class GroundedAnswerGenerator:
    def __init__(self, fine_resolver=None):
        self.fine_resolver = (
            fine_resolver or VerifiedFineResolver()
        )

    def generate(
        self,
        question: str,
        contexts: list[dict],
        recipient: str | None = None,
        as_of: str | None = None,
    ):
        if not contexts:
            return {
                "answer": (
                    "Chưa tìm thấy căn cứ pháp luật "
                    "phù hợp trong dữ liệu hiện có."
                ),
                "citations": [],
                "verified": False,
            }

        citations = []
        verified_fines = []

        for context in contexts:
            citation = context.get("citation")

            if citation and citation not in citations:
                citations.append(citation)

            clause_id = context.get("clause_id")

            if not clause_id:
                continue

            fine = self.fine_resolver.resolve(
                clause_id,
                recipient=recipient,
                as_of=as_of,
            )

            if fine:
                verified_fines.append(fine)

        # Nhiều căn cứ có thể áp dụng cho các hành vi khác nhau.
        # Không tự chọn một mức phạt khi chưa phân giải được.
        if len(verified_fines) != 1:
            return {
                "answer": (
                    "Hệ thống đã tìm thấy các quy định "
                    "có thể liên quan, nhưng chưa có "
                    "đủ căn cứ đã kiểm duyệt để xác định "
                    "mức phạt cho trường hợp này."
                ),
                "citations": citations,
                "verified": False,
            }

        fine = verified_fines[0]

        lines = []

        for item in fine["fine_ranges"]:
            minimum = f'{item["min_vnd"]:,}'.replace(",", ".")
            maximum = f'{item["max_vnd"]:,}'.replace(",", ".")

            lines.append(
                f'- {item["recipient"]}: '
                f'{minimum} – {maximum} đồng'
            )

        answer = (
            "Mức phạt trong hồ sơ đã kiểm duyệt:\n"
            + "\n".join(lines)
            + "\n\nCăn cứ đối chiếu: "
            + fine["source_reference"]
            + "\nVăn bản: "
            + fine["source_document"]
            + "\n\nLưu ý: Cần xác nhận quy định "
            "này áp dụng đúng hành vi, phương tiện "
            "và thời điểm được hỏi."
        )

        return {
            "answer": answer,
            "citations": citations,
            "verified": True,
            "fine": fine,
        }