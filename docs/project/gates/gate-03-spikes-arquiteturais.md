# Gate 3 — Spikes arquiteturais

- **Data da decisão:** 2026-07-12
- **Responsável pela decisão:** Lucas
- **Resultado:** aprovado
- **Próxima etapa autorizada:** Etapa 4 — Walking skeleton

## Critérios avaliados

| Critério | Evidência | Avaliação técnica |
|---|---|---|
| Stack mínima escolhida com evidência | Matriz + EXP-001 a EXP-005 | Recomendação pronta |
| Isolamento bloqueia comportamentos proibidos | EXP-002, 9 testes de segurança Docker | Atendido no ambiente experimental |
| Execução pode ser persistida e explicada | SQLite, JSONL, state e manifest | Atendido |
| Tecnologias sem benefício foram removidas, limitadas ou adiadas | PydanticAI disponível sob política; OTel adiado | Atendido |
| LangGraph e PydanticAI avaliados separadamente | EXP-001 e EXP-004 | Atendido |
| Autoridade do loop principal está clara | ADR-001 e ADR-004/005 | Atendido |

## Stack proposta

- LangGraph condicional para grafo/checkpoint/human-in-the-loop;
- runtime ASEF como autoridade de estados, budgets, políticas e evidências;
- gateway OpenAI direto;
- Docker Desktop/WSL2 como sandbox experimental;
- JSONL + state + manifest;
- cassette como modo demo.

## Riscos residuais não bloqueadores para a Etapa 4

- warning `DOCKER_INSECURE_NO_IPTABLES_RAW` impede alegação de produção;
- warning de event loop do `pydantic_graph`, atualmente fora da stack proposta;
- teste live PydanticAI não realizado; uso futuro exigirá evidência própria;
- ambiente ainda não validado em macOS, Linux nativo ou ARM64;
- workspace gravável e limites totais de artefatos permanecem posteriores;
- primeira publicação GitHub ainda aguarda autenticação e criação remota.

## Decisões do responsável

1. ADR-004 aceita: LangGraph condicional no walking skeleton;
2. ADR-005 aceita: gateway direto e PydanticAI disponível sob política;
3. ADR-006 aceita: Docker Desktop como sandbox experimental;
4. Gate 3 aprovado e Etapa 4 autorizada.

## Decisão

O responsável aprovou explicitamente as recomendações e os ADRs em 2026-07-12. A Etapa 3 está encerrada e a Etapa 4 está autorizada.
