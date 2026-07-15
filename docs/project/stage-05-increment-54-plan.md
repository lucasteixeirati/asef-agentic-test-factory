# Incremento 5.4 — Adapter live e budgets

- **Data:** 2026-07-14
- **Estado:** concluído localmente; candidata `0.1.0a3` em fechamento
- **Dependência:** incremento 5.3 concluído e publicado como `v0.1.0a2`

## Objetivo

Disponibilizar o provider live por uma implementação pública de `AgenticTestPort` e `TestCorrectionPort`, preservando os mesmos contratos, validações, budgets e decisões determinísticas usados no modo demo.

## Decisões de implementação

- usar a Responses API por transporte HTTP direto e substituível;
- solicitar Structured Outputs com `text.format`, JSON Schema e `strict: true`;
- manter validação local mesmo quando o provider declarar aderência ao schema;
- não fornecer tools ao modelo nem permitir que ele controle transições ou retries;
- ler a chave apenas de `OPENAI_API_KEY` no processo host;
- nunca enviar a chave, o socket Docker ou configuração do provider ao container;
- exigir `--mode live`, contexto compatível e budget monetário positivo;
- persistir a reserva da chamada antes do transporte;
- registrar provider, modelo retornado, response ID, tokens, latência e custo estimado;
- tratar recusa, rate limit/indisponibilidade, erro permanente e output inválido separadamente;
- manter provider retry independente do budget de correção;
- gravar cassette somente por opção explícita, sem prompt integral, headers ou secrets.

## Fatias executáveis

1. contratos de resultado e configuração live;
2. transporte OpenAI normalizado e testável;
3. adapter de análise, geração e correção com schemas e prompts versionados;
4. integração de budgets e métricas no application service;
5. seleção explícita do adapter na CLI;
6. cassette sanitizado e contract tests com transporte falso;
7. smoke live manual, barato e nunca obrigatório em PR;
8. regressão demo, secret scan, coverage e documentação.

## Critérios de aceite

- análise, geração e correção passam pelos mesmos contratos públicos no modo demo e live;
- uma chamada não ocorre quando call/token/cost budget já estiver esgotado;
- consumo observado é preservado mesmo quando ultrapassa o limite e encerra a run;
- falha transitória pode consumir somente o retry autorizado;
- falha permanente e recusa não são repetidas automaticamente;
- cassettes não contêm chave, Authorization, prompt integral ou marcadores sensíveis conhecidos;
- testes de contrato não dependem de rede ou credencial;
- o smoke live exige acionamento manual, chave e teto explícito;
- `asef run` em demo permanece keyless e offline;
- os containers de teste permanecem sem rede e sem credenciais.

## Critérios de parada

Interromper o incremento se um secret for persistido, se o provider assumir autoridade de workflow, se uma chamada puder ocorrer sem budget positivo, se retries escaparem ao contador central ou se a demo passar a depender de rede/chave.

## Referência oficial verificada

Em 2026-07-14 foram verificados o guia oficial de Structured Outputs e a especificação vigente de `POST /v1/responses`. A forma adotada é `text.format` com `type: json_schema`, schema estrito, extração de `output_text`, uso retornado pela resposta e tratamento explícito de recusas.

## Evidência de aceite

Em 2026-07-14, uma única chamada manual e explicitamente autorizada validou o caminho real de análise com `gpt-5.4-2026-03-05`. Foram observados 194 tokens de entrada, 138 de saída, latência de 4.515 ms e custo estimado de R$ 0,01533, abaixo do teto de R$ 0,10. O teste passou sem retry; a suíte automática e as verificações offline permanecem independentes de rede e credencial.
