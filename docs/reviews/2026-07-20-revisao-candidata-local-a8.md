# Revisão da candidata local `0.1.0a8`

**Fatia:** 7.1 — baseline e candidata do Developer Preview

**Parecer final da 7.1:** `REMOTE_CI_APPROVED`

**Limite:** nenhum push, CI remota, tag, release, kit ou participante autorizado.

## Decisão de versão

`v0.1.0a7` não representa as mudanças materiais da Etapa 6. O delta inicial possui
25 commits e 205 arquivos alterados, incluindo os novos comandos e assets API, Web
UI e Java. A metadata de desenvolvimento foi corretamente avançada para `0.1.0a8`,
enquanto a7 permanece a última publicação.

## Findings da preparação

| ID | Severidade | Finding | Estado/decisão |
|---|---|---|---|
| `A8-PRE-F001` | LOW | o primeiro harness API passou um path com espaços sem quoting ao `Start-Process`; a fixture não iniciou | `FIXED` no harness; o ASEF classificou corretamente `INFRASTRUCTURE_ERROR`; nova run após readiness explícita passou |
| `A8-PRE-F002` | MEDIUM | o job `docker-security` não construía a imagem Java nem habilitava suas integrações | `FIXED`; workflow local agora inclui imagem e `ASEF_RUN_JAVA_DOCKER_TESTS=1` |
| `A8-PRE-F003` | LOW | tutoriais API/Web ainda descreviam estados anteriores ao Gate 6 | `FIXED`; ambos refletem capabilities parciais em perfis experimentais |

Nenhum finding crítico ou alto foi observado. O caso F001 não exigiu alteração do
produto e preserva uma prova negativa útil do comportamento fail-closed.

## Artifacts locais auditados

| Artifact | Tamanho | SHA-256 |
|---|---:|---|
| `asef_agentic_test_factory-0.1.0a8-py3-none-any.whl` | 237.533 bytes | `658f4da0b9acd9678d465ee26c7377db7e83e3c9743b467520d3f850c0121d89` |
| `asef_agentic_test_factory-0.1.0a8.tar.gz` | 695.664 bytes | `148143f8cf8273dcbfc5bc39b86709562adc72da1e15c3dd01a4a52856e5780d` |

Estes artifacts foram reconstruídos do commit funcional
`b830c3856ffde3b6cb623bcbed21753663f357f8` e passaram no secret scan. O wheel contém contratos e fixtures
empacotadas de API, Web UI e Java; o sdist contém tooling, exemplos, datasets e
planejamento. Os hashes continuam locais e não representam assets publicados.

## Validação técnica

- 497 testes aprovados, 41 skips condicionais e coverage global 85%;
- integração Docker: 28 executados, 25 aprovados e três skips conhecidos do host;
- Smoke 20/20 e Security 12/12;
- documentação 172 arquivos/131 links antes destes documentos de fechamento;
- wheel final reinstalado sem dependências em venv/diretório fora do checkout;
- metadata `0.1.0a8`, doctor `DEGRADED/READY`, demo `SUCCEEDED/ACCEPTED`, auditor
  público 9/9 e cleanup `DRY_RUN_COMPLETE`;
- API, Web UI e Java instalados terminaram `SUCCEEDED/ACCEPTED`;
- source, distributions e evidências instaladas sem assinaturas de secret;
- zero containers gerenciados residuais.

## Parecer

A 7.1 atende ao recorte técnico local e remoto. O commit funcional foi enviado à
`main` e a CI pública
[`29772323987`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29772323987)
aprovou sete de sete jobs, incluindo Java no `docker-security`. O próximo checkpoint
não é automático: tag/pré-release, início da 7.2, distribuição ou recrutamento
continuam sem autorização implícita.
