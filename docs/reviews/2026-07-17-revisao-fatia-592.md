# Revisão técnica — fatia 5.9.2

- **Data:** 2026-07-17
- **Estado:** concluída com bloqueio; sessão externa `NOT_READY`
- **Escopo:** assets remotos, instalação fria, doctor/demo/auditor/cleanup, kit e checklist

## Parecer

**Recomendação: não iniciar a 5.9.3. Preparar uma release corretiva imutável antes de envolver participante externo.**

## Evidência técnica aprovada

- wheel remoto: 167.571 bytes, SHA-256 `0b40e6597acb1064c15122a7ac96934e7b1e3f62df64bf5ff1dedcd62831ff72`;
- sdist remoto: 497.111 bytes, SHA-256 `b2963ce50ddcb4bf52080510fdc55656a9ab7cd42ff66ce3008c76fac2f46289`;
- Python 3.13.5; Docker client/server 28.2.2, engine Linux amd64;
- instalação wheel `--no-deps` fora do checkout: `0.1.0a6`;
- imagem pytest construída somente do sdist;
- doctor: `DEGRADED/READY`, 12 checks, exit 0, stderr vazio;
- demo: `SUCCEEDED/ACCEPTED`, schema 1.0.0, exit 0, stderr vazio;
- auditor: 9/9;
- cleanup: `DRY_RUN_COMPLETE`, exit 0, stderr vazio;
- secret scan: aprovado;
- containers gerenciados após execução: zero.

O run efêmero foi `5eaf13f5-57cb-4252-812a-a2275adb1434`. O report JSON possui SHA-256 `530a6129332a8d6f41a637dd96383d3faad2047d9faa4b7e1ff5af44f61d0cb5`; o Markdown, `1c153dedae2ae21fa53013727b808779c954f5bb72b66f6822e7d1809a8479a9`. Paths temporários e material bruto não foram versionados.

## Finding bloqueador

`PREFLIGHT-F-001` — `HIGH/OPEN`: os documentos congelados contradizem a release que os contém.

| Documento | Alegação observada |
|---|---|
| README | `v0.1.0a5` é a última release; `0.1.0a6` não publicada |
| quickstart | `v0.1.0a5` é a última release; `0.1.0a6` candidata |
| suporte/limitações | `0.1.0a5` é a última versão; linha 5.8 candidata |

Isso afeta diretamente EXT-01/EXT-02. Entregar a página correta da release junto de documentos contraditórios exigiria recuperação de ambiguidade conhecida e reduziria a validade da sessão. A correção na árvore local não pode alterar a tag já publicada.

## Kit e governança

- kit do participante criado em `HOLD`, sem rubrica/respostas;
- checklist do facilitador criado em `HOLD`;
- registro mecânico do preflight versiona apenas dados sanitizados;
- checker rejeita `READY` com documentação falha ou findings;
- protocolo foi aprovado, mas permanece suspenso até novo preflight verde.

## Regressão

- suíte core: 356 testes aprovados, 33 skips opcionais;
- branch coverage: 85%, threshold atendido;
- Gate checker: 10/10;
- inventário: 20 critérios e 40 referências, zero findings mecânicos;
- documentação: 126 arquivos, 107 links, zero findings;
- secret scan e `git diff --check`: aprovados.

## Próximo checkpoint

O caminho tecnicamente recomendado é o B do plano: preparar candidata corretiva, repetir build/package audit/preflight e somente então decidir sobre 5.9.3. Isso exige autorização humana separada; nenhuma version bump, tag ou release foi feita nesta fatia.
