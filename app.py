"""Preview de investidor: contrato publico G2, sem modulo privado, banco ou CRM."""
from __future__ import annotations
import json
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from config import settings
from provider import generate_reply, ProviderError
from quota import consume, ready, QuotaUnavailable

MAX_BODY = 8192
MAX_MESSAGE = 1200
MAX_HISTORY = 6

app = FastAPI(title="CONSTRUTECH Investor Agent", version="G2-investor-preview",
              docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response

def reply(status: int, payload: dict):
    return JSONResponse(status_code=status, content=payload,
                        headers={"Cache-Control":"no-store"})

@app.get("/health/live")
def live():
    return {"status":"ok","service":"construtech-agent-preview","version":app.version}

@app.get("/health/ready")
async def readiness():
    is_ready = await ready()
    return reply(200 if is_ready else 503, {"status":"ready" if is_ready else "not_ready"})

@app.get("/api/v1/public/agent/status")
async def status():
    is_ready = await ready()
    return reply(200, {
        "available": is_ready,
        "kind":"public_consultative_chat_v1",
        "generative_ai":is_ready,
        "persisted":False,
        "crm_integration":False,
    })

def validate(value: object) -> tuple[str, list[dict[str,str]]]:
    if type(value) is not dict or set(value) != {"consent", "message", "history"}:
        raise ValueError("invalid_payload")
    if value["consent"] is not True:
        raise PermissionError("consent_required")
    msg=value["message"]
    hist=value["history"]
    if type(msg) is not str or not (1 <= len(msg.strip()) <= MAX_MESSAGE):
        raise ValueError("message_invalid")
    if type(hist) is not list or len(hist)>MAX_HISTORY:
        raise ValueError("history_invalid")
    for item in hist:
        if (type(item) is not dict or set(item) != {"role","content"}
            or type(item["role"]) is not str
            or item["role"] not in {"user","assistant"}
            or type(item["content"]) is not str
            or not (1 <= len(item["content"].strip()) <= MAX_MESSAGE)):
            raise ValueError("history_invalid")
    return msg.strip(), hist

@app.post("/api/v1/public/agent/chat")
async def chat(request:Request):
    if not settings.enabled:
        return reply(503, {"detail":"agent_unavailable"})
    if request.headers.get("origin") != settings.frontend_origin:
        return reply(403, {"detail":"agent_origin_forbidden"})
    if request.headers.get("content-type","").split(";",1)[0].strip().lower() != "application/json":
        return reply(415, {"detail":"agent_json_required"})
    length=request.headers.get("content-length")
    if length is not None and (not length.isdecimal() or int(length)>MAX_BODY):
        return reply(413, {"detail":"agent_payload_too_large"})
    raw=bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk)>MAX_BODY:
            return reply(413, {"detail":"agent_payload_too_large"})
        raw.extend(chunk)
    try:
        data=json.loads(raw)
    except (ValueError,UnicodeError):
        return reply(400, {"detail":"agent_invalid_json"})
    try:
        message,history=validate(data)
    except PermissionError:
        return reply(403, {"detail":"agent_consent_required"})
    except ValueError:
        return reply(422, {"detail":"invalid_agent_payload"})
    try:
        allowed=await consume()
    except QuotaUnavailable:
        return reply(503, {"detail":"agent_budget_unavailable"})
    if not allowed:
        return reply(429, {"detail":"agent_quota_exceeded"})
    request_id=request.headers.get("x-request-id","")
    if (not request_id or len(request_id)>128
       or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in request_id)):
        request_id=str(uuid.uuid4())
    try:
        text=await generate_reply(message,history,request_id)
    except ProviderError:
        return reply(503, {"detail":"agent_provider_unavailable"})
    return reply(200,{
        "kind":"public_consultative_chat_v1",
        "reply":text,
        "persisted":False,
        "crm_sent":False,
        "lead_created":False
    })
