# Inventário da candidata local `0.1.0a8`

**Fatia:** 7.1 — baseline e candidata do Developer Preview

**Estado:** `READY_FOR_COMMIT_CHECKPOINT`; sem commit de candidata, push, tag ou
release.

## Identidade anterior

- última publicação: `v0.1.0a7`;
- commit da tag: `79fbeb0dbbef39799801b86cebd59f8b55edaa0a`;
- wheel publicado: SHA-256 `f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad`;
- sdist publicado: SHA-256 `d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af`;
- escopo público: Alpha Python e correção documental do Gate 5.

## Motivo do incremento de versão

Entre `v0.1.0a7` e o início da 7.1 existem 25 commits e 205 arquivos alterados, com
12.301 inserções e 253 remoções. O package passou a expor mudanças materiais e não
pode continuar usando a identidade publicada `0.1.0a7`.

## Superfície material acrescentada

| Área | Mudança desde a7 | Estado declarado |
|---|---|---|
| backend API | plano natural gravado/live opt-in, OpenAPI fechado, run revisável e execução loopback | partial no perfil Python experimental |
| Web UI | plano gravado/live opt-in, compilação TypeScript, Chromium isolado, conformance e evidência | partial no perfil Node experimental |
| Java/JUnit | plano gravado/live opt-in, compilador determinístico, Maven offline, Surefire e conformance | partial no perfil Java experimental |
| unit TypeScript | intenção aritmética comum, compilação e Node test/TAP | partial somente no recorte de conformance |
| quality | aplicabilidade explícita, relações metamórficas e datasets separados | coverage/mutation continuam disponíveis somente no recorte Python |
| perfis | Node e Java promovidos de planned para experimental no Gate 6 | somente capabilities comprovadas |
| experiência | novos comandos `api*`, `web*` e `java*`, tutoriais, fixtures e assets empacotados | local, fictícia e sem alvo externo |

## Comandos públicos observados na candidata

`api`, `api-generate`, `cancel`, `cleanup`, `doctor`, `generate`, `java`,
`java-generate`, `prepare`, `resume`, `run`, `security`, `smoke`, `wait`, `web` e
`web-generate`.

## Decisão de identidade

- última release permanece `v0.1.0a7`;
- versão em desenvolvimento passa a `0.1.0a8`;
- estado canônico: `CANDIDATE_LOCAL`;
- nome esperado dos artifacts locais:
  `asef_agentic_test_factory-0.1.0a8-py3-none-any.whl` e
  `asef_agentic_test_factory-0.1.0a8.tar.gz`;
- tag `v0.1.0a8`, pré-release e links remotos não existem e não devem ser alegados.

## Critérios técnicos da 7.1

- metadata, fallbacks, release state e três documentos canônicos reconciliados;
- wheel e sdist construídos da mesma árvore;
- contents e assets Stage 6 presentes nos dois formatos aplicáveis;
- wheel instalado sem dependências fora do checkout;
- `doctor`, demo, auditor público, API, Web UI e Java exercitados no recorte instalado;
- regressão, coverage, Docker, Smoke, Security, docs e scans aprovados;
- nenhum container gerenciado residual;
- revisão local registra hashes, tamanhos, resultados e limitações.

Cumprir estes critérios prepara um checkpoint de commit. Não autoriza push, CI
remota, tag, release, distribuição do kit ou contato com participante.

## Snapshot de auditoria local

- metadata instalada: `0.1.0a8`;
- wheel: 237.533 bytes, SHA-256
  `658f4da0b9acd9678d465ee26c7377db7e83e3c9743b467520d3f850c0121d89`;
- sdist: 693.503 bytes, SHA-256
  `5b15770e967aa0f32b31ad317a8454ad48ed302a69d34321496eb6b48c2e4d4e`;
- regressão: 497 testes, 41 skips condicionais, coverage global 85%;
- Docker: 28 testes, 25 aprovados e três skips condicionais do host Windows;
- Smoke `smoke-20260720T165200Z-2c188d81`: 20/20;
- Security `security-20260720T165221Z-188624dc`: 12/12;
- instalado: doctor `DEGRADED/READY`, demo `SUCCEEDED/ACCEPTED`, auditor 9/9 e
  cleanup `SUCCEEDED/DRY_RUN_COMPLETE`;
- runs instaladas finais: API `b5fcd12c-081e-4005-8ea0-d6b9abb0270c`, Web UI
  `f5aa5a01-919a-4487-9abd-e754af781919` e Java
  `9b3de07f-970e-44fc-92f8-3816303c4644`, todas `SUCCEEDED/ACCEPTED`;
- scans de source, artifacts e evidência instalada sem findings;
- zero containers ASEF gerenciados residuais.

Os hashes identificam a árvore de trabalho auditada antes dos documentos de
fechamento. Eles não são artifacts imutáveis nem hashes de release. Após autorização
de commit, a candidata deve ser reconstruída do commit exato e revalidada antes de
qualquer proposta de push/CI.
