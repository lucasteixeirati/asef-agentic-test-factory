# Relato — incremento 5.8.6 revisão e candidata

- **Data:** 2026-07-17
- **Estado:** candidata publicada como pré-release `v0.1.0a6`
- **Dependência:** 5.8.5 concluída e 5.8.6 aprovada por Lucas

Lucas autorizou a fatia final do 5.8 sem autorizar automaticamente publicação ou Gate 5. A metadata foi promovida para `0.1.0a6`; os fallbacks do CLI e do report builder foram reconciliados e protegidos por teste.

O walkthrough frio instalou o wheel sem dependências em diretório vazio e percorreu requisitos, doctor, demo, report, checklist factual, cleanup e rotas de contribuição/segurança. Doctor terminou `DEGRADED/READY`, demo `SUCCEEDED/ACCEPTED`, evidência pública ficou `VERIFIED` e cleanup foi dry-run sem deleção. O auditor executou o JSON Schema Draft 2020-12 real após instalar o validator apenas como ferramenta de qualidade.

Smoke permaneceu 20/20 e Security 12/12. A matriz Docker/quality aprovou 17 de 20 integrações; os três skips são as duas provas Linux e o symlink Windows sem privilégio. As provas Linux foram executadas separadamente e passaram 2/2. A regressão aprovou 345 testes com 33 skips e coverage de 85,34%.

Lucas aprovou o checkpoint de commit/push/CI. O commit `9739c1e` foi enviado à `main`, e a execução pública `29597109452` aprovou os sete jobs: `core`, `framework-spikes`, `docker-security`, `alpha-smoke`, `quality-capabilities`, `alpha-security` e `public-experience`. O fechamento documental `ddeeb3a` repetiu os sete jobs com sucesso em `29597666988`.

Após autorização explícita de publicação, a tag anotada e a pré-release `v0.1.0a6` foram publicadas em 2026-07-17. O wheel possui SHA-256 `0b40e6597acb1064c15122a7ac96934e7b1e3f62df64bf5ff1dedcd62831ff72`; o sdist possui SHA-256 `b2963ce50ddcb4bf52080510fdc55656a9ab7cd42ff66ce3008c76fac2f46289`. Os digests remotos conferem com os artifacts locais auditados. O incremento 5.8 está concluído; 5.9, Gate 5 e Etapa 6 continuam sem autorização.
