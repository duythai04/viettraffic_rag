from src.llm.llm_client import LLMClient


def main():
    print("Initializing GPT-4o mini...")

    llm = LLMClient()

    print("Model:", llm.model)

    question = (
        "Hãy giới thiệu ngắn gọn về VietTraffic AI, "
        "một trợ lý tra cứu pháp luật giao thông Việt Nam."
    )

    print("\nQuestion:")
    print(question)

    answer = llm.generate(
        prompt=question,
    )

    print("\n========== LLM ANSWER ==========")
    print(answer)


if __name__ == "__main__":
    main()