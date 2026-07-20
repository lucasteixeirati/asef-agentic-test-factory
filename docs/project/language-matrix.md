# Matriz de linguagens e capabilities

Esta matriz descreve implementação, não intenção de roadmap. Definições públicas de nível e ambientes estão em [`support-and-limitations.md`](support-and-limitations.md).

## Estado atual

| Perfil | Ecossistema | Nível atual | Alvo declarado | Evidência |
|---|---|---|---|---|
| `python-pytest` | Python 3.13 / pytest | experimental | reference | WF-001, Smoke, adapter pytest, coverage/mutation delimitados |
| `node-typescript` | Node 24.16 | planned (partial candidate) | supported | `web-ui` local completo, conformance 18/18 e fixture empacotada; promoção pendente |
| `java-junit` | Java 21.0.11 / Maven 3.9.16 | planned (experimental candidate) | experimental | `unit` local completo, Surefire, conformance repetida e fixture empacotada; promoção pendente |
| Go | Go | planned | não declarado no código | nenhuma capability executável |
| .NET | .NET | planned | não declarado no código | nenhuma capability executável |

Alvo futuro não promove o nível atual. “Imagem inicia” não significa que projeto, dependências, build, testes ou resultados sejam suportados.

## Declaração do perfil Python

| Capability | Status | Adapter/contrato | Limite |
|---|---|---|---|
| `unit` | partial | `pytest-docker-junit` / `NormalizedExecutionResult` | adapter existe, mas o CLI público ainda tem recorte fixo e experimental |
| `project-detection` | partial | `quality-context` | markers e scopes delimitados; sem detecção geral de projetos externos |
| `coverage` | available | `python-quality-docker` / `CoverageResult` | validada na fixture de referência e budgets definidos |
| `mutation` | available | `python-quality-docker` / `MutationResult` | validada na fixture de referência e budgets definidos |
| `backend-api` | partial | `loopback-http-api` / `ApiExecutionResult` | geração cassette/live opt-in, OpenAPI JSON, run/budgets/evidências e conformance; execução ainda host/loopback, sem alvo externo |
| `performance` | planned | — | sem adapter/conformance |

As imagens `python-pytest` e `python-quality` são pinadas/reproduzíveis, mas precisam de build local até existir decisão de distribuição por registry.

## Perfis planejados

Node declara suas capabilities como planned; `web-ui` é candidata a `partial`, mas o perfil não muda antes da revisão final. Java mantém o perfil planned, porém `unit` possui candidata a `partial`: contrato/política, detector Maven fechado, compilador determinístico, imagem offline, revisão por run, Surefire normalizado, conformance repetida e experiência instalada. As demais capabilities Java continuam planned.

Vitest/Jest, Gradle, JaCoCo, PIT e Stryker continuam escolhas futuras. Maven/JUnit existem somente no recorte fixo Calculator descrito acima.

## Critério para promoção

Uma promoção exige contrato neutro, adapter encapsulado, imagem/toolchain pinados, detecção, staging, execução, normalização, failure paths, isolamento, conformance, tutorial e limitações públicas. A evidência precisa cobrir o recorte anunciado em host/CI definido.

O procedimento de proposta está no [`../contributing/adapter-guide.md`](../contributing/adapter-guide.md). A arquitetura não aceita condicionais de ecossistema espalhadas pelo core.
