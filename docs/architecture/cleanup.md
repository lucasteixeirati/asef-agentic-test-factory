# Retention e cleanup

`asef cleanup` transforma retenção em manutenção observável, sem ampliar a autoridade do usuário para paths arbitrários.

## Planejamento

O comando recebe kind e `older-than-days >= 1`. A raiz é sempre `.asef`. Sem `--apply`, todos os targets elegíveis permanecem `PLANNED`; nenhuma mutação ocorre.

Selectors conhecidos:

- runs: `state.json` com `run_id` e `created_at`;
- Smoke/Security: ID temporal e `suite.json` conciliados;
- doctor: ID temporal e `report.json` conciliados;
- quality: subárvore de run com idade herdada;
- logs: maior timestamp JSONL válido;
- containers: label ASEF, Created e ID completo.

Metadata inválida, target legado, link, junction, arquivo inesperado, escape ou inspeção falha não recebe inferência destrutiva.

## Identidade e apply

Arquivos e árvores possuem SHA-256 de identidade com metadata e conteúdo. Árvores rejeitam links, junctions, mudança de filesystem e mais de 50.000 entradas. Antes de apply, safety e identity são recalculadas.

Diretórios só usam `shutil.rmtree` quando a caracterização informa suporte recursivo resistente a links. No Windows atual isso é recusado. Arquivos usam `unlink` após revalidação. Containers são reinspecionados e removidos por ID exato; `docker system prune` nunca é chamado.

## Tombstone

Cada execução grava JSON e Markdown em `.asef/maintenance/cleanup`, incluindo policy/version, plan hash, counters, targets, reasons e bytes estimados. Tombstones não são selecionados pelo próprio cleanup. Falha parcial retorna exit `7`; dry-run ou apply completo retorna `0`.

ASEF não promete secure erase, recuperação, backup ou que bytes estimados correspondam a espaço físico liberado.

As diferenças entre apply Windows e a prova Linux controlada são mantidas na fonte canônica [`../project/support-and-limitations.md`](../project/support-and-limitations.md). O procedimento público está no [quickstart](../getting-started/quickstart.md) e no [troubleshooting](../guides/troubleshooting.md).
