# Pacote da Etapa 2 — Contratos, workflow e avaliação

## Objetivo

Especificar o comportamento do WF-001, seus contratos, políticas, datasets e critérios de aceite antes de escolher a implementação definitiva nos spikes.

## Entregáveis

| Entregável | Arquivo | Situação |
|---|---|---|
| Topologia do WF-001 | `../architecture/workflows/wf-001-topology.md` | Aprovado |
| Estado compartilhado | `../architecture/workflows/wf-001-state-model.md` | Aprovado |
| Schemas do core | `../architecture/contracts/core-schemas.md` | Aprovado |
| Contratos de capabilities | `../architecture/contracts/capability-contracts.md` | Aprovado |
| Sandbox e budgets | `../quality/sandbox-policy-baseline.md` | Aprovado para experimentação |
| Catálogo de datasets | `../quality/datasets/catalog.md` | Aprovado |
| Critérios de aceite | `acceptance-criteria.md` | Aprovado |
| Fronteiras de controle | `../architecture/adr/ADR-001-control-boundaries.md` | ADR aceita |
| Perfis compostos | `../architecture/adr/ADR-002-composable-language-profiles.md` | ADR aceita |
| Independência do oracle | `../architecture/adr/ADR-003-independent-sut-tests-oracle.md` | ADR aceita |

## Decisões e baselines propostas

1. WF-001 terá estados e terminais explícitos independentes do framework.
2. Retries pertencem ao runtime e à política, nunca ao agente isoladamente.
3. Possível defeito no SUT exige revisão humana.
4. Pydantic poderá implementar schemas, mas não faz parte do contrato conceitual.
5. Docker Desktop/WSL2 executará containers Linux efêmeros.
6. Modo live terá custo de API padrão R$ 0,00 até configuração explícita.
7. Correção de teste terá no máximo duas tentativas inicialmente.
8. A run terá baseline de 15 minutos, 8 chamadas de modelo, 120 mil tokens de entrada e 40 mil de saída, sujeitos a spikes.
9. Smoke Dataset começa com 10 casos e Security Dataset com 12 vetores.
10. Oracles e holdouts serão independentes da geração avaliada.

## Gate 2 — Resultado

| Critério | Evidência | Situação |
|---|---|---|
| Cada transição possui condição clara? | Topologia e tabela de estados | Aprovado |
| Retries e encerramento são limitados? | Topologia e sandbox baseline | Aprovado |
| Evidências necessárias estão especificadas? | Schemas e evidence model | Aprovado |
| Datasets cobrem sucesso, falha, ambiguidade e abuso? | Catálogo SMK/SEC | Aprovado |
| Há casos equivalentes para mais de uma linguagem? | LCF-001 a LCF-010 | Aprovado |
| Fronteira de segurança está explícita? | Security strategy e sandbox policy | Aprovado |

## Pontos que devem ser revisados pelo responsável

- quantidade e categorias dos estados;
- retries propostos;
- budgets quantitativos baseline;
- custo de API padrão zero;
- estrutura e quantidade inicial dos casos de dataset;
- critérios de aceite por maturidade.

## Decisão

O responsável aprovou explicitamente o pacote em 2026-07-11. Os budgets quantitativos foram aprovados como baselines a experimentar na Etapa 3, não como valores definitivos. A Etapa 2 está encerrada e a Etapa 3 está autorizada.
