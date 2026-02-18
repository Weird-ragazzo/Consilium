import asyncio

from backend.config import settings
from backend.llm_client import LLMClient
from backend.models import CouncilResponse, ModelResponse
from backend.prompts import (
    CRITIQUE_USER_TEMPLATE,
    REVISE_USER_TEMPLATE,
    SYSTEM_PROMPT_CRITIQUE,
    SYSTEM_PROMPT_GENERATE,
    SYSTEM_PROMPT_REVISE,
)


def _build_clients() -> tuple[LLMClient, LLMClient]:
    client_a = LLMClient(
        api_key=settings.nvidia_api_key_llama,
        base_url=settings.nvidia_base_url,
        model=settings.model_a,
    )
    client_b = LLMClient(
        api_key=settings.nvidia_api_key_llama2,
        base_url=settings.nvidia_base_url,
        model=settings.model_b,
    )
    return client_a, client_b


async def run_council(prompt: str) -> CouncilResponse:
    client_a, client_b = _build_clients()

    # Phase 1: Generate — both models respond in parallel
    response_a, response_b = await asyncio.gather(
        client_a.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_GENERATE},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
        client_b.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_GENERATE},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
    )

    # Phase 2: Critique — A critiques B's response, B critiques A's response
    critique_from_a, critique_from_b = await asyncio.gather(
        client_a.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CRITIQUE},
                {
                    "role": "user",
                    "content": CRITIQUE_USER_TEMPLATE.format(
                        prompt=prompt, response=response_b
                    ),
                },
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
        client_b.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CRITIQUE},
                {
                    "role": "user",
                    "content": CRITIQUE_USER_TEMPLATE.format(
                        prompt=prompt, response=response_a
                    ),
                },
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
    )

    # Phase 3: Revise — each model revises using the other's critique
    # A gets critique_from_b (B critiqued A's response)
    # B gets critique_from_a (A critiqued B's response)
    final_a, final_b = await asyncio.gather(
        client_a.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_REVISE},
                {
                    "role": "user",
                    "content": REVISE_USER_TEMPLATE.format(
                        prompt=prompt,
                        own_response=response_a,
                        critique=critique_from_b,
                    ),
                },
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
        client_b.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_REVISE},
                {
                    "role": "user",
                    "content": REVISE_USER_TEMPLATE.format(
                        prompt=prompt,
                        own_response=response_b,
                        critique=critique_from_a,
                    ),
                },
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        ),
    )

    return CouncilResponse(
        prompt=prompt,
        model_a=ModelResponse(
            model_name="Llama 4 Scout",
            model_id=settings.model_a,
            initial_response=response_a,
            critique_received=critique_from_b,
            final_response=final_a,
            was_revised=final_a.strip() != response_a.strip(),
        ),
        model_b=ModelResponse(
            model_name="Llama 3.1 8B",
            model_id=settings.model_b,
            initial_response=response_b,
            critique_received=critique_from_a,
            final_response=final_b,
            was_revised=final_b.strip() != response_b.strip(),
        ),
        phases_completed=["generate", "critique", "revise"],
    )
