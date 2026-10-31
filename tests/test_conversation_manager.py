from src.conversation.conversation_manager import (
    ConversationManager,
)


def test_create_session():

    manager = ConversationManager()

    session_id = manager.create_session()

    session = manager.get_session(session_id)

    assert session is not None

    assert session.session_id == session_id

    assert session.pending_question is None


def test_save_clarification():

    manager = ConversationManager()

    session_id = manager.create_session()

    manager.save_clarification(
        session_id=session_id,
        question="Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        reason="missing_speed_excess",
    )

    session = manager.get_session(session_id)

    assert session.pending_question is not None

    assert session.clarification_reason == "missing_speed_excess"


def test_resolve_speed_followup():

    manager = ConversationManager()

    session_id = manager.create_session()

    manager.save_clarification(
        session_id=session_id,
        question="Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        reason="missing_speed_excess",
    )

    rewritten = manager.resolve_followup(
        session_id=session_id,
        message="15 km/h",
    )

    assert rewritten is not None

    assert "15 km/h" in rewritten

    assert manager.get_session(session_id).pending_question is None


def test_invalid_followup():

    manager = ConversationManager()

    session_id = manager.create_session()

    manager.save_clarification(
        session_id=session_id,
        question="Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        reason="missing_speed_excess",
    )

    rewritten = manager.resolve_followup(
        session_id=session_id,
        message="Tôi không biết",
    )

    assert rewritten is None

    assert manager.get_session(session_id).pending_question is not None


def test_clear_session():

    manager = ConversationManager()

    session_id = manager.create_session()

    manager.clear_session(session_id)

    assert manager.get_session(session_id) is None
