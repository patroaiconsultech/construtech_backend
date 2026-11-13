"""Limites globais, atomicos, persistidos em Redis; falha = nao chamar IA.

As contagens sao agregadas e NAO armazenam IP, conteudo, cookie ou tenant.
"""
from datetime import datetime, timezone
import redis.asyncio as redis
from config import settings

# Verifica ambos os limites antes de consumir, sem corrida entre replicas.
_ATOMIC_BUDGET = """
local hour = tonumber(redis.call('GET', KEYS[1]) or '0')
local day = tonumber(redis.call('GET', KEYS[2]) or '0')
if hour >= tonumber(ARGV[1]) or day >= tonumber(ARGV[2]) then
  return 0
end
local hn = redis.call('INCR', KEYS[1])
if hn == 1 then redis.call('EXPIRE', KEYS[1], 3700) end
local dn = redis.call('INCR', KEYS[2])
if dn == 1 then redis.call('EXPIRE', KEYS[2], 90000) end
return 1
"""

class QuotaUnavailable(Exception):
    pass

async def _client():
    # Socket com timeout curto para falhar fechado quando o Redis estiver indisponivel.
    return redis.from_url(settings.redis_url, socket_connect_timeout=2.0,
                          socket_timeout=2.0, decode_responses=True)

async def ready() -> bool:
    if not settings.enabled:
        return False
    try:
        client = await _client()
        try:
            return bool(await client.ping())
        finally:
            await client.aclose()
    except Exception:
        return False

async def consume() -> bool:
    now = datetime.now(timezone.utc)
    key_hour = f"construtech:agent:requests:hour:{now:%Y%m%d%H}"
    key_day = f"construtech:agent:requests:day:{now:%Y%m%d}"
    try:
        client = await _client()
        try:
            result = await client.eval(
                _ATOMIC_BUDGET, 2, key_hour, key_day,
                settings.max_hourly_requests, settings.max_daily_requests)
            return int(result) == 1
        finally:
            await client.aclose()
    except Exception as exc:
        raise QuotaUnavailable("quota_store_unavailable") from exc
