# Gate 5 — Plano de aceite do Alpha Python

- **Estado:** execução em andamento; 5.8 publicado em `v0.1.0a6`; 5.9.2 bloqueou a sessão e a candidata corretiva local `0.1.0a7` aguarda checkpoint de publicação
- **Responsável pela decisão final:** Lucas
- **Ambiente de referência:** Windows, Docker Desktop com backend WSL2 e Python 3.13 suportado pelo package
- **Inventário mecânico:** `docs/project/gates/gate-05-evidence-inventory.json` — decisão continua pendente e humana

## Critérios obrigatórios

| ID | Critério | Evidência esperada | Estado |
|---|---|---|---|
| G5-01 | Wheel instala e executa fora do checkout | sessão limpa + CI de package audit | Atendido: wheel e sdist `0.1.0a6` auditados, instalação limpa aprovada e pré-release publicada |
| G5-02 | Demo completa funciona sem chave e sem rede de provider | Smoke Dataset + secret ausente | Atendido no 5.5: 20/20 keyless local e na CI, com secret scan verde |
| G5-03 | WF-001 live usa a mesma porta, policies e budgets do demo | contract tests + live smoke manual | Atendido no 5.4: contratos falsos + smoke real autorizado |
| G5-04 | Perfil Python executa `pytest` somente em Docker | manifest + integração | Atendido: fluxo combinado público executa pytest/oracle no Docker local e na CI |
| G5-05 | Análise, riscos, cenários, testes e resultados são rastreáveis | report + schema/contract tests | Atendido no 5.8.6: cadeia tipada, parser e JSON Schema Draft 2020-12 reconciliados no wheel e aprovados na CI |
| G5-06 | Oracle curado não entra no prompt e é independente do teste gerado | payload test + hashes + fixtures | Atendido no 5.3: integração Docker, workspaces e evidências independentes |
| G5-07 | `TEST_ERROR` permite no máximo duas correções somente no teste | casos de correção e exaustão | Atendido: SMK-006 prova uma correção após erro de coleta e regressões mantêm o limite |
| G5-08 | `SUT_DEFECT_SUSPECTED` exige evidência independente e revisão humana | SUT defeituoso + oracle + checkpoint | Atendido localmente e exposto no SMK-007 público, sem correção do SUT |
| G5-09 | Policy, budget, infraestrutura e resultado funcional são distintos | matriz de outcomes/exit codes | Atendido: contratos, exits públicos e SMK-008/009/010 preservam as distinções |
| G5-10 | `SMK-001` a `SMK-010` são executáveis e reproduzíveis em demo | relatório agregado 10/10 | Atendido: 20/20 em duas repetições e fingerprints estáveis localmente e na CI |
| G5-11 | `SEC-001` a `SEC-012` passam no ambiente de referência | job Docker/security 12/12 | Atendido no 5.7: Windows 12/12 e job público `alpha-security` verde com prova Linux de symlink/cleanup recursivo |
| G5-12 | Coverage Python é normalizada com escopo e limitações | fixture de conformance + report | Atendido no 5.6: JSON nativo, linhas/branches exatos, report e SUT de referência aprovados localmente e na CI |
| G5-13 | Mutation Python é normalizada e limitada por budget | fixture conhecida + timeout test | Atendido no 5.6: admissão antes da execução, hard timeout, estados reconciliados e baseline aprovados localmente e na CI |
| G5-14 | Reports JSON e Markdown separam fatos, inferências e recomendações | schema + revisão de conteúdo | Atendido no 5.8.6: JSON normativo, Markdown derivado e auditor instalado 9/9, aprovados na CI |
| G5-15 | Logs/evidências são correlacionados, limitados e sem secrets | test logs + secret scan | Atendido no 5.7: policy 1.0.0, cleanup, tombstones, debug, scanner e artifacts sanitizados aprovados localmente e no `alpha-security` |
| G5-16 | `asef doctor` diagnostica requisitos sem expor credenciais | CLI end-to-end | Atendido no 5.7: 12 checks, wheel isolado e validação pública no `alpha-security` aprovados |
| G5-17 | Core não importa Python tooling, Docker, OpenAI ou LangGraph | import boundaries + job core mínimo | Atendido até `v0.1.0a6`: fronteiras AST e job core aprovados |
| G5-18 | README, quickstart, tutorial, arquitetura, segurança e limitações refletem o Alpha real | auditoria documental | Bloqueio externo: a candidata local `0.1.0a7` corrige os três documentos e passou no ensaio instalado, mas `v0.1.0a6` permanece a release imutável divergente; `PREFLIGHT-F-001` alto aberto até publicar e baixar novamente os novos assets |
| G5-19 | Métricas, falhas, decisões humanas e contribuição da IA estão registradas | journal + baseline + retrospectiva | Parcial forte: sincronizado até o início do Dia 6; retrospectiva final 5.9 pendente |
| G5-20 | CI pública e regressões do Gate 4 permanecem verdes | execução GitHub Actions | Atendido no checkpoint 5.8: commit `9739c1e` aprovado nos sete jobs da CI `29597109452` |

## Casos de aceite obrigatórios

| Caso | Resultado mínimo esperado |
|---|---|
| caminho feliz demo | `ACCEPTED`, artifact e report reproduzíveis |
| caminho feliz live | integração real documentada, dentro do budget e sem secret persistido |
| teste com sintaxe/collection error | `TEST_ERROR`, correção limitada ou exaustão explícita |
| teste incoerente com SUT correto | `TEST_ERROR` confirmado pelo oracle |
| SUT com defeito semeado | `SUT_DEFECT_SUSPECTED`, sem correção do SUT |
| requisito ambíguo/contraditório | espera humana ou inconclusão, sem geração forçada |
| Docker indisponível | `INFRASTRUCTURE_ERROR` e orientação diagnóstica |
| operação proibida | `POLICY_VIOLATION`, sem execução do artifact |
| budget esgotado | parada terminal, sem chamada ou correção extra |
| provider/output inválido | retry tipado dentro do limite ou falha explícita |

## Evidências informativas

- duração por nó, incremento e etapa;
- chamadas, tokens, custo e latência live;
- overhead Docker, coverage e mutation;
- estabilidade das repetições demo;
- correções tentadas e padrões de falha;
- diferenças entre estimativa e tempo real;
- retrabalho e decisões em que o julgamento de QA redirecionou a IA.

## Não exigido para aprovação

- TypeScript ou Java end-to-end;
- MCP real ou interface gráfica;
- execução de repositórios arbitrários;
- benchmark com significância estatística;
- correção automática do SUT;
- concorrência distribuída ou uso de produção;
- score universal mínimo de coverage ou mutation para projetos externos.

## Regra de decisão

Todos os critérios G5 são obrigatórios. Uma exceção só pode ser aceita se estiver documentada como risco residual e não invalidar segurança, independência do oracle, limites de correção, instalação limpa ou neutralidade do core. CI verde comprova evidências, mas não aprova o gate. A decisão de Lucas deve ser explícita e registrada em pacote de evidências próprio.

A aprovação do Gate 5 autorizará apenas o planejamento detalhado da Etapa 6; não inicia automaticamente a implementação multilíngue.
