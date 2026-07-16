# Relato — Incremento 5.7.6 CI e candidata

- **Data:** 2026-07-16
- **Estado:** concluído e publicado como `v0.1.0a5`

Lucas autorizou a última fatia do 5.7. Foi criado o job `alpha-security`, mantendo os cinco jobs anteriores independentes. O job é keyless, não executa provider e publica apenas reports sanitizados.

A prova Linux foi executada antes da CI em container pinado e isolado. Apply recursivo removeu a fixture autorizada; symlink foi rejeitado e o target externo permaneceu intacto.

O wheel instalado sem dependências fora do checkout aprovou doctor, demo keyless, cleanup dry-run/apply e scanner. A matriz Docker/quality continuou verde. A versão foi promovida para `0.1.0a5`, pois `v0.1.0a4` já representa o 5.6 publicado.

A regressão final ficou em 318 testes, 285 passes e 33 skips opcionais, com branch coverage de 85,16%. O checkpoint funcional `2de3c44` foi publicado e a CI `29528937211` aprovou os seis jobs. O `alpha-security` confirmou Security 12/12, doctor, prova Linux de symlink/cleanup, ausência de órfãos e scanner verde. A candidata está tecnicamente aprovada; não houve aprovação automática de release ou Gate 5.

Lucas aprovou explicitamente a publicação. A tag anotada aponta para `4c8073c`; wheel e sdist foram reconstruídos nesse estado, passaram no scanner e foram publicados na pré-release `v0.1.0a5`. Os digests remotos conciliam com os locais: wheel `6b4d191705a9ddf4a513b3e33f4df021bae477e4a77b5149e713a42b055e937c` e sdist `783c1c8a2beb6285f3cbef5a127a8c59cd778e3ae23c682c795e6a0bb76080fc`. O Gate 5 permanece aberto para 5.8/5.9.
