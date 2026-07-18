# EXP-001 — Máquina de estados Python versus LangGraph

- **Data:** 2026-07-12
- **Status:** concluído; decisão incorporada pela ADR-008 aceita em 2026-07-12
- **Baseline:** Python 3.13.5, LangGraph 1.2.9, langgraph-checkpoint-sqlite 3.1.0

## Pergunta

LangGraph agrega valor suficiente em persistência, inspeção e evolução do WF-001 para justificar dependências e abstração adicionais sobre uma máquina de estados explícita?

## Hipótese

A baseline Python será mais simples para transições básicas; LangGraph deverá demonstrar vantagem em checkpoint, retomada e human-in-the-loop.

## Contexto controlado

- mesmo `WorkflowRequest`;
- mesmo cassette `wf001_analysis_success`;
- mesmo gateway e BudgetController;
- mesmo resultado esperado: `SUCCEEDED`;
- geração e execução reais de testes fora deste spike.

## Implementações

### Baseline Python

- tabela explícita de transições;
- `RunState` por dataclass;
- validação de terminais;
- eventos JSONL e manifest pelo runner;
- zero dependências runtime externas.

### LangGraph

- `StateGraph` com roteamento condicional;
- `InMemorySaver` e `SqliteSaver`;
- estado composto somente por tipos primitivos;
- cinco testes dedicados;
- LangGraph 1.2.9 e 35 pacotes no ambiente isolado.

## Resultados

| Critério | Baseline Python | LangGraph |
|---|---|---|
| Resultado funcional do caso | Aprovado | Aprovado |
| Input inválido sem chamar modelo | Aprovado | Aprovado |
| Checkpoint pronto | Não implementado | Aprovado em memória |
| Estado inspecionável | Por JSON próprio | Snapshot nativo |
| Interrupção humana | Estado explícito, retomada não implementada | Aprovada com `interrupt`/`Command` |
| Persistência após recriar o runtime | Não implementada | Aprovada com SQLite local |
| Repetição da chamada LLM na retomada | Não avaliada | Não ocorreu; permaneceu em uma chamada |
| Dependências externas | 0 | 35 pacotes no venv |
| Linhas não vazias comparadas | 188 em state machine + runner | 105 no grafo |
| Serialização estrita | JSON próprio | Aprovada após correção |

## Finding durante o experimento

A primeira versão persistiu `WorkflowRequest` como dataclass. LangGraph alertou que desserialização de tipo não registrado será bloqueada futuramente. O estado foi alterado para dicionários primitivos e o teste foi repetido com `LANGGRAPH_STRICT_MSGPACK=true`, passando sem aviso.

## Limitações

- a baseline inclui runner e evidências, enquanto o arquivo LangGraph mede majoritariamente o grafo;
- a persistência SQLite foi validada localmente, mas ainda não sob concorrência ou falha abrupta;
- a baseline Python ainda não possui uma implementação equivalente de retomada durável;
- não houve benchmark de carga;
- contagem de linhas não mede complexidade sozinha.

## Conclusão e decisão incorporada

LangGraph demonstrou valor concreto em checkpoint, snapshot, interrupção humana e retomada após recriação do grafo. A retomada continuou do checkpoint sem repetir a chamada ao modelo. Lucas aceitou a ADR-008: LangGraph fica restrito ao adapter opcional de checkpoint e retomada humana; o runtime explícito e os application services ASEF continuam canônicos, sem dependência do framework no core.

## Encaminhamento realizado

- retry, budget, autorização e transições permanecem responsabilidades exclusivas do ASEF;
- a fronteira com PydanticAI continua pela porta tipada do modelo, sem acoplar os frameworks;
- a implementação e o rollback seguem os critérios da ADR-008.
