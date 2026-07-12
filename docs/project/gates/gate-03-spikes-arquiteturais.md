# Gate 3 — Spikes arquiteturais

- **Data da revisão técnica:** 2026-07-12
- **Responsável pela decisão:** Lucas
- **Resultado atual:** pronto para decisão; ainda não aprovado pelo responsável
- **Próxima etapa proposta:** Etapa 4 — Walking skeleton

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

## Decisões requeridas do responsável

1. aceitar, rejeitar ou ajustar ADR-004;
2. aceitar, rejeitar ou ajustar ADR-005;
3. aceitar, rejeitar ou ajustar ADR-006;
4. aprovar ou rejeitar o Gate 3 e autorizar a Etapa 4.

## Decisão

Pendente de manifestação explícita do responsável. Este documento não autoriza automaticamente a Etapa 4.
