# Contratos de segurança, diagnóstico e manutenção — 5.7.1

- **Estado:** implementados na fatia 5.7.1
- **Schema:** `1.0.0`
- **Código:** `src/asef/security_contracts.py`

## Fronteira

Os contratos usam somente biblioteca padrão e contratos ASEF. Eles não importam Docker, OpenAI, LangGraph, pytest ou tooling Python. Esta fatia não executa containers, não diagnostica o host por CLI e não remove arquivos.

## Security Dataset

`SecurityCaseSpec` contém somente identidade, controle, executor enum, referências relativas de fixtures, precondições, outcome e limitações. A matriz é fechada por ID:

- `SEC-001` a `SEC-012` possuem executor e outcome específicos;
- manifest não fornece shell, argv, imagem, mount ou path absoluto;
- campos desconhecidos, traversal, executor desconhecido ou combinação divergente falham fechados.

`SecurityCaseResult` separa `PASSED`, `FAILED`, `ERROR` e `UNSUPPORTED`. Cada status possui classificação única. Pass exige evidência; os demais exigem diagnóstico estável e sanitizado. O fingerprint é recalculado a partir de identidade, status, classificação, facts e diagnostic code; duração, timestamp e paths de evidência não participam.

`SecuritySuiteReport` exige exatamente doze resultados ordenados. O aceite derivado requer 12 `PASSED`, zero failure, zero error e zero unsupported.

## Doctor

`DoctorCheck` possui ID pertencente à matriz inicial, categoria, obrigatoriedade, status, código, resumo, duração, timeout, facts allowlisted por check e recomendação opcional. Recomendações pertencem a uma enumeração revisada; texto de erro externo nunca se transforma em comando.

`DoctorReport` registra versões do ASEF/Python, perfil e ambiente. O status agregado é `HEALTHY`, `DEGRADED` ou `BLOCKED`: qualquer `FAIL` bloqueia; `WARN` ou `SKIP` degradam; somente passes resultam em healthy pleno. A 5.7.4 implementou os checks operacionais, executor substituível, reports atômicos e a CLI pública.

## Cleanup operacional

A 5.7.5 implementou `asef cleanup`, executor substituível e tombstones JSON/Markdown. `CleanupReport` registra `asef-local-retention@1.0.0`; o plan hash concilia kind, idade, root fixa, target refs, identities e bytes estimados.

Targets são selecionados somente nas raízes conhecidas. Idade vem de `state.json`, ID temporal conciliado com suite/report, timestamp JSONL ou metadata Docker por label. Target malformed ou legado sem timestamp é `SKIPPED`, nunca inferido por `mtime`.

Apply revalida containment, link/junction, filesystem, tree/file identity e plan imediatamente antes da mutação. Diretórios exigem perfil com remoção recursiva segura; arquivos usam `unlink` após fingerprint; containers usam label e ID completo. Tombstones não pertencem ao mesmo ciclo que documentam.

## Retenção

`RetentionPolicy` exige uma regra para cada classe conhecida:

| Classe | Regra inicial |
|---|---|
| efêmero | remoção imediata |
| evidência final | cleanup explícito |
| log operacional | 1 MiB e dois backups |
| cassette live | cleanup explícito e não publicável automaticamente |
| report de CI | sete dias, sanitizado |
| debug | explícito e sanitizado |
| tombstone | preservado por cleanup explícito |

A policy rejeita alegação de secure erase e cleanup automático de evidência final.

## Cleanup

`CleanupRequest` usa raiz fixa `.asef`, selector enum, idade mínima de um dia e modo `DRY_RUN` por padrão. `CleanupReport` reconcilia `PLANNED`, `DELETED`, `FAILED` e `SKIPPED`; dry-run não pode alegar deleção. O hash do plano é recalculado sobre request, paths relativos, identidades e estimativas, sem confiar em um digest fornecido pelo caller.

Esses contratos não autorizam remoção. Executor, revalidação TOCTOU e persistência de tombstone pertencem à 5.7.5.

## Filesystem

`characterize_filesystem_safety()` registra primitives disponíveis sem mutação. `inspect_filesystem_target()` classifica root, target externo, ausência, arquivo, symlink, junction ou diretório candidato.

Apply recursivo só pode ser anunciado quando:

- `shutil.rmtree.avoids_symlink_attacks` é verdadeiro;
- remoção relativa por `dir_fd` é suportada;
- `stat(..., follow_symlinks=False)` é suportado;
- no Windows, junctions podem ser detectadas.

Mesmo quando essas primitives existem, containment, identidade, manifest e revalidação continuam obrigatórios.
