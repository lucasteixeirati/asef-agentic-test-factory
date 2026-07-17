# Relato — incremento 5.8.2 publicação do Alpha report

- **Data:** 2026-07-16
- **Estado:** concluída e aprovada localmente
- **Dependência:** 5.8.1 aprovada

Lucas autorizou exclusivamente a segunda fatia do incremento 5.8. O report ad hoc foi substituído por uma projeção determinística de `AlphaRunReport 1.0.0`, mantendo o JSON como representação normativa e o Markdown como view pura do contrato validado.

A implementação separou builder, verificador de evidências, renderer e store. Evidence refs são confinadas à run e classificadas como `VERIFIED`, `MISSING` ou `MISMATCH`; link/junction nunca é seguido. JSON, Markdown e manifest são preparados antes da substituição e restaurados ao estado anterior se a transação falhar. Reemissão verifica os hashes existentes e bloqueia tamper.

O manifest agora referencia os dois reports por SHA-256. A CLI preserva `report_path` e adiciona `report_json`, `report_markdown` e `report_schema_version`. Terminais persistidos de sucesso, falha funcional, erro de infraestrutura, policy, budget, cancel e resume produzem report; espera humana permanece não terminal.

A regressão final local executou 337 testes, com 33 skips opcionais e branch coverage de 85,34%. Seis testes específicos cobriram idempotência, hash ausente/divergente, tamper, escape Markdown, rollback e terminal sem artifact. Nenhum commit, push, CI, versão ou release foi criado. A jornada documental continua reservada à 5.8.3.
