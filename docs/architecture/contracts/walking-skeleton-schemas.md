# Contratos concretos do Walking Skeleton — Incremento 4.1

- **Estado:** implementados e cobertos por testes; aguardam checkpoint humano
- **Implementação:** `src/asef/contracts.py` e `src/asef/outcomes.py`
- **Distribuição:** `asef-agentic-test-factory 0.1.0a1`

## Versões

| Contrato | Versão | Regra |
|---|---|---|
| Requests, artifacts, snapshots e results | `1.0.0` | versão exata no skeleton |
| Estado persistido | `2.0.0` | compatibilidade por major 2 |
| Workflow | `0.1.0-skeleton` | identifica o fluxo da Etapa 4 |

Estado `1.x` pertence aos spikes e não pode ser retomado. Ele não possui QualityContext, skill, scopes ou referências exigidas pelo skeleton. A execução deve iniciar uma nova run; nenhuma migração inventa esses campos.

## `SkeletonRunRequest`

- referência do contexto;
- sistema e skill solicitada;
- requisito;
- output root;
- modo demo/live;
- budget monetário explícito.

Invariantes:

- campos textuais obrigatórios;
- requisito limitado a 20 mil caracteres;
- budget não negativo;
- modo live exige budget positivo;
- schema exato `1.0.0`.

## `UnitTestArtifact`

- um arquivo `.py` diretamente em `tests_generated/`;
- path canônico com `/`, relativo e sem `..`;
- conteúdo UTF-8 não vazio, até 20 KiB;
- uma ou mais referências de cenário;
- attempt positivo;
- SHA-256 calculado pelo runtime.

O hash enviado por modelo não faz parte da entrada confiável.

## `ContextSnapshot`

- digest do QualityContext de origem;
- IDs de QA, equipe, sistema, repositório e skill;
- profile e imagem fixada por digest;
- provider, modelo e modo;
- scopes efetivos;
- MCPs efetivamente utilizados.

O snapshot contém referências sanitizadas, não o documento integral. Marcadores de secrets em scopes são rejeitados.

## `EvidenceRef`

- tipo;
- path relativo à run;
- SHA-256;
- schema version.

Paths vazios, absolutos ou com traversal são inválidos.

## `NormalizedExecutionResult`

- imagem por digest;
- comando como lista segura;
- exit code e duração;
- refs de stdout/stderr;
- contagens opcionais de testes;
- timeout e truncamento.

Comandos rejeitam NUL e marcadores de valores sensíveis. Contagens não podem ser negativas ou inconsistentes.

## `SkeletonRunState`

- request imutável por contrato;
- run/workflow/schema IDs;
- status e classificação separados;
- referência ao snapshot;
- evidências;
- attempts;
- budgets e usage;
- errors e history estruturados.

Estado serializa apenas tipos primitivos. Usage não pode exceder os limites persistidos, e budget da request precisa corresponder ao budget da run.

## Status e classificação

Status representa posição/terminal do workflow. Classificação representa significado do resultado. Uma run não deve usar `FAILED` como substituto genérico para input, policy, budget ou infraestrutura.

## Exit codes

| Código | Contrato |
|---:|---|
| 0 | sucesso aceito |
| 2 | input/contexto inválido |
| 3 | espera humana |
| 4 | falha funcional/inconclusiva |
| 5 | policy blocked |
| 6 | budget exhausted |
| 7 | provider/infraestrutura |
| 130 | cancelamento |

## Independência de frameworks

O package `asef` não importa LangGraph, OpenAI, Docker ou PydanticAI. Esses componentes serão adapters. Um teste lê o source dos contratos e protege essa fronteira durante o skeleton.

## Evidência de teste

- 19 testes do incremento 4.1;
- requests e serialização;
- paths, tamanho e hash;
- snapshot e imagem por digest;
- execução e dados sensíveis;
- budgets;
- estado v2 e rejeição do spike v1;
- exit codes;
- ausência de imports de frameworks.
