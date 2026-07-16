# Revisão técnica — fatia 5.7.2

- **Data:** 2026-07-16
- **Estado:** aprovada localmente
- **Escopo:** dataset, loader, executores internos, runner, reports e CLI

## Findings corrigidos

1. A criação de junction usava argv PowerShell incorreto. A primeira suite terminou 11/12 com SEC-004 `UNSUPPORTED`, como esperado. O executor passou a usar comando interno fixo e o caso foi comprovado isoladamente e na suite.
2. O runner de aplicação importava a observation a partir do adapter. O tipo foi movido para contratos neutros e uma regressão AST preserva a fronteira.
3. Manifest limitations e arquivos de texto precisavam de validação UTF-8/conteúdo explícita.
4. SEC-004 retornava `target_preserved` sem exigir o valor. O executor agora falha se o target não existir.
5. Faltava prova de continuidade após control failure. Um teste confirma que SEC-012 ainda executa após falha de SEC-004.

## Evidências

- Security Suite real: 12/12;
- dataset SHA-256: `e386538869acc970a86d935b7068c794e5522b884caf327a953b3b4434b1818b`;
- 287 testes descobertos, 258 aprovados e 29 skips opcionais;
- branch coverage geral: 85,78%;
- nenhum container `asef-*` residual;
- source e reports passaram no secret scan;
- `git diff --check` aprovado.

## Parecer

A 5.7.2 atende seu escopo e está aprovada localmente. O report publica a limitação de que labels, cleanup após interrupção e orphan detection pertencem à 5.7.3. Nenhuma CI ou release foi criada.
