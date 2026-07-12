# EXP-003 — OpenAI Responses API com structured output

- **Data:** 2026-07-12
- **Status:** aprovado para o recorte inicial
- **Modelo:** `gpt-5.4-mini-2026-03-17`
- **Endpoint:** Responses API

## Pergunta

O gateway HTTP direto consegue obter análise estruturada, registrar uso e direcionar uma transição do WF-001 sem expor a chave à sandbox?

## Segurança e custo

- chave lida da variável de usuário do Windows;
- chave nunca persistida nos artefatos;
- container confirmou ausência da variável;
- uma chamada live bem-sucedida;
- budget lógico informado: R$ 10,00;
- limite de saída: 600 tokens.

## Ocorrência de configuração

A primeira tentativa retornou `401 invalid_api_key` porque a variável continha uma aspa literal no início. A propriedade foi diagnosticada sem imprimir a chave, e somente o caractere inválido foi removido. Não houve geração útil nessa tentativa.

## Resultado live

| Métrica | Resultado |
|---|---:|
| Chamadas bem-sucedidas | 1 |
| Input tokens | 124 |
| Output tokens | 161 |
| Behaviors | 4 |
| Risks | 4 |
| Scenarios | 5 |
| Structured output válido | Sim |
| Estado resultante | `WAITING_FOR_CLARIFICATION` |

O estado de espera é resultado de domínio válido: o modelo indicou necessidade de esclarecimento. O processo CLI retornou código não zero, revelando a necessidade futura de códigos de saída distintos para pausa, falha e sucesso.

## Limitações

- apenas uma chamada bem-sucedida;
- validação local cobre chaves exatas e tipos básicos, mas ainda não substitui schemas completos;
- conversão de custo USD/BRL não foi implementada;
- o budget em BRL é autorização lógica, não hard stop no billing da OpenAI;
- retry e recuperação de schema inválido foram posteriormente validados offline no `EXP-005`; uma falha live ainda não foi provocada deliberadamente.

## Conclusão

O gateway direto é viável como baseline para comparação com PydanticAI. Structured output, tokens, modelo e resposta foram registrados. A abstração definitiva permanece aberta.

Após o teste live, foi adicionada validação local independente do provider para rejeitar campos extras e tipos incorretos. Dois testes unitários cobrem essas falhas.
