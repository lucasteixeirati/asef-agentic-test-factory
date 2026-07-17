# Revisão técnica — fatia 5.8.1

- **Data:** 2026-07-16
- **Estado:** aprovada localmente
- **Escopo:** contrato público, JSON Schema e threat model do Alpha report

## Findings corrigidos

1. A ordem dos budgets no parser dependia de um `set`; o parsing passou a usar ordem explícita e estável.
2. O `oracle_execution_id` aceitava um execution node de outro attempt; a reconciliação agora exige o ID canônico do mesmo attempt.
3. Paths normalizados, drive Windows e backslash ainda podiam produzir referências ambíguas; somente paths relativos POSIX canônicos e contidos são aceitos.
4. Traceability podia declarar artifacts sem execution node/link completo; cenário, artifact, attempt e execution agora reconciliam em cadeia fechada.
5. Acceptance funcional podia coexistir com contagens incompletas; resultado aceito exige todos os testes aprovados e zero failure, error ou skip.
6. Evidence ausente ou divergente não tornava explícita a limitação; `EVIDENCE_INTEGRITY_FAILURE` é obrigatória e publicação exige conteúdo sanitizado e verificado.
7. A cobertura exibida como 85% era 84,97% em precisão de duas casas; casos adversariais de fields aninhados elevaram o total sem reduzir o gate.

## Evidências

- 13 testes específicos do report aprovados;
- 331 testes descobertos e aprovados, com 33 skips de integrações opcionais;
- branch coverage geral: 85,10%; módulo novo: 84,61%;
- JSON Schema Draft 2020-12 estruturalmente válido e compatível com uma instância do contrato;
- wheel e sdist incluem `asef/report_contracts.py` e `asef/schemas/alpha-run-report.schema.json`;
- contrato neutro, sem imports de provider, Docker, framework de testes, coverage ou workflow engine;
- builder, renderer, store, CLI e reports reais permanecem ausentes por desenho nesta fatia.

## Parecer

A 5.8.1 atende seu escopo e está aprovada localmente. O contrato `AlphaRunReport 1.0.0`, sua taxonomia semântica, rastreabilidade, regras de integridade, schema e threat model estão congelados como base da próxima fatia. Nenhum commit, push, CI, candidata ou release foi criado. A 5.8.2 requer aprovação explícita separada.
