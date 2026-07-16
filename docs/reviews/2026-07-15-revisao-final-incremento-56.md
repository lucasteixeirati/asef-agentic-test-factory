# Revisão final local — incremento 5.6

- **Data:** 2026-07-15
- **Candidata:** `0.1.0a4`
- **Escopo:** coverage e mutation do SUT Python, evidências, reports e CI dedicada
- **Estado:** aprovada localmente e na CI `29461154744`; tag e release pendentes

## Parecer

O incremento 5.6 atende localmente aos critérios técnicos do plano. Coverage e mutation são executados por adapter Docker separado, com imagem e ferramentas pinadas, fonte original read-only, rede bloqueada, outputs nativos preservados, normalização tipada e budgets de tempo/quantidade. As métricas enriquecem apenas runs funcionalmente aceitas e não alteram sua classificação.

G5-12 e G5-13 estão atendidos. O novo job público `quality-capabilities` e os quatro jobs anteriores foram aprovados na run `29461154744`.

## Findings fechados

1. A serialização aninhada removia percentuais derivados de coverage; corrigida e coberta por contrato.
2. O store misturava base relativa e paths absolutos no Windows; referências agora usam paths canônicos resolvidos.
3. Uma falha de normalização escapava do adapter e descartava o output nativo; agora gera observation `FAILED` mantendo evidência.
4. Stdout/stderr e diagnósticos do tooling precisavam de sanitização explícita; valores sensíveis são suprimidos antes da persistência.
5. O report final não era reemitido depois de `facts["quality"]`; o serviço agora atualiza JSON/Markdown quando a avaliação funcional está presente.
6. O job `docker-security` descobriria testes que dependem da imagem nova; a suíte quality ganhou opt-in próprio e permanece isolada no job dedicado.

## Evidências locais

- core: 253 testes descobertos, 226 executados e 27 integrações opcionais ignoradas;
- branch coverage: 86%, acima do mínimo de 85%;
- Docker: 18 testes descobertos, 17 aprovados e um skip conhecido de symlink no Windows;
- quality Docker: 3/3 aprovados com opt-in dedicado;
- Smoke Dataset: 20/20, hash `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`;
- fixture: coverage 7/8 linhas e 1/2 branches; mutation 5 descobertos, 3 admitidos, 1 morto, 2 sobreviventes e 2 deferidos;
- SUT de referência: coverage 11/11 linhas e 2/2 branches; mutation 9 descobertos, 8 admitidos, 5 mortos, 3 sobreviventes e 1 deferido;
- source, wheel, sdist, Smoke e evidências: secret scan aprovado;
- `git diff --check`: aprovado;
- wheel instalado sem dependências em venv novo e identificado como `0.1.0a4`;
- demo keyless fora do checkout: `SUCCEEDED` / `ACCEPTED`.

## Artifacts da candidata

- `asef_agentic_test_factory-0.1.0a4-py3-none-any.whl`: SHA-256 `ad3bebddb39e712f80c5d0d1105fa5636afb06375702d9ad2b5f16036e8a90c5`;
- `asef_agentic_test_factory-0.1.0a4.tar.gz`: SHA-256 `565aa650a1a693a6d7382ab4c83165382bbe5e4a66a33143e53e9a4cc396229e`.

## Riscos residuais

- metadata do mutmut é interna à versão pinada e exige nova conformance em qualquer upgrade;
- a imagem de quality precisa ser construída localmente enquanto não houver distribuição por registry;
- a baseline demonstra o perfil Python de referência limitado, não um threshold universal nem suporte a repositórios arbitrários.

## Próxima decisão

Publicar o commit documental de fechamento, confirmar sua CI e então criar a tag anotada e a pré-release `v0.1.0a4`.
