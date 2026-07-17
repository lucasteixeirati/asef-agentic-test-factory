# Revisão — candidata corretiva local `0.1.0a7`

- **Data:** 2026-07-17
- **Escopo autorizado:** preparar e auditar a candidata; sem commit, push, tag, pré-release ou 5.9.3
- **Parecer:** `READY_FOR_PUBLICATION_CHECKPOINT`
- **Gate 5:** permanece bloqueado

## Correção

O projeto passou a separar formalmente a última release publicada da versão em desenvolvimento em `docs/project/release-state.json`. `pyproject.toml`, CLI e report builder foram promovidos para `0.1.0a7`; README, quickstart e suporte agora declaram simultaneamente `v0.1.0a6` como última publicação e `0.1.0a7` como candidata local não publicada.

O docs checker deixou de inferir publicação pela metadata do package. Ele valida o estado canônico, reconcilia a versão em desenvolvimento com o package, reconcilia tag e versão publicada e rejeita claims históricas divergentes. Seis testes documentais cobrem o repositório e os casos adversariais.

## Artefatos e ensaio isolado

O build local produziu:

- wheel, 167628 bytes, SHA-256 `f4751c710e051e35f16d11d360fd4280d2ad7de20280e660bfc2c0ace6ff55c0`;
- sdist, 532330 bytes, SHA-256 `502775bbe4de7b10331d9b59d69d195edfb91dcb6e6903d894835d639aa8f603`.

O sdist contém os três documentos canônicos, `release-state.json` e o checker. Fora do checkout, a auditoria documental percorreu 126 arquivos e 107 links sem finding; o wheel instalou com `--no-deps` e expôs metadata `0.1.0a7`; a imagem pytest foi reconstruída do sdist.

Doctor terminou `DEGRADED/READY` com 12 checks. A demo keyless terminou `SUCCEEDED/ACCEPTED`; o auditor passou 9/9; cleanup retornou `DRY_RUN_COMPLETE`; scanner passou e nenhum container gerenciado permaneceu. A regressão aprovou 357 testes, manteve 33 skips opcionais e branch coverage de 85%. Gate checker 10/10, inventário 20 critérios/40 evidências, docs checker, secret scan e `git diff --check` ficaram verdes.

## Limite do parecer

Os hashes acima identificam artefatos locais de uma worktree, não uma release imutável. Portanto `PREFLIGHT-F-001` permanece `HIGH/OPEN`, o kit continua `HOLD` e a 5.9.3 não pode começar. O próximo checkpoint possível é humano e separado: autorizar ou rejeitar commit/push/CI e, depois de seus resultados, decidir sobre tag/pré-release. Somente assets remotos publicados e baixados novamente podem encerrar o finding.
