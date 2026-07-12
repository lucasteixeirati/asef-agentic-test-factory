# ADR-001 — Fronteiras de controle entre workflow, runtime e agente

- **Status:** aceita
- **Data:** 2026-07-11
- **Responsável:** Lucas

## Contexto

LangGraph, PydanticAI, gateways de modelo e código próprio podem oferecer retries, loops ou controle de execução. Sem fronteiras explícitas, dois runtimes podem competir e tornar comportamento, teste e retomada imprevisíveis.

## Drivers

- controle determinístico;
- auditabilidade;
- human-in-the-loop;
- substituição de frameworks;
- testes de transição;
- budgets e critérios de parada únicos.

## Opções consideradas

1. Delegar o loop ao agente/framework de maior nível.
2. Permitir que cada componente faça seus próprios retries.
3. Centralizar controle no workflow/runtime e limitar agentes a outputs tipados.

## Decisão

Adotar a opção 3:

- workflow define estados, transições e condições;
- runtime valida e aplica transições, budgets, persistência e políticas;
- agente produz análise, decisão candidata ou artefato tipado;
- skills executam capacidades limitadas;
- adapters traduzem ferramentas e providers;
- retries são autorizados pela política central.

## Consequências

### Positivas

- fluxo observável e testável;
- menor acoplamento a frameworks;
- critérios de parada consistentes;
- retomada e auditoria simplificadas.

### Negativas

- mais código explícito no core;
- recursos automáticos de frameworks podem não ser utilizados;
- integração exige adapters disciplinados.

## Evidências

- Planejamento Mestre aprovado;
- revisão cross-model;
- topologia do WF-001.

## Revisitar quando

Um spike demonstrar que delegar parte do controle reduz complexidade sem duplicar loops, enfraquecer budgets ou perder auditabilidade.

