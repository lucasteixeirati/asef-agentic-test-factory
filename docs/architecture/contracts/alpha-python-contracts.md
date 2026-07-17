# Contratos do Alpha Python — baseline 5.1

- **Estado:** implementados; ADR-009 aceita
- **Data:** 2026-07-13
- **Código:** `src/asef/evaluation_contracts.py` e `src/asef/languages.py`

## Perfil de linguagem

`LanguageProfile` agora separa:

- nível atual de suporte;
- nível-alvo;
- markers de projeto;
- capabilities e estado individual;
- adapter e contrato de resultado, quando existirem;
- limitações publicadas.

O perfil `python-pytest` é `experimental` com alvo `reference`. Unit é parcial porque o walking skeleton executa um runner limitado. Coverage e mutation estão disponíveis no adapter `python-quality-docker` para o perfil de referência limitado, com imagem local pinada, escopo explícito e budgets obrigatórios. Node e Java continuam planejados apesar do container smoke aprovado na Etapa 3.

## `DatasetCase`

Campos obrigatórios:

- schema, ID, versão e tipo;
- título, objetivo, origem, licença e curador;
- perfil, SUT e requisito;
- inputs permitidos para geração;
- inputs exclusivos de avaliação e oracle;
- classificações esperadas, modos, exposição pública/protegida, política do oracle e tags.

Invariantes principais:

- `SMK-NNN` pertence a Smoke e `SEC-NNN` a Security;
- referências são POSIX relativas ao repositório e sem traversal;
- geração e avaliação são conjuntos disjuntos;
- exposição do dataset e isolamento do oracle são dimensões distintas;
- oracle nunca aparece nos inputs de geração;
- oracle declarado precisa constar nos inputs de avaliação.

Foi adotado `case.json`, não `case.yaml`, para manter o core sem dependência de parser YAML. Um formato externo poderá ser convertido na borda posteriormente.

## `CoverageResult`

- ferramenta e versão;
- escopo e exclusões;
- linhas e branches cobertos/totais separadamente;
- duração, limitações e referência ao resultado bruto;
- percentuais derivados; denominador zero resulta em `null`, nunca em 100% inventado.

## `MutationResult`

- ferramenta, versão e escopo;
- total, mortos, sobreviventes, inválidos, timeout e não executados;
- duração e budgets de mutantes/tempo;
- referência ao resultado bruto e limitações;
- score calculado apenas sobre mortos + sobreviventes.

As categorias precisam reconciliar com o total. Desde a fatia 5.6.1, `mutants_total` representa todos os mutantes descobertos, inclusive os não admitidos; `killed + survived + invalid + timed_out` representa os processados e não pode exceder `max_mutants`. O restante é `not_run`. Essa correção permite aplicar admission control sem esconder o universo descoberto.

## Evolução 5.6.1 — requests, observations e admission control

`QualityCapabilityRequest` declara capability, ferramenta/versão, escopo, testes, ambiente e budgets sem importar tooling. Mutation exige `max_mutants`; coverage o rejeita.

`QualityCapabilityObservation` distingue `COMPLETED`, `PARTIAL`, `UNAVAILABLE`, `FAILED` e `BUDGET_EXHAUSTED`. Estado incompleto exige diagnóstico; `UNAVAILABLE`/`FAILED` não podem carregar métricas fabricadas. `QualityEvaluationReport` agrega no máximo uma observation por capability e só é completo quando todas terminam `COMPLETED`.

`admit_mutants` ordena nomes descobertos de forma canônica e separa admitidos/deferidos antes da execução. A caracterização específica do mutmut `3.6.0` está em `docs/quality/mutmut-3.6.0-characterization.md`.

## Neutralidade do core

Os contratos usam somente biblioteca padrão e `EvidenceRef`. Um teste baseado em AST verifica que os módulos de contratos, outcomes, linguagens e avaliação não importam `pytest`, coverage, mutmut, Docker, OpenAI, LangGraph ou PydanticAI.

Strings de identificação de ferramenta são dados; não constituem import ou autoridade arquitetural.

## Evolução 5.8.1 — `AlphaRunReport 1.0.0`

A fatia 5.8.1 congelou o contrato neutro do report público em `src/asef/report_contracts.py` e o JSON Schema Draft 2020-12 em `src/asef/schemas/alpha-run-report.schema.json`. Desde a 5.8.2, esse contrato substitui o report ad hoc do `JsonRunStore`.

O report possui seções normativas para requirement, traceability, artifacts, attempts, resultado funcional, quality, intervenções humanas, policy/budgets, usage, evidence, facts, inferences, recommendations e limitations. JSON será normativo; o futuro Markdown será uma view do mesmo contrato.

Invariantes principais:

- `report_id` reconcilia com `run_id`;
- status, classification, terminal e acceptance funcional são coerentes;
- `BEH-NNN`, `RSK-NNN` e `SCN-NNN` são contíguos;
- scenario→artifact→execution usa apenas links tipados e IDs existentes;
- risco→cenário não é inferido quando a relação não foi observada;
- inference exige facts e evidence conhecidas;
- recommendation pertence a enum fechada e exige inference/limitation conhecida;
- evidence publicável precisa ser sanitizada e `VERIFIED`;
- evidence ausente/divergente exige limitation bloqueante;
- paths são canônicos, relativos e contidos;
- strings públicas rejeitam assinaturas sensíveis e possuem limite;
- contrato, parser e schema rejeitam campos extras e versões desconhecidas;
- o módulo não importa provider, Docker, pytest, coverage, mutation ou workflow engine.

O threat model específico está em `docs/architecture/report-publication-threat-model.md`.

## Evolução 5.8.2 — composição e publicação

As autoridades estão separadas:

- `application/build_alpha_report.py` compõe somente a partir de state, snapshot, avaliação e observações tipadas;
- `adapters/report_evidence.py` verifica containment, tipo de arquivo e SHA-256 sem seguir link/junction;
- `adapters/alpha_report_markdown.py` renderiza exclusivamente um contrato validado;
- `adapters/alpha_report_store.py` valida o JSON persistido e transaciona JSON, Markdown e manifest;
- `JsonRunStore.save_report()` delega a publicação e permanece responsável pelo state/event stream.

O JSON é normativo. Markdown não lê state, manifest, filesystem ou provider e não pode criar facts, inferences ou recommendations. Reemissão com mesma entrada é byte a byte idêntica; tamper prévio no report bloqueia reemissão. Falhas de integridade entram como `MISSING`/`MISMATCH` e `EVIDENCE_INTEGRITY_FAILURE`, sem alterar o terminal funcional original.

O manifest registra paths e hashes de `report.json` e `report.md`. A CLI mantém `report_path` para compatibilidade e acrescenta `report_json`, `report_markdown` e `report_schema_version`.

## Evolução 5.2 — execução pytest

`TestExecutionOutcome` e `NormalizedExecutionResult 1.1.0` acrescentam taxonomia factual, ferramenta/versão, errors, skipped e raw result. O adapter específico usa JUnit XML; o core recebe somente esses fatos neutros. Assertion failure permanece sem atribuição de causa até o oracle do 5.3.
