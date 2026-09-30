import json

import httpx

from app.core.config import get_settings


class LLMError(Exception):
    pass


async def generate_structured(
    system_prompt: str, user_prompt: str, json_schema: dict, schema_name: str = "response"
) -> dict:
    """Call OpenRouter for a JSON-schema-shaped completion.

    The schema is passed as a best-effort hint (`response_format`); OpenRouter's
    strict-mode support varies by model and this schema can be recursive (rule
    trees), so callers MUST re-validate the returned dict themselves (e.g. via a
    Pydantic model) rather than trust this function's output as pre-validated.
    """
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMError("OPENROUTER_API_KEY is not configured")

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": False, "schema": json_schema},
        },
        "reasoning": {"enabled": False},
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(
        base_url=settings.openrouter_base_url, timeout=settings.openrouter_timeout_seconds
    ) as client:
        try:
            resp = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                json=payload,
            )
        except httpx.HTTPError as e:
            raise LLMError(f"OpenRouter request failed: {e}") from e

    if resp.status_code >= 400:
        raise LLMError(f"OpenRouter error {resp.status_code}: {resp.text[:500]}")

    try:
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as e:
        raise LLMError(f"Malformed OpenRouter response: {e}") from e
