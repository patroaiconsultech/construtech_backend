# CONSTRUTECH — backend de IA (prévia comercial G2)

Este repositório está sendo corrigido: antes continha um frontend Node por engano.
O Dockerfile agora é **Python/FastAPI** e copia **somente** os módulos necessários
ao agente, ignorando os arquivos antigos da landing ainda presentes no Git.
A remoção desses arquivos legados deve ser feita em uma revisão separada.

Escopo: agente consultivo público da landing. Não há PostgreSQL, cadastro de
clientes, persistência de conversa, CRM nem motor financeiro homologado.

## Contratos HTTP

- `GET /health/live`: processo iniciado
- `GET /health/ready`: Redis acessível e agente habilitado
- `GET /api/v1/public/agent/status`: estado do agente
- `POST /api/v1/public/agent/chat`: JSON com `consent`, `message`, `history`.
  Só aceita Origin da landing configurada. Não envia nem persiste leads.

## Railway

No serviço `construtech_backend`, manter origem
`patroaiconsultech/construtech_backend`, diretório raiz `/` e Dockerfile
na raiz. Healthcheck: `/health/live`; porta interna `8080`.
Sem start command extra: usar CMD do Dockerfile.

Variáveis de backend (somente Variables do serviço):
- `PORT=8080`
- `CONSTRUTECH_AGENT_ENABLED=false` (habilitar após testes de Redis e orçamento)
- `CONSTRUTECH_AGENT_FRONTEND_ORIGIN=https://construtechfrontend-production.up.railway.app`
- `CONSTRUTECH_AGENT_REDIS_URL=${{Redis.REDIS_URL}}` quando o serviço chamar Redis
- `CONSTRUTECH_AGENT_MODEL=gpt-5.4-mini-2026-03-17`
- `CONSTRUTECH_AGENT_MAX_HOURLY_REQUESTS=20`
- `CONSTRUTECH_AGENT_MAX_DAILY_REQUESTS=80`
- `CONSTRUTECH_AGENT_OPENAI_API_KEY`: segredo, inserir no Railway; nunca no GitHub

Frontend Node precisa apontar `GLIP_BACKEND_URL` para o domínio privado do
serviço `construtech_backend` na porta 8080; não usar backend GLIP Premium.

## Gate

- Testes: `python -m pip install -r requirements.txt pytest==8.4.2`;
  `PYTHONPATH=. pytest -q` (Linux/macOS), `$env:PYTHONPATH='.'; pytest -q` (Windows)
- Testar `/health/live`, `/health/ready`, `/api/v1/public/agent/status`
  via rede privada e proxy do frontend.
- Habilitar somente após comprovar Redis real, limites de consumo e chave
  dedicada. `available:true` não substitui teste com resposta real.
- No Railway, usar build do commit mais recente, não redeploy de um build antigo.
- AO-01 deve revisar antes de qualquer GO público amplo.

Rollback: reverter o commit deste delta; isso restaura o estado anterior,
mas também restaura o Dockerfile incorreto e não deve ser promovido como serviço IA.
