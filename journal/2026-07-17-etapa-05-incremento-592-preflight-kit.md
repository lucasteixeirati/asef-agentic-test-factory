# Relato — incremento 5.9.2 preflight e kit

- **Data:** 2026-07-17
- **Estado:** concluído como `BLOCKED/NOT_READY`
- **Autorização:** Lucas aprovou a 5.9.1 e autorizou somente a 5.9.2

Os dois assets foram baixados novamente da release `v0.1.0a6`. Wheel e sdist conferiram com os hashes congelados. O source archive continha Dockerfile/tooling e documentação, permitindo executar todo o ensaio sem checkout.

Em venv e diretório temporários, o wheel instalou com `--no-deps` e reportou `0.1.0a6`. A imagem `asef/python-pytest:8.3.3` foi construída do sdist. Com `OPENAI_API_KEY` ausente, doctor retornou `DEGRADED/READY` com 12 checks; a demo terminou `SUCCEEDED/ACCEPTED`; cleanup retornou `DRY_RUN_COMPLETE`. O auditor instalado passou 9/9, o scanner não encontrou assinaturas e nenhum container ASEF gerenciado permaneceu.

O preflight não foi liberado. README, quickstart e suporte dentro do sdist/tag declaram `v0.1.0a5` como última release e `0.1.0a6` como candidata ainda não publicada. O finding `PREFLIGHT-F-001` foi classificado `HIGH/OPEN` porque contamina as tarefas EXT-01 e EXT-02 antes de qualquer avaliação externa. As correções locais posteriores à tag não tornam o artifact imutável coerente.

Kit e checklist foram produzidos em `HOLD`. Nenhum participante foi contatado. A próxima decisão é autorizar ou rejeitar uma candidata corretiva; a 5.9.3 não pode começar no estado atual.

Regressão final: 356 testes aprovados, 33 skips opcionais, branch coverage de 85%, Gate checker 10/10, documentação 126 arquivos/107 links sem findings, secret scan e `diff-check` verdes.
