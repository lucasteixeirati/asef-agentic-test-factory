# Contratos concretos do Walking Skeleton — Incremento 4.1

- **Estado:** contratos `1.1.0` implementados e validados em 4.R2
- **Implementação:** `src/asef/contracts.py` e `src/asef/outcomes.py`
- **Distribuição:** `asef-agentic-test-factory 0.1.0a1`

## Versões

| Contrato | Versão | Regra |
|---|---|---|
| Requests, artifacts, snapshots e results | `1.0.0` | versão exata no skeleton |
| Resultado de execução estruturado | `1.1.0` | extensão aditiva do 5.2 para tool/outcome/JUnit |
| Estado persistido | `1.1.0` | compatibilidade por major 1; import estrito de `1.0.0` |
| Workflow | `0.1.0-skeleton` | identifica o fluxo da Etapa 4 |

Estado `1.0.0` pertence aos spikes e não pode ser retomado. Ele pode ser importado sem contexto como evidência; uma execução exige replay com nova identidade e snapshot validado.

> A rejeição total de `1.x` fazia parte da ADR-007 rejeitada. O contrato vigente preserva fatos `1.0.0` como contexto não resolvido sem alegar resume.

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

No 5.2, o resultado evoluiu de forma aditiva para incluir ferramenta/versão, outcome neutro, errors, skipped e referência opcional ao resultado bruto. Imagem de execução aceita registry digest ou image ID local imutável. Os campos antigos permanecem válidos para o runner do skeleton.

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

### Nova run, import e replay

- `NEW`: nova identidade, contexto inicialmente não resolvido;
- `IMPORTED`: identidade e evidências `1.0.0` preservadas, sem autorização de execução;
- `REPLAY`: nova identidade vinculada ao import, snapshot obrigatório e execução desde o início;
- `resume_supported: false` é registrado nos eventos de import/replay;
- usage da replay começa zerado; usage e budgets anteriores continuam auditáveis.

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

Os módulos públicos de contratos e domínio não importam LangGraph, OpenAI, Docker ou PydanticAI. Esses componentes permanecem em adapters. Testes de fronteira baseados em source/AST protegem essa separação.

## Evidência de teste

- 19 testes do incremento 4.1;
- requests e serialização;
- paths, tamanho e hash;
- snapshot e imagem por digest;
- execução e dados sensíveis;
- budgets;
- estado 1.1 e importação controlada do spike 1.0;
- exit codes;
- ausência de imports de frameworks.
