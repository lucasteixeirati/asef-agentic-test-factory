# Adapter live e budgets

## Fronteira

O modo live implementa `AgenticTestPort` e `TestCorrectionPort` sem alterar a autoridade do runtime. O adapter produz análise e artifacts tipados; application services reservam chamadas, controlam retries, validam budgets e decidem transições.

O transporte usa `POST /v1/responses`, `store: false` e Structured Outputs por `text.format` com JSON Schema estrito. O runtime ainda valida forma, tipos, paths, imports, scenario IDs e invariantes de correção localmente.

Referências oficiais verificadas em 2026-07-14:

- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs);
- [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create).

## Ativação segura

Live exige simultaneamente:

- `--mode live`;
- contexto explícito com provider `openai`;
- autorização para `analysis`, `test-generation` e `test-correction`;
- `live_requires_budget: true`;
- `OPENAI_API_KEY` somente no host;
- modelo explícito;
- teto positivo em BRL;
- tarifas de entrada e saída em BRL por milhão de tokens.

As tarifas são fornecidas pelo operador porque preço e câmbio são externos e variáveis. O valor persistido é identificado como estimativa. Uma chamada é reservada antes do transporte; tokens, latência e custo observado são incorporados depois da resposta. Se o consumo observado ultrapassar o limite, a run termina em `BUDGET_EXHAUSTED` sem descartar o consumo.

## Dados enviados

Somente requisito e arquivos concretos autorizados pelo `read_scope` entram no prompt. O adapter:

- resolve novamente cada path contra a raiz autorizada;
- limita o conjunto a 64 KiB UTF-8;
- bloqueia marcadores sensíveis conhecidos antes da chamada;
- trata requisito, source e diagnóstico como dados não confiáveis;
- não envia oracle, chave, headers, socket Docker ou paths fora do escopo.

## Falhas e retries

- HTTP 408, 409, 429, 5xx, timeout e indisponibilidade: transitórios;
- 4xx não transitório e resposta de erro: permanentes;
- recusa: `PROVIDER_REFUSAL` sem retry automático;
- JSON/shape inválido: output inválido, sujeito ao retry central;
- provider retry não incrementa `test_corrections`.

## Cassette

`--record-live-cassettes` é opt-in. O registro contém schema/prompt version, hash do prompt, output sanitizado, identidade do provider e métricas. Não contém prompt integral, headers ou credencial. Cassettes live não devem ser publicados sem nova revisão humana.

## Smoke manual

O teste `ManualOpenAILiveSmokeTests` fica desabilitado por padrão. Sua execução requer `ASEF_RUN_LIVE_TESTS=1`, chave, modelo, budget e tarifas explícitos. Ele nunca integra o gate obrigatório de PR.

O percurso operacional está no [`../tutorials/wf-001-live.md`](../tutorials/wf-001-live.md). Estado experimental, ambientes e garantias não oferecidas permanecem canônicos em [`../project/support-and-limitations.md`](../project/support-and-limitations.md).
