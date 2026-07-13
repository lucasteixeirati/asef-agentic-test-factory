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

O perfil `python-pytest` é `experimental` com alvo `reference`. Unit é parcial porque o walking skeleton executa um runner limitado; coverage e mutation são `planned` até 5.6. Node e Java continuam planejados apesar do container smoke aprovado na Etapa 3.

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

As categorias precisam reconciliar com o total e o resultado não pode exceder o budget declarado.

## Neutralidade do core

Os contratos usam somente biblioteca padrão e `EvidenceRef`. Um teste baseado em AST verifica que os módulos de contratos, outcomes, linguagens e avaliação não importam `pytest`, coverage, mutmut, Docker, OpenAI, LangGraph ou PydanticAI.

Strings de identificação de ferramenta são dados; não constituem import ou autoridade arquitetural.

## Evolução 5.2 — execução pytest

`TestExecutionOutcome` e `NormalizedExecutionResult 1.1.0` acrescentam taxonomia factual, ferramenta/versão, errors, skipped e raw result. O adapter específico usa JUnit XML; o core recebe somente esses fatos neutros. Assertion failure permanece sem atribuição de causa até o oracle do 5.3.
