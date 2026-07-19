# Etapa 6.4.4 — linguagem natural e capability run gravada

**Data:** 2026-07-19

Após a 6.4.3, o caminho determinístico da 6.4.4 foi implementado sem chamada live.
`web-generate` cria `WF-WEB-001` antes do gateway, converte a intenção fictícia por
cassette em plano tipado, injeta IDs e origem, registra tokens e deixa a run
aguardando revisão. `web --run-id` revalida o SHA-256 antes de compilar ou executar.

A jornada pública local foi exercitada: geração terminou em
`WAITING_FOR_HUMAN_REVIEW` e a retomada explícita executou Chromium no container,
terminando `SUCCEEDED/ACCEPTED`. Testes adicionais cobrem criação anterior ao
gateway, budget de modelo/tokens/cenários, adulteração do plano e distinção entre
falha funcional, política e infraestrutura.

Depois da prova cassette, a integração live opt-in foi adicionada sem chamada real.
Ela usa schema estrito com todos os campos requeridos, null para opcionais e
`additionalProperties=false` em cada objeto; exige modelo, budget e tarifas
positivas, e contabiliza tokens, custo e retry. Um gateway falso comprovou duas
tentativas, um retry e custo estimado de R$ 0,18 dentro do budget fictício. A
capability continua `planned` até conformance 6.4.5.

O schema seguiu a documentação oficial vigente de
[strict mode](https://developers.openai.com/api/docs/guides/function-calling#strict-mode),
consultada em 2026-07-19. Nenhuma chave foi lida e nenhuma requisição ao provider
foi executada.

## Evidência local

- 444 testes aprovados e 36 integrações condicionais ignoradas;
- branch coverage global de 85% e 91% no recorte store/agent/serviço Web UI;
- jornada pública cassette → revisão → Docker aprovada;
- docs checker com 157 arquivos e 126 links, sem findings;
- secret scan, `git diff --check` e ausência de containers gerenciados aprovados.
