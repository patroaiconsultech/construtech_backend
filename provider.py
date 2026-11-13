"""OpenAI Responses API, sem historico persistido nem tools."""
from typing import Any
import httpx
from config import settings
from prompt import INSTRUCTIONS

class ProviderError(Exception):
    pass

def extract_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict) or payload.get("status") not in (None,"completed"):
        raise ProviderError("provider_response_invalid")
    pieces = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if isinstance(part,dict) and part.get("type")=="output_text":
                text = part.get("text")
                if isinstance(text,str) and text.strip():
                    pieces.append(text.strip())
    answer = "\n".join(pieces).strip()
    if not answer or len(answer) > 8000:
        raise ProviderError("provider_response_empty_or_large")
    return answer

async def generate_reply(message: str, history: list[dict[str,str]], request_id: str) -> str:
    payload = {
        "model": settings.model,
        "store": False,
        "instructions": INSTRUCTIONS,
        "input": [{"role":item["role"],"content":item["content"]} for item in history]
            + [{"role":"user","content":message}],
        "max_output_tokens": 750
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            reply = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type":"application/json",
                    "X-Client-Request-Id":request_id,
                },
                json=payload,
            )
        if reply.status_code != 200:
            raise ProviderError("provider_http_error")
        return extract_text(reply.json())
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise ProviderError("provider_unavailable") from exc
