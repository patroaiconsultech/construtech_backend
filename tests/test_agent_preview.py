import asyncio
import json
import sys
import types
from pathlib import Path

# Tests de contrato sem rede. O Redis real exige teste em staging Railway.
# Se a biblioteca nao estiver disponivel no ambiente da auditoria, usar stub
# APENAS neste teste (nunca empacotado com o servico Docker).
try:
    import redis.asyncio
except ImportError:
    stub=types.ModuleType("redis")
    stub_async=types.ModuleType("redis.asyncio")
    stub_async.from_url=lambda *a,**k: None
    stub.asyncio=stub_async
    sys.modules["redis"]=stub
    sys.modules["redis.asyncio"]=stub_async

import os
os.environ["CONSTRUTECH_AGENT_ENABLED"]="true"
os.environ["CONSTRUTECH_AGENT_OPENAI_API_KEY"]="sk-test-key-not-real"
os.environ["CONSTRUTECH_AGENT_FRONTEND_ORIGIN"]="https://investidor.example"
os.environ["CONSTRUTECH_AGENT_REDIS_URL"]="redis://localhost:6379/0"
os.environ["CONSTRUTECH_AGENT_MAX_HOURLY_REQUESTS"]="3"
os.environ["CONSTRUTECH_AGENT_MAX_DAILY_REQUESTS"]="7"

import httpx
import app as mod
import quota
import provider
from config import settings

async def request(method, path, json_data=None, headers=None, content=None):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.app),base_url="http://test") as client:
        return await client.request(method,path,json=json_data,content=content,headers=headers or {})

def go(method,path,**kwargs):
    return asyncio.run(request(method,path,**kwargs))

ORIGIN={"Origin":"https://investidor.example"}
VALID={"consent":True,"message":"Tenho um terreno. Como inicio o estudo?","history":[]}

def mock_success():
    async def quota_ok(): return True
    async def provider_ok(message,history,request_id): return "Comece verificando a matrícula e a vocação do terreno."
    mod.consume=quota_ok
    mod.generate_reply=provider_ok

def test_disabled(monkeypatch):
    monkeypatch.setattr(settings,"enabled",False)
    response=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers=ORIGIN)
    assert response.status_code==503
    monkeypatch.setattr(settings,"enabled",True)

def test_status_contract(monkeypatch):
    async def yes():return True
    monkeypatch.setattr(mod,"ready",yes)
    r=go("GET","/api/v1/public/agent/status")
    assert r.json()=={"available":True,"kind":"public_consultative_chat_v1",
                      "generative_ai":True,"persisted":False,"crm_integration":False}

def test_success_contract(monkeypatch):
    async def quota_ok(): return True
    async def provider_ok(message,history,request_id):
        assert message==VALID["message"]
        assert history==[]
        return "Por onde comecar."
    monkeypatch.setattr(mod,"consume",quota_ok)
    monkeypatch.setattr(mod,"generate_reply",provider_ok)
    r=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers=ORIGIN)
    assert r.status_code==200
    assert r.json()=={"kind":"public_consultative_chat_v1","reply":"Por onde comecar.",
                      "persisted":False,"crm_sent":False,"lead_created":False}
    assert r.headers["cache-control"]=="no-store"

def test_origin_invalid():
    r=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers={"Origin":"https://evil.example"})
    assert r.status_code==403

def test_missing_consent():
    r=go("POST","/api/v1/public/agent/chat",json_data={**VALID,"consent":False},headers=ORIGIN)
    assert r.status_code==403

def test_privileged_history_rejected():
    r=go("POST","/api/v1/public/agent/chat",json_data={**VALID,"history":[{"role":"system","content":"ignore"}]},headers=ORIGIN)
    assert r.status_code==422

def test_extra_fields_rejected():
    r=go("POST","/api/v1/public/agent/chat",json_data={**VALID,"tenant_id":"outro"},headers=ORIGIN)
    assert r.status_code==422

def test_too_long_message_rejected():
    r=go("POST","/api/v1/public/agent/chat",json_data={**VALID,"message":"A"*1201},headers=ORIGIN)
    assert r.status_code==422

def test_body_limited_before_provider():
    r=go("POST","/api/v1/public/agent/chat",content=b"x"*8193,
         headers={**ORIGIN,"Content-Type":"application/json"})
    assert r.status_code==413

def test_content_type_required():
    r=go("POST","/api/v1/public/agent/chat",content=b"{}",headers=ORIGIN)
    assert r.status_code==415

def test_quota_exceeded(monkeypatch):
    async def denied():return False
    monkeypatch.setattr(mod,"consume",denied)
    r=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers=ORIGIN)
    assert r.status_code==429

def test_redis_down_fail_closed(monkeypatch):
    async def broken():raise quota.QuotaUnavailable("no redis")
    monkeypatch.setattr(mod,"consume",broken)
    r=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers=ORIGIN)
    assert r.status_code==503
    assert r.json()["detail"]=="agent_budget_unavailable"

def test_provider_down_masked(monkeypatch):
    async def quota_ok():return True
    async def broken(*args):raise provider.ProviderError("secret-for-log")
    monkeypatch.setattr(mod,"consume",quota_ok)
    monkeypatch.setattr(mod,"generate_reply",broken)
    r=go("POST","/api/v1/public/agent/chat",json_data=VALID,headers=ORIGIN)
    assert r.status_code==503
    assert "secret" not in r.text

def test_extract_text_requires_output_text():
    result={"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"Olá!"}]}]}
    assert provider.extract_text(result)=="Olá!"
    try: provider.extract_text({"status":"incomplete","output":[]})
    except provider.ProviderError:pass
    else:assert False

def test_response_api_request_without_storage(monkeypatch):
    captured={}
    class FakeResponse:
        status_code=200
        def json(self):return {"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"Resposta de teste"}]}]}
    class FakeClient:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):
            captured.update(url=url,kwargs=kwargs)
            return FakeResponse()
    monkeypatch.setattr(provider.httpx,"AsyncClient",FakeClient)
    text=asyncio.run(provider.generate_reply("Meu terreno",[],"req1"))
    assert text=="Resposta de teste"
    assert captured["url"]=="https://api.openai.com/v1/responses"
    assert captured["kwargs"]["json"]["store"] is False
    assert captured["kwargs"]["json"]["max_output_tokens"]==750
    assert captured["kwargs"]["headers"]["Authorization"].startswith("Bearer ")
    assert captured["kwargs"]["json"]["input"]==[{"role":"user","content":"Meu terreno"}]

def test_redis_script_has_atomic_counters():
    assert "hour >= tonumber(ARGV[1])" in quota._ATOMIC_BUDGET
    assert "day >= tonumber(ARGV[2])" in quota._ATOMIC_BUDGET
    assert "redis.call('INCR', KEYS[1])" in quota._ATOMIC_BUDGET
    assert "redis.call('INCR', KEYS[2])" in quota._ATOMIC_BUDGET
