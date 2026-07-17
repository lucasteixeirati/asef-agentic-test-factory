# Relato — incremento 5.8.6 revisão e candidata

- **Data:** 2026-07-17
- **Estado:** candidata local pronta para checkpoint humano
- **Dependência:** 5.8.5 concluída e 5.8.6 aprovada por Lucas

Lucas autorizou a fatia final do 5.8 sem autorizar automaticamente publicação ou Gate 5. A metadata foi promovida para `0.1.0a6`; os fallbacks do CLI e do report builder foram reconciliados e protegidos por teste.

O walkthrough frio instalou o wheel sem dependências em diretório vazio e percorreu requisitos, doctor, demo, report, checklist factual, cleanup e rotas de contribuição/segurança. Doctor terminou `DEGRADED/READY`, demo `SUCCEEDED/ACCEPTED`, evidência pública ficou `VERIFIED` e cleanup foi dry-run sem deleção. O auditor executou o JSON Schema Draft 2020-12 real após instalar o validator apenas como ferramenta de qualidade.

Smoke permaneceu 20/20 e Security 12/12. A matriz Docker/quality aprovou 17 de 20 integrações; os três skips são as duas provas Linux e o symlink Windows sem privilégio. As provas Linux foram executadas separadamente e passaram 2/2. A regressão aprovou 345 testes com 33 skips e coverage de 85,34%.

O parecer recomenda avançar ao checkpoint de commit/push/CI somente após revisão de Lucas. Tag, artifacts de release, pré-release, conclusão do 5.8, 5.9 e Gate 5 continuam sem autorização.
