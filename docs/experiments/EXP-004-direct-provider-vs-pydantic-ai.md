# EXP-004 — Chamada direta ao provider versus PydanticAI

- **Data:** 2026-07-12
- **Status:** comparação offline concluída; validação live opcional pendente
- **Baseline:** gateway HTTP direto existente
- **Framework avaliado:** PydanticAI 2.9.0

## Pergunta

PydanticAI reduz a complexidade do adaptador de provider e fortalece structured output sem assumir o controle do workflow ou criar uma segunda engine de execução?

## Hipótese

PydanticAI deverá reduzir código manual de schema e parsing. O benefício só será arquiteturalmente aceitável se o runtime ASEF continuar responsável por transições, budgets e evidências.

## Método

- mesmo contrato `ModelGateway` usado pelo runtime;
- mesmo schema lógico do `wf001_analysis`;
- mesmo `BudgetController` compartilhado;
- `TestModel` para impedir custo, latência e variabilidade de rede;
- requisições reais bloqueadas por `ALLOW_MODEL_REQUESTS=False`;
- saída válida, tipo inválido, campo extra e schema desconhecido;
- execução do workflow existente até `SUCCEEDED`;
- PydanticAI mantido fora da máquina de estados.

O uso de `TestModel` segue a orientação oficial do PydanticAI para testes sem chamadas reais ao LLM.

## Resultados

| Critério | HTTP direto | PydanticAI |
|---|---|---|
| Structured output | JSON Schema manual + `json.loads` + validação local | `BaseModel` tipado |
| Linhas não vazias do adaptador | 67 | 32 |
| Linhas do modelo tipado | Não aplicável | 6 |
| Budget ASEF | Explícito | Explícito e preservado |
| Controle do workflow | Runtime ASEF | Runtime ASEF |
| Saída com tipo inválido | Rejeitada pela validação local | Rejeitada pelo PydanticAI e convertida em `GatewayError` |
| Campo extra | Rejeitado pela validação local | Rejeitado por `extra="forbid"` |
| Teste offline próprio | Cassette | `TestModel` |
| Testes do spike | Baseline já coberta | 5/5 aprovados |

## Peso de dependências

A instalação do metapacote `pydantic-ai==2.9.0` elevou o `.venv` compartilhado dos spikes de 35 para 120 pacotes. Foram instaladas integrações não necessárias ao recorte, incluindo Anthropic, Google, MCP, Logfire, OpenTelemetry e CLI.

Esse resultado não representa o mínimo possível. A recomendação técnica inicial era usar `pydantic-ai-slim[openai]`. O responsável decidiu manter `pydantic-ai==2.9.0` no ambiente experimental para permitir futuros providers, evals, MCPs e observabilidade. As integrações permanecem desabilitadas por padrão e sujeitas ao `QualityContext` e às políticas do runtime.

## Falhas e fricções

1. A primeira implementação tratou `result.usage` como método; na versão 2.9.0 ele é uma propriedade.
2. A primeira integração tentou construir outro controller no runner; foi corrigida para compartilhar a mesma instância de budget do gateway.
3. O teste em Python 3.13 emitiu `DeprecationWarning` de `pydantic_graph` por obter event loop quando ainda não existe loop corrente.
4. O framework converte validação estruturada em menos código local, mas ainda exige tradução de suas exceções para erros do domínio ASEF.

## Limitações

- PydanticAI ainda não foi executado contra a OpenAI neste experimento;
- a baseline HTTP possui uma chamada live anterior, então a comparação de provider não é perfeitamente simétrica;
- a contagem de pacotes foi feita em ambiente compartilhado após LangGraph e representa o ambiente experimental escolhido, não dependências obrigatórias de toda execução;
- não foram comparados retry, backoff ou streaming;
- linhas de código não medem sozinhas manutenibilidade ou estabilidade.

## Conclusão provisória

PydanticAI demonstrou benefício concreto como adaptador tipado de provider: reduziu parsing e validação manuais e executou o workflow existente sem assumir suas transições. Não demonstrou motivo para controlar o loop principal, persistência ou human-in-the-loop, responsabilidades que permanecem no runtime e no experimento LangGraph.

O metapacote completo permanece disponível no ambiente experimental por decisão do responsável, mas não integra automaticamente o caminho principal do walking skeleton. A adoção do adapter em uma skill ou provider deverá ser autorizada pelo contexto e acompanhada de evidência específica, incluindo chamada live quando aplicável.
