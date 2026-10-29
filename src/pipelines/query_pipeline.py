from __future__ import annotations

from src.evidence.legal_evidence_selector import LegalEvidenceSelector
from src.generation.grounded_answer import GroundedAnswerGenerator
from src.query.intent_detector import QueryIntentDetector


class QueryPipeline:
    def __init__(
        self,
        retriever,
        answer_generator=None,
        intent_detector=None,
        context_reconstructor=None,
        evidence_selector=None,
    ):
        self.retriever = retriever

        self.answer_generator = (
            answer_generator
            if answer_generator is not None
            else GroundedAnswerGenerator()
        )

        self.intent_detector = (
            intent_detector
            if intent_detector is not None
            else QueryIntentDetector()
        )

        self.context_reconstructor = context_reconstructor

        self.evidence_selector = (
            evidence_selector
            if evidence_selector is not None
            else LegalEvidenceSelector()
        )

    def _build_response(
        self,
        question: str,
        intent: str,
        answer: str,
        citations: list[str] | None = None,
        verified: bool = False,
        retrieved_chunks: int = 0,
        selected_evidence_count: int = 0,
    ) -> dict:
        return {
            "question": question,
            "intent": intent,
            "answer": answer,
            "citations": citations if citations is not None else [],
            "verified": verified,
            "retrieved_chunks": retrieved_chunks,
            "selected_evidence_count": selected_evidence_count,
        }

    def _handle_non_legal_intent(
        self,
        question: str,
        intent: str,
    ) -> dict | None:
        responses = {
            "greeting": (
                "Xin chào! Tôi là VietTraffic AI, "
                "trợ lý hỗ trợ tra cứu quy định pháp luật "
                "giao thông đường bộ Việt Nam. "
                "Bạn muốn tìm hiểu vấn đề gì?"
            ),
            "identity": (
                "Tôi là VietTraffic AI, trợ lý hỗ trợ "
                "tra cứu thông tin pháp luật giao thông "
                "đường bộ Việt Nam. Tôi có thể giúp bạn "
                "tìm hiểu các quy định và mức xử phạt giao thông."
            ),
            "out_of_scope": (
                "Tôi hiện tập trung hỗ trợ tra cứu pháp luật "
                "giao thông đường bộ Việt Nam. Bạn có thể hỏi "
                "về hành vi vi phạm, quy định hoặc mức xử phạt."
            ),
        }

        if intent not in responses:
            return None

        return self._build_response(
            question=question,
            intent=intent,
            answer=responses[intent],
        )

    @staticmethod
    def _extract_payload(result) -> dict:
        if isinstance(result, dict):
            payload = result.get("payload", result)
        else:
            payload = getattr(result, "payload", {})

        if not isinstance(payload, dict):
            return {}

        metadata = payload.get("metadata") or {}

        if not isinstance(metadata, dict):
            metadata = {}

        return {
            **metadata,
            **{
                key: value
                for key, value in payload.items()
                if key != "metadata" and value is not None
            },
        }

    @staticmethod
    def _extract_clause_id(
        payload: dict,
    ) -> str | None:
        clause_id = payload.get("clause_id")

        if clause_id:
            return clause_id

        chunk_id = payload.get("chunk_id") or ""

        if "_diem-" in chunk_id:
            return chunk_id.split("_diem-")[0]

        if "_khoan-" in chunk_id:
            return chunk_id

        return None

    def _build_contexts(
        self,
        results: list,
    ) -> list[dict]:
        contexts = []
        seen_chunk_ids = set()

        for result in results:
            payload = self._extract_payload(result)

            if not payload:
                continue

            chunk_id = payload.get("chunk_id")

            if not chunk_id:
                continue

            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)

            score = payload.get("adjusted_score")

            if score is None:
                score = payload.get("rrf_score")

            if score is None:
                score = payload.get("score")

            contexts.append({
                "clause_id": self._extract_clause_id(payload),
                "chunk_id": chunk_id,
                "citation": payload.get("citation"),
                "content": payload.get("content"),
                "article": payload.get("article"),
                "article_title": payload.get("article_title"),
                "clause": payload.get("clause"),
                "point": payload.get("point"),
                "clause_preamble": payload.get("clause_preamble"),
                "source": payload.get("source"),
                "vehicle_type": payload.get("vehicle_type"),
                "retrieval_score": score,
            })

        return contexts

    def _reconstruct_contexts(
        self,
        contexts: list[dict],
    ) -> list[dict]:
        if self.context_reconstructor is None:
            return contexts

        reconstructed = []

        for context in contexts:
            chunk_id = context.get("chunk_id")

            if not chunk_id:
                continue

            try:
                legal_context = (
                    self.context_reconstructor.reconstruct(
                        chunk_id
                    )
                )
            except KeyError:
                reconstructed.append(context)
                continue

            merged_context = {
                **context,
                **legal_context,
                "clause_id": context.get("clause_id"),
                "vehicle_type": context.get("vehicle_type"),
                "retrieval_score": context.get("retrieval_score"),
            }

            reconstructed.append(merged_context)

        return reconstructed

    def _select_evidence(
        self,
        question: str,
        contexts: list[dict],
    ) -> dict:
        if not contexts:
            return {
                "question": question,
                "selected_evidence": [],
                "requires_clarification": True,
            }

        return self.evidence_selector.select(
            question=question,
            contexts=contexts,
        )

    def run(
        self,
        question: str,
        recipient: str | None = None,
        as_of: str | None = None,
        top_k: int = 5,
        debug: bool = False,
    ) -> dict:
        if not isinstance(question, str):
            raise TypeError("Question must be a string")

        question = question.strip()

        if not question:
            raise ValueError("Question must not be empty")

        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k < 1
        ):
            raise ValueError(
                "top_k must be a positive integer"
            )

        intent = self.intent_detector.detect(question)

        non_legal_response = self._handle_non_legal_intent(
            question=question,
            intent=intent,
        )

        if non_legal_response is not None:
            return non_legal_response

        if intent not in {"legal_fine", "legal_general"}:
            return self._build_response(
                question=question,
                intent=intent,
                answer=(
                    "Tôi chưa xác định được nội dung câu hỏi. "
                    "Bạn có thể mô tả rõ hơn về quy định "
                    "giao thông cần tra cứu."
                ),
            )

        results = self.retriever.retrieve(
            question,
            top_k=top_k,
        )

        if results is None:
            results = []

        contexts = self._build_contexts(results)

        if not contexts:
            final_response = self._build_response(
                question=question,
                intent=intent,
                answer=(
                    "Tôi chưa tìm thấy quy định pháp luật "
                    "phù hợp với câu hỏi trong dữ liệu hiện có. "
                    "Bạn có thể mô tả cụ thể hơn hành vi "
                    "hoặc loại phương tiện."
                ),
            )

            if debug:
                final_response["retrieval_results"] = results
                final_response["legal_contexts"] = []
                final_response["evidence_selection"] = {
                    "question": question,
                    "selected_evidence": [],
                    "requires_clarification": True,
                }

            return final_response

        contexts = self._reconstruct_contexts(contexts)

        evidence_result = self._select_evidence(
            question=question,
            contexts=contexts,
        )

        selected_contexts = evidence_result.get(
            "selected_evidence",
            [],
        )

        if not selected_contexts:
            final_response = self._build_response(
                question=question,
                intent=intent,
                answer=(
                    "Tôi đã tìm thấy một số quy định "
                    "có thể liên quan, nhưng chưa đủ "
                    "căn cứ để xác định điều khoản "
                    "phù hợp với trường hợp được hỏi. "
                    "Bạn có thể cung cấp thêm thông tin "
                    "về phương tiện và hành vi vi phạm."
                ),
                retrieved_chunks=len(contexts),
            )

            if debug:
                final_response["retrieval_results"] = results
                final_response["legal_contexts"] = contexts
                final_response["evidence_selection"] = evidence_result

            return final_response

        response = self.answer_generator.generate(
            question=question,
            contexts=selected_contexts,
            recipient=recipient,
            as_of=as_of,
        )

        final_response = self._build_response(
            question=question,
            intent=intent,
            answer=response["answer"],
            citations=response.get("citations", []),
            verified=response.get("verified", False),
            retrieved_chunks=len(contexts),
            selected_evidence_count=len(selected_contexts),
        )

        if debug:
            final_response["retrieval_results"] = results
            final_response["legal_contexts"] = contexts
            final_response["evidence_selection"] = evidence_result

        return final_response