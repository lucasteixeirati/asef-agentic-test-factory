# Gate 5 — Plano de aceite do Alpha Python

- **Estado:** execução em andamento; evidências locais sincronizadas até o incremento 5.5; CI pública do 5.5 pendente
- **Responsável pela decisão final:** Lucas
- **Ambiente de referência:** Windows, Docker Desktop com backend WSL2 e Python 3.13 suportado pelo package

## Critérios obrigatórios

| ID | Critério | Evidência esperada | Estado |
|---|---|---|---|
| G5-01 | Wheel instala e executa fora do checkout | sessão limpa + CI de package audit | Atendido em `v0.1.0a3`: instalação limpa local e CI `29415101383` |
| G5-02 | Demo completa funciona sem chave e sem rede de provider | Smoke Dataset + secret ausente | Atendido localmente no 5.5: 20/20 keyless e secret scan verde; CI pública pendente |
| G5-03 | WF-001 live usa a mesma porta, policies e budgets do demo | contract tests + live smoke manual | Atendido no 5.4: contratos falsos + smoke real autorizado |
| G5-04 | Perfil Python executa `pytest` somente em Docker | manifest + integração | Atendido localmente: fluxo combinado público executa pytest/oracle no Docker; CI do novo job pendente |
| G5-05 | Análise, riscos, cenários, testes e resultados são rastreáveis | report + schema/contract tests | Parcial forte: refs, artifacts e provider calls tipados; consolidação do report fica no 5.8 |
| G5-06 | Oracle curado não entra no prompt e é independente do teste gerado | payload test + hashes + fixtures | Atendido no 5.3: integração Docker, workspaces e evidências independentes |
| G5-07 | `TEST_ERROR` permite no máximo duas correções somente no teste | casos de correção e exaustão | Atendido: SMK-006 prova uma correção após erro de coleta e regressões mantêm o limite |
| G5-08 | `SUT_DEFECT_SUSPECTED` exige evidência independente e revisão humana | SUT defeituoso + oracle + checkpoint | Atendido localmente e exposto no SMK-007 público, sem correção do SUT |
| G5-09 | Policy, budget, infraestrutura e resultado funcional são distintos | matriz de outcomes/exit codes | Atendido: contratos, exits públicos e SMK-008/009/010 preservam as distinções |
| G5-10 | `SMK-001` a `SMK-010` são executáveis e reproduzíveis em demo | relatório agregado 10/10 | Atendido localmente: 20/20 em duas repetições e fingerprints estáveis; CI pendente |
| G5-11 | `SEC-001` a `SEC-012` passam no ambiente de referência | job Docker/security 12/12 | Parcial: baseline Docker verde; catálogo formal 5.7 pendente |
| G5-12 | Coverage Python é normalizada com escopo e limitações | fixture de conformance + report | Parcial — contrato neutro no 5.1; adapter 5.6 pendente |
| G5-13 | Mutation Python é normalizada e limitada por budget | fixture conhecida + timeout test | Parcial — contrato e pilot do core existem; adapter 5.6 pendente |
| G5-14 | Reports JSON e Markdown separam fatos, inferências e recomendações | schema + revisão de conteúdo | Parcial: reports atuais existem; consolidação 5.8 pendente |
| G5-15 | Logs/evidências são correlacionados, limitados e sem secrets | test logs + secret scan | Parcial forte: reports agregados, limites e scans do source/wheel/evidências aprovados; retenção 5.7 pendente |
| G5-16 | `asef doctor` diagnostica requisitos sem expor credenciais | CLI end-to-end | Não iniciado |
| G5-17 | Core não importa Python tooling, Docker, OpenAI ou LangGraph | import boundaries + job core mínimo | Atendido até `v0.1.0a3`: fronteiras AST e job core aprovados |
| G5-18 | README, quickstart, tutorial, arquitetura, segurança e limitações refletem o Alpha real | auditoria documental | Parcial: README/arquitetura live atualizados; consolidação 5.8 pendente |
| G5-19 | Métricas, falhas, decisões humanas e contribuição da IA estão registradas | journal + baseline + retrospectiva | Parcial forte: sincronizado até o início do Dia 6; retrospectiva final 5.9 pendente |
| G5-20 | CI pública e regressões do Gate 4 permanecem verdes | execução GitHub Actions | Atendido até `v0.1.0a3`; novo job `alpha-smoke` do 5.5 aguarda execução pública |

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
