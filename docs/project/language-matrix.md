# Matriz de linguagens e capabilities

Esta matriz descreve implementação, não intenção de roadmap. Definições públicas de nível e ambientes estão em [`support-and-limitations.md`](support-and-limitations.md).

## Estado atual

| Perfil | Ecossistema | Nível atual | Alvo declarado | Evidência |
|---|---|---|---|---|
| `python-pytest` | Python 3.13 / pytest | experimental | reference | WF-001, Smoke, adapter pytest, coverage/mutation delimitados |
| `node-typescript` | Node 22 | planned | supported | somente inicialização histórica de imagem por digest |
| `java-junit` | Java 21 | planned | experimental | somente inicialização histórica de imagem por digest |
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
| `backend-api` | planned | — | sem adapter/conformance |
| `performance` | planned | — | sem adapter/conformance |

As imagens `python-pytest` e `python-quality` são pinadas/reproduzíveis, mas precisam de build local até existir decisão de distribuição por registry.

## Perfis planejados

Node declara `unit`, `web-ui`, `backend-api`, `coverage`, `mutation` e `performance` como planned. Java declara `unit`, `backend-api`, `coverage`, `mutation`, `performance` e `mobile` como planned. Nenhuma delas possui adapter ou contrato de resultado ativo no Alpha.

Ferramentas como Vitest/Jest, Maven/Gradle, JaCoCo, PIT ou Stryker continuam escolhas futuras; não são dependências suportadas por esta matriz.

## Critério para promoção

Uma promoção exige contrato neutro, adapter encapsulado, imagem/toolchain pinados, detecção, staging, execução, normalização, failure paths, isolamento, conformance, tutorial e limitações públicas. A evidência precisa cobrir o recorte anunciado em host/CI definido.

O procedimento de proposta está no [`../contributing/adapter-guide.md`](../contributing/adapter-guide.md). A arquitetura não aceita condicionais de ecossistema espalhadas pelo core.
