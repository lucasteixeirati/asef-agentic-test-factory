# Journal — 2026-07-11 — Etapa 2: contratos, workflow e avaliação

## Identificação

- **Dia do projeto:** Dia 1
- **Etapa/milestone:** Etapa 2
- **Período coberto:** 2026-07-11, após aprovação do Gate 1
- **Tipo de registro:** contemporâneo

## Entregáveis trabalhados

| Entregável | Estado inicial | Estado final |
|---|---|---|
| Topologia do WF-001 | Fluxo conceitual | 19 estados e transições definidos |
| Estado compartilhado | Não detalhado | Contrato conceitual versionado |
| Schemas | Requisitos macro | Inputs, resultados, avaliação e relatório definidos |
| Capabilities | Lista arquitetural | Contratos e erros normalizados |
| Sandbox | Princípios gerais | Budgets quantitativos propostos |
| Datasets | Categorias | Casos SMK, SEC e LCF catalogados |
| ADRs | Decisões distribuídas | Três decisões formalizadas |
| Aceite | Gate macro | Critérios por maturidade definidos |

## Medição em dias

- **Data de início:** 2026-07-11
- **Data de conclusão:** 2026-07-11
- **Dias corridos até o registro:** 1
- **Situação:** concluído e aprovado

## Uso de IA

| Ferramenta/IA | Finalidade | Resultado | Decisão humana pendente |
|---|---|---|---|
| ChatGPT/Codex | Estruturar especificações técnicas da Etapa 2 | Workflow, contratos, políticas, datasets e ADRs | Aprovar baselines e Gate 2 |

## Custos

- **Custo fixo vigente:** R$ 100,00 — ChatGPT Plus, validade informada de um mês.
- **Novo custo:** R$ 0,00.
- **Budget padrão de API proposto:** R$ 0,00 até autorização explícita.

## Decisões consolidadas

- controle do loop no workflow/runtime;
- profiles compostos por capabilities;
- independência entre SUT, testes e oracle;
- Docker Desktop como sandbox inicial;
- agente não corrige automaticamente possível defeito no SUT.

## Hipóteses a validar

- valores de CPU, memória, timeout e tamanho;
- oito chamadas de modelo como limite inicial;
- budgets de tokens;
- duas correções de teste;
- overhead e segurança observável do Docker Desktop;
- adequação dos contratos a Python, TypeScript e Java.

## Próximos passos

- iniciar a Etapa 3 — Spikes arquiteturais;
- implementar a baseline Python explícita;
- comparar frameworks uma dimensão por vez;
- validar sandbox, budgets, persistência e evidências.

## Encerramento

O responsável aprovou explicitamente o pacote e o Gate 2 em 2026-07-11. As baselines quantitativas estão autorizadas para experimentação e deverão ser confirmadas ou ajustadas por evidências na Etapa 3.
