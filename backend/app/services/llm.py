import logging
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1.0, 3.0)   # seconds to wait before retry 1 and retry 2


class LlmError(Exception):
    """Something went wrong talking to the LLM. The message is safe to show users."""


class LlmNotConfigured(LlmError):
    pass


def is_configured() -> bool:
    return bool(settings.llm_base_url and settings.llm_model)


def chat(messages: list[dict]) -> str:
    """Send a chat request to any OpenAI-compatible endpoint and return the reply text."""
    if not is_configured():
        raise LlmNotConfigured("The AI service is not configured")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    payload: dict = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0,   # extraction should be repeatable, not creative
    }
    if settings.llm_json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        can_retry = attempt < len(RETRY_DELAYS)
        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=settings.llm_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            logger.warning("LLM request failed: %s", type(exc).__name__)
            if can_retry:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise LlmError("Could not reach the AI service") from exc

        if response.status_code in RETRY_STATUS and can_retry:
            time.sleep(RETRY_DELAYS[attempt])
            continue
        break

    if response.status_code != 200:
        logger.warning("LLM returned HTTP %s: %s", response.status_code, response.text[:300])
        raise LlmError(f"The AI service returned an error (HTTP {response.status_code})")

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LlmError("The AI service returned an unexpected response") from exc

    if not isinstance(content, str) or not content.strip():
        raise LlmError("The AI service returned an empty response")
    return content