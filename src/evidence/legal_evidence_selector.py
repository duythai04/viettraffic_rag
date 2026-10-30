from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

from src.retrieval.vehicle_detector import VehicleDetector


class LegalEvidenceSelector:
    """
    Select legal evidence relevant to a traffic-law question.

    Responsibilities:
        - Detect vehicle type.
        - Detect violation category.
        - Identify the legally relevant role.
        - Reject incompatible evidence.
        - Rank legal evidence.
        - Attach metadata for verified fine lookup.

    Important:
        Evidence selection does not verify monetary amounts.
    """

    VIOLATION_PATTERNS = {
        "helmet": [
            r"mũ bảo hiểm",
            r"mu bao hiem",
        ],
        "red_light": [
            r"đèn đỏ",
            r"tín hiệu đèn giao thông",
            r"đèn tín hiệu giao thông",
        ],
        "alcohol": [
            r"nồng độ cồn",
            r"có cồn trong máu",
            r"có cồn trong hơi thở",
        ],
        "speed": [
            r"quá tốc độ",
            r"vượt tốc độ",
            r"tốc độ quy định",
        ],
        "license": [
            r"giấy phép lái xe",
            r"không có giấy phép",
            r"không có bằng lái",
            r"không có bằng",
        ],
        "wrong_way": [
            r"ngược chiều",
            r"đi vào đường cấm",
        ],
        "insurance": [
            r"bảo hiểm bắt buộc",
            r"không có bảo hiểm",
            r"chứng nhận bảo hiểm",
        ],
    }

    # Chỉ ánh xạ những căn cứ đã được nhận diện rõ.
    # Đây là metadata phân loại, KHÔNG phải xác minh mức phạt.
    KNOWN_EVIDENCE = {
        "168-2024-ND-CP_dieu-7_khoan-2_diem-h": {
            "violation_key": "helmet_driver",
            "role": "driver",
            "vehicle_type": "motorcycle",
        },
        "168-2024-ND-CP_dieu-7_khoan-2_diem-i": {
            "violation_key": (
                "helmet_driver_responsible_for_passenger"
            ),
            "role": "driver_responsible_for_passenger",
            "vehicle_type": "motorcycle",
        },
        "168-2024-ND-CP_dieu-12_khoan-5_diem-b": {
            "violation_key": "helmet_passenger",
            "role": "passenger",
            "vehicle_type": "motorcycle",
        },
    }

    def __init__(
        self,
        max_evidence: int = 3,
        min_score: float = 0.0,
    ):
        if (
            isinstance(max_evidence, bool)
            or not isinstance(max_evidence, int)
            or max_evidence < 1
        ):
            raise ValueError(
                "max_evidence must be a positive integer"
            )

        if (
            not isinstance(min_score, (int, float))
            or isinstance(min_score, bool)
            or not math.isfinite(min_score)
        ):
            raise ValueError(
                "min_score must be a finite number"
            )

        self.max_evidence = max_evidence
        self.min_score = float(min_score)
        self.vehicle_detector = VehicleDetector()

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize(text: str | None) -> str:
        if text is None:
            return ""

        text = unicodedata.normalize(
            "NFC",
            str(text).lower(),
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def _normalize_vehicle(
        vehicle: str | None,
    ) -> str | None:
        if not isinstance(vehicle, str):
            return None

        vehicle = vehicle.strip().lower()

        if vehicle in {"", "unknown", "none"}:
            return None

        return vehicle

    @staticmethod
    def _extract_clause_id(
        chunk_id: str | None,
    ) -> str | None:
        if not isinstance(chunk_id, str):
            return None

        if "_diem-" in chunk_id:
            return chunk_id.split("_diem-")[0]

        if "_khoan-" in chunk_id:
            return chunk_id

        return None

    # ==========================================================
    # VIOLATION DETECTION
    # ==========================================================

    def _detect_violation(
        self,
        text: str,
    ) -> set[str]:
        normalized = self._normalize(text)

        detected = set()

        for violation, patterns in (
            self.VIOLATION_PATTERNS.items()
        ):
            if any(
                re.search(pattern, normalized)
                for pattern in patterns
            ):
                detected.add(violation)

        return detected

    # ==========================================================
    # QUERY ROLE DETECTION
    # ==========================================================

    def _detect_role(
        self,
        question: str,
    ) -> str | None:
        """
        Detect the person whose legal responsibility
        is being asked about.

        Distinguish:
            driver
            passenger
            driver_responsible_for_passenger
        """
        text = self._normalize(question)

        driver_pattern = (
            r"người điều khiển|người lái|"
            r"tài xế|lái xe"
        )

        passenger_pattern = (
            r"người được chở|người ngồi sau|"
            r"người ngồi trên xe|hành khách"
        )

        driver_mentioned = bool(
            re.search(driver_pattern, text)
        )

        passenger_mentioned = bool(
            re.search(passenger_pattern, text)
        )

        # Driver is explicitly responsible for carrying
        # a passenger who violates helmet requirements.
        driver_responsibility_patterns = [
            (
                r"(?:người lái|người điều khiển|"
                r"tài xế|lái xe).*?"
                r"(?:chở|đèo).*?"
                r"(?:người|hành khách|ngồi sau)"
            ),
            (
                r"(?:chở|đèo).*?"
                r"(?:người ngồi sau|người được chở|"
                r"hành khách).*?"
                r"(?:không đội mũ|không cài quai)"
            ),
        ]

        if driver_mentioned and passenger_mentioned:
            if any(
                re.search(pattern, text)
                for pattern in driver_responsibility_patterns
            ):
                return "driver_responsible_for_passenger"

            # Both roles appear, but responsibility is unclear.
            return None

        if passenger_mentioned:
            return "passenger"

        if driver_mentioned:
            return "driver"

        return None

    # ==========================================================
    # EVIDENCE ROLE DETECTION
    # ==========================================================

    def _detect_evidence_role(
        self,
        context: dict,
    ) -> str | None:
        """
        Detect legal responsibility described by evidence.

        Explicitly recognized evidence metadata takes
        precedence over heuristic text classification.
        """
        chunk_id = context.get("chunk_id")

        known = self.KNOWN_EVIDENCE.get(chunk_id)

        if known is not None:
            return known["role"]

        violation = self._normalize(
            context.get("violation")
            or context.get("content")
            or ""
        )

        preamble = self._normalize(
            context.get("clause_preamble")
            or ""
        )

        if re.search(
            r"chở người.*?(?:không đội|không cài)|"
            r"chở người ngồi trên xe",
            violation,
        ):
            return "driver_responsible_for_passenger"

        if (
            "người được chở" in violation
            or "người được chở" in preamble
        ):
            return "passenger"

        if (
            "khi điều khiển xe" in violation
            or "người điều khiển" in violation
            or "người điều khiển" in preamble
        ):
            return "driver"

        return None

    # ==========================================================
    # VERIFIED FINE METADATA
    # ==========================================================

    def _detect_violation_key(
        self,
        context: dict,
        evidence_role: str | None,
    ) -> str | None:
        """
        Assign a fine lookup key only to known evidence.

        Unknown evidence must not receive a guessed key.
        """
        chunk_id = context.get("chunk_id")

        known = self.KNOWN_EVIDENCE.get(chunk_id)

        if known is None:
            return None

        if known["role"] != evidence_role:
            return None

        return known["violation_key"]

    def _resolve_context_vehicle(
        self,
        context: dict,
    ) -> str | None:
        """
        Resolve vehicle type from context metadata.

        For explicitly mapped evidence, use the known
        legal classification.

        Never infer the evidence vehicle from the question.
        """
        chunk_id = context.get("chunk_id")

        known = self.KNOWN_EVIDENCE.get(chunk_id)

        existing = self._normalize_vehicle(
            context.get("vehicle_type")
        )

        if known is None:
            return existing

        expected = known["vehicle_type"]

        # Contradictory metadata must not be silently
        # replaced with the known mapping.
        if existing is not None and existing != expected:
            return existing

        return expected

    # ==========================================================
    # COMPATIBILITY CHECKS
    # ==========================================================

    def _is_vehicle_compatible(
        self,
        query_vehicle: str | None,
        context_vehicle: str | None,
    ) -> bool:
        query_vehicle = self._normalize_vehicle(
            query_vehicle
        )

        context_vehicle = self._normalize_vehicle(
            context_vehicle
        )

        if (
            query_vehicle is None
            or context_vehicle is None
        ):
            return True

        return query_vehicle == context_vehicle

    @staticmethod
    def _is_role_compatible(
        query_role: str | None,
        context_role: str | None,
    ) -> bool:
        if (
            query_role is None
            or context_role is None
        ):
            return True

        return query_role == context_role

    @staticmethod
    def _is_violation_compatible(
        query_violations: set[str],
        context_violations: set[str],
    ) -> bool:
        if not query_violations:
            return True

        if not context_violations:
            return False

        return bool(
            query_violations.intersection(
                context_violations
            )
        )

    # ==========================================================
    # SCORE CALCULATION
    # ==========================================================

    def _calculate_score(
        self,
        retrieval_score: float,
        query_vehicle: str | None,
        context_vehicle: str | None,
        query_role: str | None,
        context_role: str | None,
        query_violations: set[str],
        context_violations: set[str],
    ) -> tuple[float, dict]:

        vehicle_score = 0.0
        role_score = 0.0
        violation_score = 0.0

        if (
            query_vehicle is not None
            and query_vehicle == context_vehicle
        ):
            vehicle_score = 0.03

        if (
            query_role is not None
            and query_role == context_role
        ):
            role_score = 0.02

        if (
            query_violations
            and query_violations.intersection(
                context_violations
            )
        ):
            violation_score = 0.04

        breakdown = {
            "retrieval": retrieval_score,
            "vehicle": vehicle_score,
            "role": role_score,
            "violation": violation_score,
        }

        return (
            sum(breakdown.values()),
            breakdown,
        )

    # ==========================================================
    # MAIN EVIDENCE SELECTION
    # ==========================================================

    def select(
        self,
        question: str,
        contexts: list[dict],
    ) -> dict[str, Any]:

        if not isinstance(question, str):
            raise TypeError(
                "question must be a string"
            )

        if not isinstance(contexts, list):
            raise TypeError(
                "contexts must be a list"
            )

        query_vehicle = self._normalize_vehicle(
            self.vehicle_detector.detect(question)
        )

        query_role = self._detect_role(question)

        query_violations = self._detect_violation(
            question
        )

        candidates = []
        rejected = []

        for context in contexts:

            if not isinstance(context, dict):
                continue

            try:
                retrieval_score = float(
                    context.get("retrieval_score")
                    or 0.0
                )
            except (TypeError, ValueError):
                retrieval_score = 0.0

            if not math.isfinite(retrieval_score):
                retrieval_score = 0.0

            if retrieval_score < self.min_score:
                continue

            chunk_id = context.get("chunk_id")

            context_vehicle = (
                self._resolve_context_vehicle(context)
            )

            context_role = (
                self._detect_evidence_role(context)
            )

            violation_text = (
                context.get("violation")
                or context.get("content")
                or ""
            )

            context_violations = (
                self._detect_violation(
                    violation_text
                )
            )

            rejection_reasons = []

            # Check contradictory metadata against
            # explicitly known evidence classification.
            known = self.KNOWN_EVIDENCE.get(chunk_id)

            if known is not None:
                existing_vehicle = self._normalize_vehicle(
                    context.get("vehicle_type")
                )

                if (
                    existing_vehicle is not None
                    and existing_vehicle
                    != known["vehicle_type"]
                ):
                    rejection_reasons.append(
                        "known_evidence_vehicle_conflict"
                    )

            if not self._is_vehicle_compatible(
                query_vehicle,
                context_vehicle,
            ):
                rejection_reasons.append(
                    "vehicle_mismatch"
                )

            if not self._is_role_compatible(
                query_role,
                context_role,
            ):
                rejection_reasons.append(
                    "role_mismatch"
                )

            if not self._is_violation_compatible(
                query_violations,
                context_violations,
            ):
                rejection_reasons.append(
                    "violation_mismatch"
                )

            if rejection_reasons:
                rejected.append({
                    "chunk_id": chunk_id,
                    "reasons": rejection_reasons,
                })
                continue

            score, breakdown = (
                self._calculate_score(
                    retrieval_score=retrieval_score,
                    query_vehicle=query_vehicle,
                    context_vehicle=context_vehicle,
                    query_role=query_role,
                    context_role=context_role,
                    query_violations=query_violations,
                    context_violations=context_violations,
                )
            )

            violation_key = (
                self._detect_violation_key(
                    context=context,
                    evidence_role=context_role,
                )
            )

            clause_id = (
                context.get("clause_id")
                or self._extract_clause_id(chunk_id)
            )

            candidates.append({
                **context,
                "clause_id": clause_id,
                "vehicle_type": context_vehicle,
                "evidence_role": context_role,
                "role": context_role,
                "violation_key": violation_key,
                "evidence_score": score,
                "score_breakdown": breakdown,
                "matched_violations": sorted(
                    query_violations.intersection(
                        context_violations
                    )
                ),
            })

        candidates.sort(
            key=lambda item: item["evidence_score"],
            reverse=True,
        )

        selected = candidates[
            :self.max_evidence
        ]

        return {
            "question": question,
            "query_vehicle": query_vehicle,
            "query_role": query_role,
            "query_violations": sorted(
                query_violations
            ),
            "selected_evidence": selected,
            "rejected_evidence": rejected,
            "requires_clarification": (
                not bool(selected)
            ),
        }