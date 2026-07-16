# Revisão técnica — fatia 5.7.4

- **Data:** 2026-07-16
- **Estado:** aprovada localmente
- **Escopo:** checks tipados, CLI, executor falso, integração real e report sanitizado

## Findings corrigidos

1. Contexto explícito inválido estava inicialmente modelado como warning opcional. O check passou a ser obrigatório quando `--context` é informado e agora bloqueia sem refletir path ou erro bruto.
2. Selecionar campos de `docker info` não bastava para impedir conteúdo hostil dentro dos valores. Server version, OSType e architecture passaram a exigir formatos fechados antes da persistência.
3. O report do Security Dataset ainda publicava uma limitação temporal dizendo que hardening pertencia à 5.7.3. O texto foi reconciliado com o lifecycle já implementado.

## Evidências

- executor falso cobre requisito ausente, daemon inválido, erro interno, contexto inválido, chave live e containers residuais;
- checkout via `PYTHONPATH=src`: bloqueado apenas por distribuição não instalada;
- wheel instalado sem dependências fora do checkout: 10 `PASS`, 2 `SKIP`, `DEGRADED/READY`, exit `0`;
- Security Suite real: 12/12;
- Smoke Dataset real: 20/20;
- 300 testes descobertos, 271 aprovados e 29 skips opcionais;
- branch coverage geral: 85,54%;
- source, wheel, sdist e report instalado aprovados no secret scan;
- compilação e `git diff --check` aprovados.

## Parecer

A 5.7.4 atende seu escopo e está aprovada localmente. O doctor não possui autoridade corretiva e não persiste raw subprocess output ou credenciais. Retention/cleanup/debug, tombstones, scanner expandido e remoção de cleanups silenciosos permanecem exclusivamente na 5.7.5. Nenhum commit, push, CI pública ou release foi criado.
