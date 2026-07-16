# Relato — Incremento 5.7.6 CI e candidata

- **Data:** 2026-07-16
- **Estado:** implementação e CI pública concluídas; publicação pendente

Lucas autorizou a última fatia do 5.7. Foi criado o job `alpha-security`, mantendo os cinco jobs anteriores independentes. O job é keyless, não executa provider e publica apenas reports sanitizados.

A prova Linux foi executada antes da CI em container pinado e isolado. Apply recursivo removeu a fixture autorizada; symlink foi rejeitado e o target externo permaneceu intacto.

O wheel instalado sem dependências fora do checkout aprovou doctor, demo keyless, cleanup dry-run/apply e scanner. A matriz Docker/quality continuou verde. A versão foi promovida para `0.1.0a5`, pois `v0.1.0a4` já representa o 5.6 publicado.

A regressão final ficou em 318 testes, 285 passes e 33 skips opcionais, com branch coverage de 85,16%. O checkpoint funcional `2de3c44` foi publicado e a CI `29528937211` aprovou os seis jobs. O `alpha-security` confirmou Security 12/12, doctor, prova Linux de symlink/cleanup, ausência de órfãos e scanner verde. A candidata está tecnicamente aprovada; não houve aprovação automática de release ou Gate 5.
