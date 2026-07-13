# 4.R8 — Hardening da estratégia de testes

- **Data:** 2026-07-13
- **Estado:** concluído e validado

## Baselines de coverage

Coverage mede linhas e branches e passa a ser gate da CI.

| Perfil | Escopo | Baseline medida | Threshold |
|---|---|---:|---:|
| Core canônico | package sem legado e sem workflow opcional | 89% | 85% |
| Checkpoint opcional | adapter LangGraph + human decision service | 85% | 85% |

O threshold impede regressão; não representa meta final nem prova efetividade sozinho. Módulos excluídos de um perfil são medidos no outro ou permanecem explicitamente legados.

## Ampliação orientada a risco

Foram acrescentados testes para:

- cassette inválido, schema incorreto, shape extra e tipos incompatíveis;
- gateway live com transporte simulado, budget, HTTP error, falha de conexão e output inválido;
- `run_id` malicioso, state ausente/corrompido e JSON não objeto;
- escaping de Markdown;
- persistência JSON atômica;
- stream de eventos corrompido, deduplicação e preservação append-only;
- campos mínimos de correlação em eventos;
- logging JSONL, rotação de handlers e redaction;
- semântica interna de `BudgetExceeded` e combinações incoerentes de outcome.

Nenhum teste live consumiu créditos de API.

Regressão final: 123 testes core descobertos, 104 aprovados e 19 opt-in/skip; 18/18 no job de frameworks/workflow opcional; 11/11 integrações Docker.

## Mutation pilot

O Mutmut 3.6.0 foi executado em Linux sobre `runtime/budgets.py`, `runtime/__init__.py` e `outcomes.py`.

### Primeira execução válida

- mutantes: 13;
- mortos: 8;
- sobreviventes: 5;
- sobreviventes: quatro alterações em `BudgetExceeded.__init__` e uma no happy path de `exit_code_for`.

### Correção

Os testes passaram a verificar budget, used, limit e mensagem do erro, além de combinações `SUCCEEDED/UNCLASSIFIED` e `FAILED/ACCEPTED`.

### Reexecução

- mutantes: 13;
- mortos: 13;
- sobreviventes: 0;
- mutation score do piloto: 100%.

O resultado não deve ser extrapolado para todo o ASEF. O workflow de mutation é manual e semanal porque a ferramenta exige `fork` e o custo não é adequado a cada push neste estágio.

## Lacunas remanescentes

- mutation ainda não cobre contratos, adapters ou application services;
- não há teste multiwriter para o mesmo run store;
- não há fault injection entre state, manifest e events;
- property-based testing continua planejado;
- usuário externo real ainda não executou o quickstart.
