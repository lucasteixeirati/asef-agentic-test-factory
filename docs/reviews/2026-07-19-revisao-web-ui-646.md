# Revisão local — Web UI 6.4.6

- **Data:** 2026-07-19
- **Escopo:** documentação, distribuição, experiência instalada e candidata 6.4
- **Decisão:** candidata técnica concluída; promoção documental adiada para a revisão final do Gate 6

## Experiência instalada

O wheel `0.1.0a7` foi construído a partir da árvore local e instalado com `--no-deps`
em virtualenv temporária fora do checkout. A imagem Web UI havia sido construída a
partir da toolchain pública da mesma revisão.

| Observação | Resultado |
|---|---|
| instalação fora do checkout | aprovado |
| geração por cassette sem provider | `WAITING_FOR_HUMAN_REVIEW` / `PLAN_READY_FOR_REVIEW` |
| plano revisado | uma origem loopback e um cenário delimitado |
| execução instalada | `SUCCEEDED` / `ACCEPTED` |
| contadores | 1 teste, 1 aprovado, 0 erros |
| evidências | `web_ui_test_plan`, `web_ui_execution_result` |
| fixture | carregada do wheel, sem dependência de `examples/` |
| rede | provider não usado; browser em Docker `--network none` |

A virtualenv temporária foi removida depois da auditoria. Nenhum container ASEF
residual permaneceu.

## Finding corrigido

O executor buscava os assets em `examples/web-ui`, caminho disponível apenas no
checkout. A experiência instalada falharia apesar dos testes locais verdes. Os
quatro assets passaram a integrar `asef/fixtures/web_ui`; um teste exige igualdade
byte a byte com a fixture pública, e o build confirmou sua presença no wheel.

## Evidências acumuladas da 6.4

- contrato, parser e política fail-closed;
- Playwright/Chromium/Node pinados e executados como não-root;
- artifact TypeScript determinístico reconciliado por hash;
- capability run com checkpoint humano e cassette;
- live opt-in coberto sem chamada real;
- 14 controles de conformance, nove casos Docker repetidos duas vezes;
- experiência instalada completa fora do checkout;
- tutorial, arquitetura, skill, mapa e limitações reconciliados.

Não há finding alto ou crítico aberto. Sites externos, autenticação, múltiplos
browsers, upload, download, visual regression, performance e produção permanecem
fora do escopo. O perfil continua `planned` até a validação humana final da Etapa 6.

## Gate técnico local

- regressão: 451 testes aprovados e 37 skips condicionais;
- branch coverage global: 85%;
- integrações Docker Web UI: 3/3;
- docs checker: 159 arquivos e 127 links, zero finding;
- secret scan e `git diff --check`: aprovados;
- containers residuais: zero após a execução;
- wheel SHA-256: `b107393b1672b344ecfcbb5009d39fd996f6bc8d82dd1cdd5085fb1ae745dbff`;
- sdist SHA-256: `088f7658975dd085af9627273327ab20e3735536ff6bfc9ac87b835dc80b6fe5`.
