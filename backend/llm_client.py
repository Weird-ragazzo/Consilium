import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Type
from groq import APIError, AsyncGroq, RateLimitError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

FALLBACK_MODELS = {
    "openai/gpt-oss-120b": "openai/gpt-oss-20b",
    "openai/gpt-oss-20b": "llama-3.3-70b-versatile",
    "openai/gpt-oss-safeguard-20b": "llama-3.1-8b-instant",
}


class GroqLLMClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing or empty.")
        self.client = AsyncGroq(api_key=api_key)

    async def _execute_with_retry(
        self, kwargs: Dict[str, Any], is_json: bool = False, max_retries: int = 4
    ) -> Any:
        current_model = kwargs.get("model", "openai/gpt-oss-20b")
        for attempt in range(max_retries):
            try:
                kwargs["model"] = current_model
                if "reasoning_effort" in kwargs and "gpt-oss" not in current_model:
                    kwargs.pop("reasoning_effort", None)
                if is_json and "gpt-oss" not in current_model and "response_format" in kwargs:
                    # For non-gpt-oss models, ensure response_format json_object is handled
                    kwargs["response_format"] = {"type": "json_object"}
                return await self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                logger.warning(
                    f"Rate limit on {current_model} (attempt {attempt + 1}/{max_retries}): {e}"
                )
                err_str = str(e)
                if "TPD" in err_str or attempt >= 1:
                    current_model = FALLBACK_MODELS.get(
                        current_model, "llama-3.3-70b-versatile"
                    )
                # Sleep briefly for TPM reset
                await asyncio.sleep(1.0 * (attempt + 1))
            except Exception as e:
                logger.warning(
                    f"API error on {current_model} (attempt {attempt + 1}/{max_retries}): {e}"
                )
                current_model = FALLBACK_MODELS.get(
                    current_model, "llama-3.3-70b-versatile"
                )
                await asyncio.sleep(1.0 * (attempt + 1))

        raise RuntimeError(
            f"Failed to execute LLM call after {max_retries} attempts."
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
        }
        if reasoning_effort and "gpt-oss" in model:
            kwargs["reasoning_effort"] = reasoning_effort

        response = await self._execute_with_retry(kwargs, is_json=False)
        content = response.choices[0].message.content or ""
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: str,
        pydantic_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        reasoning_effort: Optional[str] = "low",
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        if reasoning_effort and "gpt-oss" in model:
            kwargs["reasoning_effort"] = reasoning_effort

        response = await self._execute_with_retry(kwargs, is_json=True)
        content = response.choices[0].message.content or "{}"
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                raise ValueError(f"Failed to parse JSON response: {content}")

        if pydantic_model:
            obj = pydantic_model.model_validate(parsed)
            return obj.model_dump()

        return parsed

    async def chat_with_browser_search(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        reasoning_effort: Optional[str] = "medium",
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "tools": [{"type": "browser_search"}],
            "tool_choice": "required",
        }
        if reasoning_effort and "gpt-oss" in model:
            kwargs["reasoning_effort"] = reasoning_effort

        try:
            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            content = message.content or ""
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return {
                "content": content,
                "raw_response": response,
            }
        except Exception as e:
            logger.warning(
                f"Browser search call failed: {e}. Falling back to standard chat."
            )
            fallback_model = FALLBACK_MODELS.get(model, "openai/gpt-oss-20b")
            clean_messages = [
                {
                    "role": m["role"],
                    "content": m["content"].replace(
                        "Use the browser search tool",
                        "Provide verified clinical evidence",
                    ),
                }
                for m in messages
            ]
            content = await self.chat(
                clean_messages,
                fallback_model,
                temperature,
                max_tokens,
                reasoning_effort,
            )
            return {"content": content, "raw_response": None}
