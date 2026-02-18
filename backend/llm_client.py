import re

from openai import AsyncOpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        # Strip <think>...</think> blocks that DeepSeek R1 may produce
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content
