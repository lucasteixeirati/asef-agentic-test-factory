# Relato — incremento 5.8.4 arquitetura e contribuição

- **Data:** 2026-07-17
- **Estado:** concluída e aprovada localmente
- **Dependência:** 5.8.3 concluída e 5.8.4 aprovada por Lucas

Lucas autorizou exclusivamente a fatia 5.8.4. A implementação foi auditada pelas fronteiras de aplicação, adapters, perfis, persistência, reports e CI existente antes da consolidação documental.

Foram criados a arquitetura real do Alpha Python, a fonte canônica de suporte/limitações, o guia de adapters e o código de conduta. Evidence model, avaliação, segurança, matriz de linguagens, observabilidade, doctor, cleanup, live provider, README, SECURITY e contribuição foram reconciliados. O walking skeleton foi mantido como histórico e passou a apontar para a arquitetura vigente. Templates existentes não foram recriados.

A revisão confirmou `python-pytest` como experimental, Node/Java como planned e a prova Linux da CI como recorte delimitado, sem anunciá-la como host público geral. Smoke 20/20 e Security 12/12 são baselines específicas, não certificação.

Todos os links locais em 115 arquivos Markdown resolveram. A regressão aprovou 337 testes, com 33 skips opcionais e coverage de 85,34%; secret scan documental e `git diff --check` passaram. Nenhum Docker/live, commit, push, CI, package/version ou release foi iniciado. A 5.8.5 continua dependente de autorização explícita.
