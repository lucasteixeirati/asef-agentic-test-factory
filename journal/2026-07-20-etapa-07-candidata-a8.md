# 20/07/2026 — candidata local a8 do Developer Preview

Lucas aprovou o planejamento da Etapa 7 e autorizou avançar na fatia 7.1 local. O
delta desde `v0.1.0a7` demonstrou mudança material, levando à identidade de
desenvolvimento `0.1.0a8`, sem alterar a última release publicada.

Wheel e sdist foram construídos; o wheel final foi reinstalado fora do checkout e
executou doctor, demo, cleanup, API, Web UI e Java. Regressão, cobertura, integrações
Docker, Smoke, Security, docs e scanners passaram. A primeira tentativa da API
falhou por quoting incorreto do path do servidor no harness de auditoria; o produto
registrou `INFRASTRUCTURE_ERROR`. Após corrigir o harness e esperar readiness, a run
passou sem mudança de produto.

A CI preparada para uma futura execução remota passou a incluir explicitamente a
imagem e as integrações Java. A candidata permanece local e mutável, pronta somente
para decisão de commit. Nenhum push, tag, release, provider live, alvo externo ou
participante foi autorizado ou usado.

Após autorização separada, o commit funcional
`b830c3856ffde3b6cb623bcbed21753663f357f8` foi enviado à `main`. A CI pública
`29772323987` aprovou os sete jobs; `docker-security` comprovou também a integração
Java recém-habilitada. A candidata passou a `REMOTE_CI_APPROVED`, ainda sem tag,
pré-release, postflight ou autorização para a 7.2.
