# CONSTRUTECH — Registro de continuidade do Investor Intelligence

**Data:** 18/11/2026 · **Responsável técnico:** DG-01 · **Estado:** PAUSADO POR PRIORIZAÇÃO COMERCIAL

## Decisão de produto
Priorizar captação de clientes incorporadores, motor de viabilidade econômico-financeira de empreendimentos e, depois, gestão de empreendimentos. O portal institucional de investidores permanece no roadmap e não será descartado. Não há autorização de deploy implícita neste registro.

## Último marco
- DR02: candidata privada local com perfis, convites, sessões, NDA demonstrativo, permissões por documento/versão, revisão, criptografia e auditoria.
- DR03: leitura privada interna, bloqueio do download original para perfis externos e prévia administrativa reservada.
- DR04: gestão empresarial administrativa com lançamentos, estornos, metas e revisões de projeções; planejado, realizado e projetado separados.
- Evidência de usuário: login administrativo e convite/cadastro funcionaram localmente; nova interface DR04 carregou no Windows. Regressão financeira completa em Windows e autorização documental no navegador pendentes.
- Relatórios de entrega registram testes HTTP locais para DR02/DR03/DR04; não equivalem a homologação independente, PostgreSQL ou produção.

## Retomada futura
1. Recuperar os artefatos DR02, DR03 e DR04 do acervo privado autorizado e checar manifesto, hashes, banco e código. Não recriar o ambiente por tentativa.
2. Reproduzir a execução local e validar cálculos, persistência, estornos e permissões de leitura; investigar a pendência de publicação/autorização documental.
3. Construir portal navegável e publicação versionada de conteúdo e indicadores autorizados. Preservar o planejamento original; distinguir fatos, projeções e hipóteses.
4. Homologar PostgreSQL, migrações, isolamento, armazenamento, backups, MFA/identidade, sessões, e-mail, logs e NDA revisado.
5. Investor IA: recuperar apenas conteúdo autorizado, revalidar acesso, manter fontes/versões e bloquear exfiltração. Sem envio de conteúdo confidencial sem autorização.
6. Revisão AO-01, aprovação humana, staging HTTPS e gates independentes antes de uso externo.

## Preservação
Não publicar dados pessoais, bancos locais, backups, chaves, senhas, acervo de investidores, referências de terceiros ou planilhas confidenciais. Manter os pacotes de implementação e a custódia em armazenamento privado controlado. Este registro deliberadamente não contém valores financeiros ou detalhes de credenciais.
A landing e o agente público permanecem separados do portal privado. Não alterar ambientes operacionais para arquivar o módulo.

**Próxima linha de produto:** VIA — viabilidade imobiliária, seguida de gestão de empreendimentos.  
**Gate do portal institucional:** NO-GO externo até homologação. **Status deste registro:** pronto para revisão e versionamento documental.
