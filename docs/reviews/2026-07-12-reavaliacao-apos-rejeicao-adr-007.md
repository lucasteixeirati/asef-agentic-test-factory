# Reavaliação da Etapa 4 após rejeição da ADR-007

- **Data:** 2026-07-12
- **Status:** Opção C aprovada pelo responsável
- **Gatilho:** rejeição explícita da ADR-007

## Finding principal

A separação proposta foi prematura. O package `asef_spike` ainda contém aproximadamente 38 KiB de implementação funcional distribuída em CLI, contexto, budgets, domínio, eventos, gateway, DockerRunner, profiles, runner e state machine. O novo package `asef` contém aproximadamente 17 KiB concentrados em contratos e outcomes.

Continuar os incrementos 4.2–4.5 nessa condição criaria dois centros de gravidade:

- contratos novos em `asef`;
- comportamento real e adapters em `asef_spike`;
- dois modelos de estado e budget;
- CLI ainda apontando para o package de spike;
- testes e experimentos majoritariamente ligados ao package antigo.

Isso aumentaria retrabalho e tornaria a arquitetura pública menos clara.

## Opções avaliadas

### Opção A — Manter a ADR-007

Continuar com dois packages até o Gate 4 e rejeitar estado `1.x`.

**Avaliação:** rejeitada pelo responsável e não recomendada após o inventário.

### Opção B — Voltar tudo para `asef_spike`

Remover o novo package, manter o código atual e adiar arquitetura pública até o fim do skeleton.

**Vantagem:** menor mudança imediata.

**Risco:** o spike continuaria recebendo responsabilidades de produto e a dívida seria apenas adiada.

### Opção C — Promoção completa antes de nova ADR

Consolidar implementação e contratos em um único package `asef`, usando o histórico Git como preservação dos spikes. Implementar contexto e primeiro fluxo real antes de decidir a arquitetura definitiva.

**Avaliação:** recomendada.

## Direção recomendada

### 1. Um único núcleo

- mover budgets, contexto, domínio, eventos, profiles e policies reutilizáveis para `asef`;
- organizar adapters de gateway, Docker e LangGraph sob fronteiras explícitas;
- criar application service do WF-001;
- atualizar todos os testes e spikes para imports do package `asef`;
- remover `src/asef_spike` após equivalência de comportamento;
- manter temporariamente o comando `asef-spike` apenas como alias para a nova CLI, não como package paralelo.

O histórico anterior permanece recuperável por Git e pelos commits já publicados; não é necessário duplicar o núcleo para preservar a jornada.

### 2. Estado `1.1`, não rejeição total de `1.x`

- tratar `1.0` como estado de spike importável;
- evoluir para `1.1.0` com campos opcionais de contexto e proveniência;
- carregar documento `1.0` em estado `CONTEXT_UNRESOLVED`;
- exigir QualityContext válido antes de qualquer novo efeito colateral;
- preservar fatos, usage e history originais;
- não fingir retomada exatamente no meio de um nó;
- criar nova tentativa vinculada ao estado importado quando replay for necessário.

Essa estratégia oferece continuidade auditável sem inventar contexto ausente.

### 3. Implementar mais antes da próxima ADR

Combinar os checkpoints 4.1 e 4.2 e antecipar parte de 4.3–4.5:

1. contratos revisados e upgrader `1.0 → 1.1`;
2. QualityContext e fixture calculator;
3. ports e application service;
4. CLI pública `asef`;
5. gateway gravado para análise e artifact;
6. skill `unit` mínima;
7. workspace efêmero e evidências;
8. primeiro WS-001 executável, inicialmente com adapter determinístico;
9. LangGraph e Docker conectados somente após portas estáveis.

Uma nova ADR será submetida quando existir um fluxo vertical funcionando no package único. Assim, a decisão avaliará arquitetura executada, não somente contratos isolados.

## Nova sequência proposta

| Incremento revisado | Resultado |
|---|---|
| 4.R1 — Consolidação | package único, imports e testes migrados |
| 4.R2 — Contexto e estado 1.1 | fixture, resolver, snapshot e upgrader |
| 4.R3 — Application service | ports, CLI e fluxo determinístico |
| 4.R4 — Artifact e skill unit | geração gravada, policy e workspace |
| 4.R5 — Adapters reais | LangGraph, SQLite e Docker |
| Checkpoint arquitetural | nova ADR baseada no WS-001 funcional |
| 4.R6 — Adversarial/UX | WS-002 a WS-007 |
| 4.R7 — Gate 4 | evidências, quickstart e decisão |

## Impacto na estimativa

A consolidação adiciona trabalho imediato, mas remove migração duplicada posterior. A faixa da Etapa 4 passa provisoriamente de 4–8 para 6–10 dias de projeto. Essa estimativa será recalibrada após 4.R1.

## Riscos

- refactor amplo pode quebrar os spikes; mitigação por migração mecânica e regressão em cada módulo;
- estado `1.1` pode parecer compatível além do que é; documentação distinguirá import, replay e resume;
- antecipar componentes pode expandir escopo; WS-001 e skill `unit` continuam sendo o limite;
- nova ADR pode ser adiada demais; checkpoint obrigatório após o primeiro WS-001 funcional.

## Decisão requerida

O responsável aprovou explicitamente a Opção C e a sequência revisada. O incremento 4.R1 foi autorizado e executado.

## Resultado inicial

4.R1 consolidou toda a implementação em uma única distribuição/package raiz `asef`. O antigo source package foi removido; a baseline funciona em `asef.legacy` apenas como namespace interno temporário. Testes, spikes, Docker e CLI foram migrados e aprovados.
