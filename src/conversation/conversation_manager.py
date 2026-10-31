from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ConversationState:
    session_id: str
    pending_question: str | None = None
    clarification_reason: str | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ConversationManager:

    SPEED_PATTERN = re.compile(
        r"^\s*(\d+(?:[.,]\d+)?)\s*"
        r"(?:km/h|kmh|km/giờ)\s*[.!?]?\s*$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.sessions: dict[str, ConversationState] = {}

    def create_session(self) -> str:
        session_id = str(uuid4())

        self.sessions[session_id] = ConversationState(
            session_id=session_id
        )

        return session_id

    def get_session(
        self,
        session_id: str,
    ) -> ConversationState | None:
        return self.sessions.get(session_id)

    def save_clarification(
        self,
        session_id: str,
        question: str,
        reason: str,
    ) -> None:

        session = self.get_session(session_id)

        if session is None:
            raise ValueError("Session not found")

        session.pending_question = question
        session.clarification_reason = reason

    def resolve_followup(
        self,
        session_id: str,
        message: str,
    ) -> str | None:

        session = self.get_session(session_id)

        if session is None:
            return None

        if session.pending_question is None:
            return None

        if session.clarification_reason != "missing_speed_excess":
            return None

        match = self.SPEED_PATTERN.fullmatch(message)

        if not match:
            return None

        speed = match.group(1).replace(",", ".")

        original_question = session.pending_question

        rewritten_question = (
            f"{original_question} "
            f"Mức vượt quá tốc độ cho phép là {speed} km/h."
        )

        session.pending_question = None
        session.clarification_reason = None

        return rewritten_question

    def clear_session(
        self,
        session_id: str,
    ) -> None:
        self.sessions.pop(session_id, None)
