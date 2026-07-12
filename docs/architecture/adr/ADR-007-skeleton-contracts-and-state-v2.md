# ADR-007 — Package de contratos do skeleton e estado v2

- **Status:** proposta para checkpoint do incremento 4.1
- **Data:** 2026-07-12
- **Responsável pela decisão:** Lucas

## Contexto

Os spikes vivem em `asef_spike` e misturam baseline executável com adapters experimentais. Expandir indefinidamente esse package transformaria resultados descartáveis em arquitetura pública. Além disso, o estado `1.x` dos spikes não possui QualityContext, skill, scopes e referências exigidas pela Etapa 4.

## Decisão proposta

- criar `src/asef` como fronteira pública do walking skeleton;
- renomear a distribuição para `asef-agentic-test-factory 0.1.0a1`;
- manter contratos e outcomes sem dependências de frameworks;
- usar estado schema `2.0.0` e workflow `0.1.0-skeleton`;
- rejeitar retomada de estado `1.x` com erro explícito;
- iniciar nova run em vez de fabricar uma migração incompleta;
- manter `asef_spike` durante a Etapa 4 como baseline de regressão;
- remover ou arquivar o package de spike somente após equivalência demonstrada.

## Consequências positivas

- arquitetura pública não nasce acoplada a LangGraph/OpenAI/Docker;
- contratos podem ser testados antes dos adapters;
- incompatibilidade é explícita e segura;
- baseline histórica continua executável.

## Consequências negativas

- dois packages coexistem temporariamente;
- o comando legado ainda se chama `asef-spike` até a CLI do skeleton ser implementada;
- não é possível retomar runs locais criadas pelo spike;
- CLI pública ainda precisa ser extraída em incremento posterior;
- haverá trabalho deliberado de migração de funcionalidades, não apenas renomeação.

## Evidências

- 19 testes de contrato aprovados;
- regressão local aprovada;
- `docs/architecture/contracts/walking-skeleton-schemas.md`;
- plano da Etapa 4 e ADR-001/004/005/006.

## Revisitar quando

- o walking skeleton atingir Gate 4;
- existir estado v2 persistido que exija migração real;
- `asef_spike` deixar de oferecer evidência comparativa útil.
