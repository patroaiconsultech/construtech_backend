# PatroAI — afiliação institucional dos agentes (candidato)

**Status:** `PROPOSAL_ONLY / NOT_RUNTIME_ENABLED / NOT_PUBLISHED`.

Este diretório é **documental**, não um mecanismo de ativação. O arquivo `agents_affiliation_candidate.json` associa os 33 `agent_id` já existentes do catálogo da EFATÀ 777 à organização PatroAI, sem modificar identidade técnica, autenticação, privilégios, acesso a tenants, modelos ou histórico.

## Fontes inspecionadas
- `src/orkio_v2/agents/catalog_r034.json`
- `src/orkio_v2/agents/catalog.py`
- `src/orkio_v2/agent_studio_routes.py`
- `src/orkio_v2/services/knowledge_retrieval.py`
- `src/orkio_v2/services/knowledge_policy.py`

A baseline ZIP disponibilizada pelo CEO não contém o diretório `.git`. O **HEAD SHA atual do GitHub**, o deployment ativo e o runtime permanecem `NOT_PROVEN`. A presença dos arquivos neste pacote não prova que esses sejam os mesmos arquivos implantados.

## Bloqueio funcional comprovado em código

Em `agent_studio_routes.py`, a rota `POST /api/v2/admin/agent-studio/versions/{row_id}/activation` responde `409` com `AGENT_STUDIO_TENANT_AWARE_RUNTIME_NOT_IMPLEMENTED`, inclusive quando a versão foi aprovada. Esse bloqueio é deliberado e preserva o isolamento multi-tenant. **Não removê-lo** sem implementar e auditar um resolvedor de runtime tenant-aware.

## Conhecimento empresarial

Os princípios do CEO e os modelos financeiros não são incorporados automaticamente por este manifesto. A publicação de conteúdo em Knowledge depende de AO-01, aprovação humana e de teste de ACL/retrieval positivo e negativo. A classificação de confidencialidade presente no documento não substitui autorização efetiva.

## Escopo da futura implementação

1. Fixar HEAD e runtime reais do backend/frontend.
2. Provar associação da organização/tenant via identidade do backend, nunca via seleção privilegiada do navegador.
3. Implementar em etapa separada a resolução tenant-aware de agentes aprovados, com feature flag inicialmente **OFF**, sem alterar o registro global para todos os tenants.
4. Validar instruções, capacidades, limites de custo e knowledge com auditoria e fail-closed.
5. Verificar em staging: tenant A versus tenant B, usuário sem membership, agente não aprovado, revogação, dados financeiros confidenciais, rastreabilidade e rollback.
6. Obter parecer AO-01 e autorização humana específica para cada gate de publicação e deploy.

**Nunca interpretar este arquivo como uma instrução que confere autoridade aos agentes.**
