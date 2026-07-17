# Revisão técnica — fatia 5.8.2

- **Data:** 2026-07-16
- **Estado:** aprovada localmente
- **Escopo:** builder, integridade de evidências, renderer, persistência, manifest, CLI e terminais

## Findings corrigidos

1. `JsonRunStore` acumulava composição, apresentação e persistência. As autoridades foram separadas em application builder e adapters específicos.
2. Terminais ocorridos antes de workspace/execution, como policy e budget, encerravam sem report. Todo terminal posterior à criação persistida da run agora publica o contrato; espera humana continua sem alegar terminal.
3. Evidence refs confiavam apenas no hash declarado. O verifier passou a confinar paths, rejeitar forma não canônica, não seguir links/junctions e recalcular SHA-256.
4. Markdown era montado diretamente a partir de state/evaluation. O renderer agora aceita somente `AlphaRunReport` validado e escapa HTML, pipe, backtick e linhas de input.
5. JSON e Markdown podiam ser atualizados sem prova no manifest. O manifest recebe path/hash dos dois e é reconciliado antes e depois da emissão.
6. Falha entre substituições poderia deixar publicação parcial. JSON, Markdown e manifest passaram a usar transação recuperável com rollback testado.
7. Reemissão poderia encobrir tamper existente. Hash divergente bloqueia a operação como erro, sem “reparar” silenciosamente a trilha.
8. A CLI expunha somente `report_path`. Os campos aditivos normativos foram incluídos sem remover compatibilidade.

## Evidências

- seis testes específicos de publicação aprovados;
- terminais `SUCCEEDED`, falhas funcionais, infraestrutura, `POLICY_BLOCKED` e `BUDGET_EXHAUSTED` exercitados localmente;
- testes de resume/cancel preservados na suíte opcional LangGraph;
- 337 testes aprovados, com 33 skips opcionais;
- branch coverage geral: 85,34%;
- builder com 86,96%, store com 88,03% e renderer com 91,53% na medição local;
- JSON reaberto pelo parser estrito após persistência;
- reemissão idempotente byte a byte;
- mismatch/missing visíveis sem alterar status/classification original;
- `git diff --check`, compilação, package audit e secret scan aprovados; wheel/sdist contêm builder, verifier, renderer, store, contrato e schema.

## Parecer

A 5.8.2 atende seu escopo e está aprovada localmente. O report público substitui a composição ad hoc, possui integridade explícita, Markdown derivado, hashes no manifest e cobertura dos terminais persistidos. A 5.8.3 permanece decisão separada; nenhum commit, push, CI, candidata ou release foi criado.
