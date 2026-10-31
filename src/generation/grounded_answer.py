from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.generation.answer_validator import AnswerValidator
from src.llm.llm_client import LLMClient
from src.llm.prompt_builder import LegalPromptBuilder
from src.validation.verified_fine_resolver import VerifiedFineResolver
from src.evidence.fine_evidence_enricher import FineEvidenceEnricher


class GroundedAnswerGenerator:
    """
    Generate grounded legal answers for VietTraffic RAG.

    Workflow:
        1. Receive selected legal evidence.
        2. Detect whether the question asks about fines.
        3. Resolve a human-reviewed fine when possible.
        4. Otherwise generate a grounded answer using the LLM.
        5. Validate the generated answer.
        6. Reject unsupported monetary amounts.

    Important:
        OCR-extracted fine amounts are not considered verified.
    """

    def __init__(
        self,
        fine_resolver=None,
        llm_client=None,
        prompt_builder=None,
        answer_validator=None,
    ):
        self.fine_resolver = (
            fine_resolver
            if fine_resolver is not None
            else VerifiedFineResolver()
        )

        self.llm_client = (
            llm_client
            if llm_client is not None
            else LLMClient()
        )

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else LegalPromptBuilder()
        )

        self.answer_validator = (
            answer_validator
            if answer_validator is not None
            else AnswerValidator()
        )

    # ==========================================================
    # TEXT NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for question classification.
        """
        text = unicodedata.normalize(
            "NFC",
            str(text).lower(),
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ==========================================================
    # CITATIONS
    # ==========================================================

    @staticmethod
    def _collect_citations(
        contexts: list[dict],
    ) -> list[str]:
        """
        Collect unique citations from legal contexts.
        """
        citations = []

        for context in contexts:
            citation = context.get("citation")

            if (
                isinstance(citation, str)
                and citation.strip()
                and citation not in citations
            ):
                citations.append(citation)

        return citations

    # ==========================================================
    # SAFE RESPONSE
    # ==========================================================

    @staticmethod
    def _safe_response(
        answer: str,
        citations: list[str] | None = None,
        validation_errors: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Return a safe, unverified response.
        """
        return {
            "answer": answer,
            "citations": citations or [],
            "verified": False,
            "validation_errors": validation_errors or [],
        }

    # ==========================================================
    # FINE QUESTION DETECTION
    # ==========================================================

    @classmethod
    def _is_fine_question(
        cls,
        question: str,
    ) -> bool:
        """
        Detect questions asking about penalties or fine amounts.
        """
        text = cls._normalize_text(question)

        patterns = [
            r"phạt bao nhiêu",
            r"mức phạt",
            r"tiền phạt",
            r"phạt tiền",
            r"bao nhiêu tiền",
            r"bị phạt",
            r"xử phạt",
            r"phạt mấy",
            r"phạt từ bao nhiêu",
            r"phạt đến bao nhiêu",
            r"bao nhiêu đồng",
            r"bao nhiêu triệu",
            r"mất bao nhiêu tiền",
        ]

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    # ==========================================================
    # LEGAL CONTEXT VALIDATION
    # ==========================================================

    @staticmethod
    def _has_required_metadata(
        context: dict,
    ) -> bool:
        """
        Check metadata required for verified fine lookup.

        All fields must be present and non-empty.
        """
        required_fields = (
            "clause_id",
            "chunk_id",
            "vehicle_type",
            "role",
            "violation_key",
        )

        for field in required_fields:
            value = context.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                return False

        return True

    # ==========================================================
    # VERIFIED FINE RESOLUTION
    # ==========================================================

    def _resolve_verified_fine(
        self,
        contexts: list[dict],
        recipient: str | None = None,
        as_of: str | None = None,
    ) -> dict | None:
        """
        Resolve a fine only when one selected evidence
        item contains complete legal metadata.

        No fallback to OCR monetary amounts.
        """

        if len(contexts) != 1:
            return None

        context = contexts[0]

        if not self._has_required_metadata(context):
            return None

        clause_id = context["clause_id"]
        chunk_id = context["chunk_id"]
        vehicle_type = context["vehicle_type"]
        role = context["role"]
        violation_key = context["violation_key"]

        try:
            fine = self.fine_resolver.resolve(
                clause_id=clause_id,
                chunk_id=chunk_id,
                vehicle_type=vehicle_type,
                role=role,
                violation_key=violation_key,
                recipient=recipient,
                as_of=as_of,
            )

        except (
            KeyError,
            ValueError,
            TypeError,
        ) as exc:
            print(
                "[GroundedAnswerGenerator] "
                f"Fine resolver error: {exc}"
            )

            return None

        if not isinstance(fine, dict):
            return None

        # The resolver must return a human-reviewed record.
        if (
            fine.get("status") != "review_confirmed"
            or fine.get("review_confirmed") is not True
        ):
            return None

        # Verify that the resolved record still matches
        # the exact evidence selected for the question.
        for field in (
            "clause_id",
            "chunk_id",
            "vehicle_type",
            "role",
            "violation_key",
        ):
            if fine.get(field) != context.get(field):
                return None

        return fine

    # ==========================================================
    # FORMAT VERIFIED FINE
    # ==========================================================

    @staticmethod
    def _format_vnd(
        amount: int,
    ) -> str:
        """
        Format Vietnamese currency amounts.
        """
        return f"{amount:,}".replace(",", ".")

    @classmethod
    def _format_verified_fine(
        cls,
        fine: dict,
    ) -> str:
        """
        Format fine ranges from a reviewed record.

        Never read monetary amounts from OCR context.
        """
        lines = []

        fine_ranges = fine.get(
            "fine_ranges",
            [],
        )

        if not isinstance(fine_ranges, list):
            return ""

        recipient_labels = {
            "individual": "Cá nhân",
            "organization": "Tổ chức",
            "driver": "Người điều khiển phương tiện",
            "passenger": "Người được chở",
            "other": "Đối tượng khác",
        }

        for item in fine_ranges:
            if not isinstance(item, dict):
                return ""

            minimum = item.get("min_vnd")
            maximum = item.get("max_vnd")
            recipient = item.get("recipient")

            if (
                type(minimum) is not int
                or type(maximum) is not int
                or minimum <= 0
                or maximum < minimum
            ):
                return ""

            if recipient not in recipient_labels:
                return ""

            minimum_text = cls._format_vnd(minimum)
            maximum_text = cls._format_vnd(maximum)

            recipient_label = recipient_labels[recipient]

            if minimum == maximum:
                fine_text = f"{minimum_text} đồng"
            else:
                fine_text = (
                    f"{minimum_text} – "
                    f"{maximum_text} đồng"
                )

            lines.append(
                f"- {recipient_label}: {fine_text}"
            )

        if not lines:
            return ""

        source_reference = fine.get(
            "source_reference",
            "",
        )

        source_document = fine.get(
            "source_document",
            "",
        )

        effective_from = fine.get(
            "effective_from",
        )

        effective_to = fine.get(
            "effective_to",
        )

        answer_parts = [
            "Mức phạt theo hồ sơ đã được kiểm duyệt:",
            "\n".join(lines),
            "",
            f"Căn cứ pháp luật: {source_reference}",
            f"Văn bản: {source_document}",
        ]

        if effective_from:
            answer_parts.append(
                f"Áp dụng từ ngày: {effective_from}"
            )

        if effective_to:
            answer_parts.append(
                f"Áp dụng đến ngày: {effective_to}"
            )

        answer_parts.extend([
            "",
            (
                "Lưu ý: Mức phạt trên được lấy từ hồ sơ "
                "đã được kiểm duyệt trong hệ thống. "
                "Cần đối chiếu văn bản pháp luật chính thức "
                "và các sửa đổi có hiệu lực tại thời điểm "
                "xảy ra hành vi."
            ),
        ])

        return "\n".join(answer_parts)

    # ==========================================================
    # LLM GENERATION
    # ==========================================================

    def _generate_llm_answer(
        self,
        question: str,
        contexts: list[dict],
        citations: list[str],
    ) -> dict[str, Any]:
        """
        Generate a grounded answer using GPT-4o mini.

        Any monetary amount must be rejected because
        this path has no verified fine record.
        """

        try:
            system_prompt, prompt = self.prompt_builder.build(
                question=question,
                contexts=contexts,
            )

        except (
            ValueError,
            TypeError,
            KeyError,
        ):
            return self._safe_response(
                answer=(
                    "Hệ thống đã tìm thấy một số quy định "
                    "có thể liên quan, nhưng chưa đủ căn cứ "
                    "để tạo câu trả lời."
                ),
                citations=citations,
                validation_errors=[
                    "invalid_prompt_context"
                ],
            )

        try:
            answer = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

        except Exception as exc:
            print(
                "[GroundedAnswerGenerator] "
                f"LLM generation error: "
                f"{type(exc).__name__}: {exc}"
            )

            return self._safe_response(
                answer=(
                    "Hệ thống hiện không thể tạo câu trả lời "
                    "từ GPT-4o mini. Vui lòng thử lại sau."
                ),
                citations=citations,
                validation_errors=[
                    "llm_generation_failed"
                ],
            )

        if not isinstance(answer, str):
            return self._safe_response(
                answer=(
                    "Hệ thống không nhận được câu trả lời "
                    "hợp lệ từ mô hình ngôn ngữ."
                ),
                citations=citations,
                validation_errors=[
                    "invalid_llm_response"
                ],
            )

        answer = answer.strip()

        if not answer:
            return self._safe_response(
                answer=(
                    "Mô hình ngôn ngữ chưa tạo được "
                    "câu trả lời phù hợp."
                ),
                citations=citations,
                validation_errors=[
                    "empty_llm_response"
                ],
            )

        try:
            validation = self.answer_validator.validate(
                answer=answer,
                contexts=contexts,
                fine_verified=False,
            )

        except Exception as exc:
            print(
                "[GroundedAnswerGenerator] "
                f"Answer validation error: "
                f"{type(exc).__name__}: {exc}"
            )

            return self._safe_response(
                answer=(
                    "Hệ thống chưa thể kiểm chứng "
                    "câu trả lời được tạo."
                ),
                citations=citations,
                validation_errors=[
                    "answer_validation_failed"
                ],
            )

        if not validation.get("valid", False):
            errors = validation.get(
                "errors",
                ["invalid_answer"],
            )

            print(
                "[GroundedAnswerGenerator] "
                "Answer rejected:",
                errors,
            )

            return self._safe_response(
                answer=(
                    "Hệ thống đã tìm thấy quy định "
                    "có thể liên quan, nhưng câu trả lời "
                    "được tạo chưa đáp ứng yêu cầu "
                    "kiểm chứng pháp lý. "
                    "Vui lòng tham khảo căn cứ "
                    "được truy xuất."
                ),
                citations=citations,
                validation_errors=errors,
            )

        return {
            "answer": answer,
            "citations": citations,
            "verified": False,
            "validation_errors": [],
        }

    # ==========================================================
    # MAIN GENERATION METHOD
    # ==========================================================

    def generate(
        self,
        question: str,
        contexts: list[dict],
        recipient: str | None = None,
        as_of: str | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point.

        Returns:
            {
                "answer": str,
                "citations": list[str],
                "verified": bool,
                "validation_errors": list[str],
                "fine": dict (optional)
            }
        """

        if not isinstance(question, str):
            raise TypeError(
                "question must be a string"
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "question must not be empty"
            )

        if not isinstance(contexts, list):
            raise TypeError(
                "contexts must be a list"
            )

        if not contexts:
            return self._safe_response(
                answer=(
                    "Chưa tìm thấy căn cứ pháp luật "
                    "phù hợp trong dữ liệu hiện có."
                )
            )

        # Use the highest-ranked evidence only.
        best_context = contexts[0]

        if not isinstance(best_context, dict):
            return self._safe_response(
                answer=(
                    "Dữ liệu căn cứ pháp luật "
                    "không hợp lệ."
                ),
                validation_errors=[
                    "invalid_evidence_context"
                ],
            )

      # Enrich metadata for supported legal fine evidence.
        enriched_context = FineEvidenceEnricher.enrich(
            question=question,
            context=best_context,
        )

        selected_contexts = [
            enriched_context
        ]

        citations = self._collect_citations(
            selected_contexts
        )

        # ------------------------------------------------------
        # STEP 1: CHECK WHETHER QUESTION ASKS ABOUT A FINE
        # ------------------------------------------------------

        is_fine_question = self._is_fine_question(
            question
        )

        # ------------------------------------------------------
        # STEP 2: RESOLVE VERIFIED FINE
        # ------------------------------------------------------

        if is_fine_question:
            fine = self._resolve_verified_fine(
                contexts=selected_contexts,
                recipient=recipient,
                as_of=as_of,
            )

            if fine is not None:
                fine_answer = self._format_verified_fine(
                    fine
                )

                if fine_answer:
                    return {
                        "answer": fine_answer,
                        "citations": citations,
                        "verified": True,
                        "fine": fine,
                        "validation_errors": [],
                    }

        # ------------------------------------------------------
        # STEP 3: GENERATE GROUNDED ANSWER
        # ------------------------------------------------------

        result = self._generate_llm_answer(
            question=question,
            contexts=selected_contexts,
            citations=citations,
        )

        # ------------------------------------------------------
        # STEP 4: EXTRA SAFETY CHECK FOR FINE QUESTIONS
        # ------------------------------------------------------

        if is_fine_question and not result.get(
            "verified",
            False,
        ):
            answer = result.get(
                "answer",
                "",
            )

            # Reject monetary values if they appear despite
            # the validator or prompt restrictions.
            money_pattern = re.compile(
                r"\b\d[\d.,\s]*"
                r"(?:đồng|vnd|vnđ|triệu|tỷ)\b",
                re.IGNORECASE,
            )

            if money_pattern.search(answer):
                return self._safe_response(
                    answer=(
                        "Hệ thống đã tìm thấy căn cứ "
                        "pháp luật liên quan, nhưng "
                        "chưa có hồ sơ mức phạt "
                        "được kiểm duyệt để xác nhận "
                        "số tiền cụ thể."
                    ),
                    citations=citations,
                    validation_errors=[
                        "unverified_fine_amount"
                    ],
                )

        return result