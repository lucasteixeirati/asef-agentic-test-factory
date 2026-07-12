# Etapa 3 — Progresso dos spikes arquiteturais

## Status

Concluída e aprovada em 2026-07-12. ADR-004, ADR-005 e ADR-006 aceitas; Etapa 4 autorizada.

## Ambiente auditado

- Python 3.13.5;
- Docker Desktop 4.42.1;
- Docker Engine 28.2.2;
- backend WSL2/Linux x86-64;
- LangGraph 1.2.9 em `.venv`;
- langgraph-checkpoint-sqlite 3.1.0 em `.venv`;
- PydanticAI 2.9.0 completo mantido no `.venv` experimental por decisão do responsável;
- imagem Python fixada por digest.

## Concluído

| Spike | Evidência | Resultado |
|---|---|---|
| Baseline Python explícita | `src/asef_spike/` | Funcional |
| Modo demo gravado | cassette + CLI | `SUCCEEDED` |
| Structured output OpenAI live | EXP-003 | `WAITING_FOR_CLARIFICATION` válido |
| Docker security baseline | EXP-002 | 3/3 integrações aprovadas |
| LangGraph inicial | EXP-001 | Checkpoint e estado estrito aprovados |
| LangGraph human-in-the-loop | EXP-001 | Interrupção e retomada aprovadas |
| Persistência local durável | EXP-001 | Retomada após recriar o grafo aprovada com SQLite |
| Provider direto versus PydanticAI | EXP-004 | Gateway direto no caminho padrão; pacote completo disponível sob política |
| Recuperação de structured output | EXP-005 | Retry limitado e evidências aprovados |
| Docker adversarial | EXP-002 | 9/9 integrações de segurança aprovadas |
| Containers multilíngues | EXP-006 | Python, Node e Java aprovados por digest |
| Matriz tecnológica | technology-decision-matrix.md | Recomendações consolidadas |
| Evidências | JSONL, state e manifest | Funcional no recorte |

## Verificação atual

- 40 testes descobertos na suíte local: 30 aprovados e 10 integrações desabilitadas conforme a rodada;
- 10 integrações Docker reais aprovadas;
- 5 testes LangGraph aprovados;
- 5 testes PydanticAI aprovados sem chamadas live;
- compilação Python aprovada;
- API key ausente dentro do container;
- uma chamada live bem-sucedida, 124 tokens de entrada e 161 de saída.

## Findings relevantes

- budget usage precisa ser compartilhado pelo runtime;
- ACL de diretórios temporários do Windows interfere em bind mounts;
- estado de framework deve usar dados primitivos;
- retomada por checkpoint não repetiu a chamada ao modelo;
- CLI precisa distinguir espera humana de falha;
- structured output exige validação local;
- recuperação de schema pertence ao runtime e termina em budget explícito;
- PydanticAI reduz o adaptador, mas não deve controlar o workflow;
- metapacote PydanticAI aumentou o ambiente de 35 para 120 pacotes;
- `pydantic_graph` emitiu `DeprecationWarning` relacionado ao event loop no Python 3.13;
- alerta `DOCKER_INSECURE_NO_IPTABLES_RAW` permanece sob investigação.

## Encerramento

Não há pendência bloqueadora da Etapa 3. Riscos residuais permanecem versionados no Gate 3 e nas ADRs aceitas.
