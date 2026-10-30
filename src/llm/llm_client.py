from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int = 500,
    ):
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY chưa được cấu hình trong .env"
            )

        self.model = model or os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini",
        )

        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        self.client = OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt không được để trống.")

        instructions = system_prompt or (
            "Bạn là VietTraffic AI, trợ lý tra cứu "
            "pháp luật giao thông đường bộ Việt Nam. "
            "Chỉ sử dụng căn cứ pháp luật được cung cấp. "
            "Không tự tạo điều khoản, mức phạt hoặc "
            "thông tin pháp lý chưa được xác minh. "
            "Nếu thiếu căn cứ, hãy nói rõ giới hạn. "
            "Trả lời bằng tiếng Việt."
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            store=False,
        )

        answer = response.output_text.strip()

        if not answer:
            raise RuntimeError(
                "LLM không trả về nội dung."
            )

        return answer