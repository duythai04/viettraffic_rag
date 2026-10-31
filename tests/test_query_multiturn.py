from unittest.mock import Mock

from src.conversation.conversation_manager import ConversationManager
from src.pipelines.query_pipeline import QueryPipeline


def build_pipeline():
    retriever = Mock()
    retriever.retrieve.return_value = []
    intent = Mock()
    intent.detect.return_value = "legal_fine"
    detector = Mock()
    detector.detect.side_effect = lambda q: {
        "requires_clarification": "15 km/h" not in q,
        "reason": "missing_speed_excess" if "15 km/h" not in q else None,
        "message": "Bạn vượt tốc độ bao nhiêu km/h?",
    }
    manager = ConversationManager()
    pipeline = QueryPipeline(
        retriever=retriever,
        answer_generator=Mock(),
        intent_detector=intent,
        evidence_selector=Mock(),
        clarification_detector=detector,
        conversation_manager=manager,
    )
    return pipeline, manager, retriever


def test_multiturn_resolves_followup_and_retrieves():
    pipeline, manager, retriever = build_pipeline()
    sid = manager.create_session()
    first = pipeline.run("Xe máy chạy quá tốc độ bị phạt bao nhiêu?", session_id=sid, debug=True)
    assert first["requires_clarification"] is True
    retriever.retrieve.assert_not_called()

    second = pipeline.run("15 km/h", session_id=sid, debug=True)
    assert second["requires_clarification"] is False
    assert "15 km/h" in second["rewritten_question"]
    assert second["original_question"] == "15 km/h"
    assert manager.get_session(sid).pending_question is None
    retriever.retrieve.assert_called_once()
    assert "15 km/h" in retriever.retrieve.call_args.args[0]


def test_without_session_still_works():
    pipeline, _, retriever = build_pipeline()
    result = pipeline.run("Xe máy chạy quá tốc độ bị phạt bao nhiêu?")
    assert result["requires_clarification"] is True
    assert "session_id" not in result
    retriever.retrieve.assert_not_called()


def test_invalid_followup_keeps_pending():
    pipeline, manager, retriever = build_pipeline()
    sid = manager.create_session()
    pipeline.run("Xe máy chạy quá tốc độ bị phạt bao nhiêu?", session_id=sid)
    result = pipeline.run("Tôi không biết", session_id=sid)
    assert result["requires_clarification"] is True
    assert manager.get_session(sid).pending_question is not None
    retriever.retrieve.assert_not_called()
