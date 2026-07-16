# Revisão técnica — fatia 5.7.5

- **Data:** 2026-07-16
- **Estado:** aprovada localmente com apply recursivo Windows bloqueado
- **Escopo:** retention, cleanup, debug, scanner e cleanups silenciosos

## Findings corrigidos

1. Resolver `.asef` antes da inspeção ocultava a possibilidade de a própria raiz ser link/junction. A raiz lexical agora é validada antes de qualquer resolução operacional.
2. `docker ps -aq` podia retornar ID curto, incompatível com `.Id` completo. Orphan cleanup passou a usar `--no-trunc` e ID exato.
3. Tree identity não rejeitava mudança de `st_dev`; uma árvore poderia atravessar filesystem. O fingerprint agora falha antes de descer.
4. `all` podia planejar simultaneamente uma run e sua subárvore quality. O overlap foi eliminado.
5. Refs de targets não eram escapadas no Markdown. Tombstones agora neutralizam pipe, backtick e HTML.
6. O scanner autodetectava qualquer arquivo como tar e a heurística de assignment gerava falsos positivos em código. Archives passaram a depender da extensão declarada e assignments são analisados apenas em formatos de dados/log.
7. O scanner anterior não abria sdist tar.gz e ignorava silenciosamente symlink, oversize e archive inválido. Esses casos agora são verificáveis e bloqueantes.

## Evidências

- dry-run real `cleanup-20260716T181517Z-1796bf2b`: 1 planned, 13 skipped, 0 deleted/failed;
- apply de arquivo, container e diretório suportado exercitados somente em fixtures temporárias;
- mudança entre plan/apply: falha fechada;
- root/target linkado: target externo preservado;
- `ignore_errors=True` ausente em `src`;
- Security real: 12/12;
- Smoke real: 20/20;
- 316 testes descobertos, 285 aprovados e 31 skips opcionais;
- branch coverage geral: 85,16%;
- wheel e sdist contêm cleanup e passaram no scanner endurecido;
- nenhum container gerenciado residual;
- `git diff --check` e compilação aprovados.

## Parecer

A 5.7.5 atende seu escopo local e está aprovada. Diretórios não são removidos por apply no Windows atual; isso preserva o fail-closed previsto pela caracterização. A prova real Linux, o job `alpha-security`, package isolado final e a decisão da candidata pertencem à 5.7.6. Nenhum commit, push, CI ou release foi criado.
