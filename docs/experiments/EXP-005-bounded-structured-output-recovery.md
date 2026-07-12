# EXP-005 — Recuperação limitada de structured output inválido

- **Data:** 2026-07-12
- **Status:** aprovado para o recorte da Etapa 3
- **Execução:** offline e determinística

## Pergunta

O runtime consegue recuperar uma saída inválida sem criar loop infinito, perder a autoridade sobre budgets ou depender exclusivamente da validação do provider/framework?

## Hipótese

A recuperação deve pertencer ao runtime. O gateway executa e contabiliza chamadas; o runtime valida, registra evidências e autoriza no máximo `max_provider_retries` novas tentativas.

## Política implementada

1. Toda saída passa pela validação local.
2. JSON malformado ou falha de validação interna do adaptador usa `InvalidStructuredOutput`.
3. O runtime registra `PROVIDER_OUTPUT_INVALID` antes de tentar recuperação.
4. Cada nova tentativa reserva `provider_retries` e também uma nova `model_call` no gateway.
5. O prompt de reparo contém somente o contrato esperado e até 500 caracteres do erro; a saída inválida não é reinjetada.
6. Ao esgotar retries, a execução termina em `BUDGET_EXHAUSTED` e persiste estado, eventos e manifest.

## Casos executados

| Caso | Resultado |
|---|---|
| Tipo inválido seguido de saída válida | `SUCCEEDED`, 2 chamadas, 1 retry |
| Tipo inválido em todas as tentativas | `BUDGET_EXHAUSTED`, evidências persistidas |
| `InvalidStructuredOutput` gerado dentro do gateway seguido de saída válida | `SUCCEEDED`, mesma política aplicada |
| Reserva além de `max_provider_retries` | `BudgetExceeded`, contador sem incremento parcial |
| Prompt de reparo | Limitado e sem cópia da saída inválida |

## Evidências

- 24 testes locais aprovados na fotografia do EXP-005, antes da ampliação posterior da suíte Docker;
- 5 testes LangGraph aprovados;
- 5 testes PydanticAI aprovados;
- nenhuma chamada live e nenhum crédito consumido neste experimento.

## Findings

- retry de schema é decisão do runtime, não detalhe invisível do provider;
- `model_calls` e `provider_retries` medem dimensões diferentes e ambas precisam de limite;
- falha repetida de schema é classificada como esgotamento de budget, não exceção não tratada;
- a mensagem de reparo não precisa repetir conteúdo potencialmente volumoso ou hostil;
- erros de validação originados no runner e no gateway podem compartilhar a mesma política.

## Limitações

- o teste usa um gateway sequencial determinístico, não uma falha live do provider;
- não há backoff porque o problema é semântico, não indisponibilidade transitória;
- se um framework abortar sem expor o objeto de uso, os tokens daquela tentativa podem não ser contabilizados localmente, embora a chamada seja contada;
- custo monetário ainda não é convertido por execução;
- a política não cobre retries de rede ou infraestrutura, que exigem classificação separada.

## Conclusão

A recuperação é limitada, observável e independente do adaptador. O finding crítico sobre loops infinitos de correção está mitigado no recorte do WF-001. O desenho deve ser preservado ao substituir gateways de spike por implementações de produção.
