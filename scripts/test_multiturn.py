from scripts.test_real_rag import build_pipeline


def main():
    pipeline = build_pipeline()

    session_id = pipeline.conversation_manager.create_session()

    questions = [
        "Xe máy chạy quá tốc độ bị phạt bao nhiêu?",
        "15 km/h",
    ]

    for question in questions:
        print(f"\nUSER: {question}")

        result = pipeline.run(
            question=question,
            session_id=session_id,
            debug=True,
        )

        print(f"VIETTRAFFIC AI: {result['answer']}")
        print(
            "Requires clarification:",
            result.get("requires_clarification", False),
        )

        if result.get("rewritten_question"):
            print(
                "Rewritten question:",
                result["rewritten_question"],
            )

        print("Verified:", result.get("verified"))
        print("Citations:", result.get("citations", []))


if __name__ == "__main__":
    main()
