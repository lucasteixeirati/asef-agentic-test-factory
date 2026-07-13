# Gate 5 — Plano de aceite do Alpha Python

- **Estado:** baseline de aceite aprovada por Lucas em 2026-07-13; execução não iniciada
- **Responsável pela decisão final:** Lucas
- **Ambiente de referência:** Windows, Docker Desktop com backend WSL2 e Python 3.13 suportado pelo package

## Critérios obrigatórios

| ID | Critério | Evidência esperada | Estado |
|---|---|---|---|
| G5-01 | Wheel instala e executa fora do checkout | sessão limpa + CI de package audit | Não iniciado |
| G5-02 | Demo completa funciona sem chave e sem rede de provider | Smoke Dataset + secret ausente | Não iniciado |
| G5-03 | WF-001 live usa a mesma porta, policies e budgets do demo | contract tests + live smoke manual | Não iniciado |
| G5-04 | Perfil Python executa `pytest` somente em Docker | manifest + integração | Não iniciado |
| G5-05 | Análise, riscos, cenários, testes e resultados são rastreáveis | report + schema/contract tests | Parcial — casos e refs tipados no 5.1 |
| G5-06 | Oracle curado não entra no prompt e é independente do teste gerado | payload test + hashes + fixtures | Parcial — schema, fixtures e hashes no 5.1; integração futura |
| G5-07 | `TEST_ERROR` permite no máximo duas correções somente no teste | casos de correção e exaustão | Não iniciado |
| G5-08 | `SUT_DEFECT_SUSPECTED` exige evidência independente e revisão humana | SUT defeituoso + oracle + checkpoint | Não iniciado |
| G5-09 | Policy, budget, infraestrutura e resultado funcional são distintos | matriz de outcomes/exit codes | Não iniciado |
| G5-10 | `SMK-001` a `SMK-010` são executáveis e reproduzíveis em demo | relatório agregado 10/10 | Não iniciado |
| G5-11 | `SEC-001` a `SEC-012` passam no ambiente de referência | job Docker/security 12/12 | Não iniciado |
| G5-12 | Coverage Python é normalizada com escopo e limitações | fixture de conformance + report | Parcial — contrato neutro no 5.1; adapter futuro |
| G5-13 | Mutation Python é normalizada e limitada por budget | fixture conhecida + timeout test | Parcial — contrato e budget no 5.1; adapter futuro |
| G5-14 | Reports JSON e Markdown separam fatos, inferências e recomendações | schema + revisão de conteúdo | Não iniciado |
| G5-15 | Logs/evidências são correlacionados, limitados e sem secrets | test logs + secret scan | Não iniciado |
| G5-16 | `asef doctor` diagnostica requisitos sem expor credenciais | CLI end-to-end | Não iniciado |
| G5-17 | Core não importa Python tooling, Docker, OpenAI ou LangGraph | import boundaries + job core mínimo | Parcial — fronteira AST e core mínimo aprovados localmente |
| G5-18 | README, quickstart, tutorial, arquitetura, segurança e limitações refletem o Alpha real | auditoria documental | Não iniciado |
| G5-19 | Métricas, falhas, decisões humanas e contribuição da IA estão registradas | journal + baseline + retrospectiva | Parcial — journals e baseline atualizados até 5.1 |
| G5-20 | CI pública e regressões do Gate 4 permanecem verdes | execução GitHub Actions | Parcial — regressões locais verdes; CI do 5.1 pendente |

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
