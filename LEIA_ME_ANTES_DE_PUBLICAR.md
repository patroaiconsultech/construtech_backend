# EFATÀ 777 / PatroAI — pacote de preparação GitHub

**Data-base:** 13/11/2026  
**Status:** `PREPARED_NOT_DEPLOYED / PROPOSAL_ONLY / AO01_REVIEW_PENDING`  
**Atenção:** o arquivo de afiliação **não torna os agentes operacionais**.

Esta entrega está dividida em **dois arquivos ZIP separados**:

1. **PATROAI_AGENTES_GITHUB_PR_CANDIDATO_20261113.zip** — apenas `docs/patroai/`, `tools/`, `tests/`, este README e manifesto. Candidato de PR do backend; a publicação em repositório público ainda requer revisão de conteúdo e autorização.
2. **PATROAI_AGENTES_HANDOFF_PRIVADO_AO01_20261113.zip** — documentos de diretrizes e handoff de segurança **não destinados ao repositório público**. Submeter a AO-01 e manter em escopo protegido.

**Jamais envie o ZIP privado para um repositório público.** Não há migrations, alterações de autenticação, código de ativação ou migração de dados nesta entrega.

## Repositórios observados
- backend `https://github.com/patroaiconsultech/efata-777-backend-staging-web01`, branch `main` visível;
- frontend `https://github.com/patroaiconsultech/efata-777-frontend-staging-web01`, branch `main` visível.
Os SHAs atuais de HEAD e deploy runtime não foram comprovados. Os dois repositórios aparecem públicos. A baseline fornecida tem arquivos ZIP sem `.git`.

## Instalação por PR — somente após gate de identidade e revisão

Um operador autorizado fixa primeiro o commit de `origin/main` e compara arquivos com a baseline examinada. Ao preparar a branch, copie **somente** o conteúdo do ZIP público (pastas `docs/`, `tools/`, `tests/`) para a raiz do repositório backend:

```sh
git fetch origin main
git status --porcelain
git rev-parse origin/main
git switch -c dg01/patroai-agents-governance-r1 origin/main
# Copiar apenas arquivos e pastas do GITHUB_BACKEND_OVERLAY/ para este repositório.
python tools/validate_patroai_agent_manifest.py --manifest docs/patroai/agents_affiliation_candidate.json --catalog src/orkio_v2/agents/catalog_r034.json
python -m unittest discover -s tests -p 'test_patroai_agent_manifest.py' -v
git diff --stat
git diff --check
```

Não executar `git add/commit/push`, abrir PR, mergear, migrar ou implantar automaticamente com base neste documento. Exigir autorização e evidências para cada gate.

## Primeira divergência causal no código de referência

`agent_studio_routes.activate_agent_studio_version` retorna HTTP 409 `AGENT_STUDIO_TENANT_AWARE_RUNTIME_NOT_IMPLEMENTED`. O controle protege contra ativação de agente por tenant sem resolvedor seguro. **Não contornar**.

O próximo patch efetivamente funcional dependerá de implementar um resolvedor tenant-aware no backend (e testá-lo em execução), verificando source HEAD, contratos, roles, tenant, tools e knowledge. Não foi construído aqui sem target/runtime comprovado.

## Gates para efetividade

`SOURCE_PINNED → GOVERNANCE_PR → AO01_REVIEW → TENANT_AWARE_RESOLVER_PATCH → POSTGRES_TESTS → STAGING_RUNTIME → CEO_APPROVAL → DEPLOYMENT → AUDITED_AGENT_EXECUTION`.

A publicação da Memória Mestre, a aprovação econômica e a ativação permanecem **NO-GO**.
