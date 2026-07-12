# Gate 2 — Contratos, workflow e estratégia de avaliação

- **Data da decisão:** 2026-07-11
- **Responsável:** Lucas
- **Resultado:** aprovado
- **Próxima etapa autorizada:** Etapa 3 — Spikes arquiteturais

## Critérios avaliados

| Critério | Evidência | Resultado |
|---|---|---|
| Transições com condições claras | Topologia e modelo de estado | Atendido |
| Retries e encerramento limitados | Topologia e sandbox baseline | Atendido |
| Evidências especificadas | Schemas, contracts e evidence model | Atendido |
| Datasets cobrem sucesso, falha, ambiguidade e abuso | Catálogo SMK/SEC | Atendido |
| Casos equivalentes entre linguagens | LCF-001 a LCF-010 | Atendido |
| Fronteira de segurança explícita | Security strategy e sandbox policy | Atendido |

## Entregáveis aprovados

- topologia e estado compartilhado do WF-001;
- schemas conceituais do core;
- contratos de capabilities, profiles, provider, sandbox e evidências;
- política baseline de Docker Desktop e budgets;
- catálogo inicial dos datasets;
- critérios de aceite por maturidade;
- ADR-001, ADR-002 e ADR-003.

## Baselines autorizadas para experimento

- duas correções de teste;
- 2 vCPUs e 1 GiB de memória;
- 15 minutos por workflow sem espera humana;
- oito chamadas de modelo;
- 120 mil tokens de entrada e 40 mil de saída;
- custo de API padrão R$ 0,00 até autorização explícita;
- dez casos smoke, doze vetores de segurança e dez invariantes de conformidade.

Esses números não são definitivos. A Etapa 3 deverá confirmá-los, ajustá-los ou rejeitá-los com evidências.

## Pendências

Nenhuma pendência bloqueadora para iniciar os spikes. Escolhas definitivas de LangGraph, PydanticAI, persistência e tooling permanecem abertas.

## Decisão

O responsável aprovou explicitamente o pacote da Etapa 2. A etapa está encerrada e a Etapa 3 está autorizada.

