# Etapa 4 — Progresso do Walking Skeleton

## Status

Em replanejamento desde 2026-07-12. O incremento 4.1 produziu evidência técnica, mas a ADR-007 foi rejeitada e seus contratos não constituem arquitetura aceita.

## Incremento 4.1 — Contratos e estado

### Concluído

- novo package `asef` separado de `asef_spike`;
- distribuição `asef-agentic-test-factory 0.1.0a1`, mantendo CLI legada temporária;
- request do skeleton;
- artifact unitário tipado e limitado;
- snapshot contextual sanitizado;
- evidence refs;
- resultado de execução normalizado;
- budgets e usage;
- estado schema `2.0.0`;
- status, classificações e exit codes;
- rejeição explícita de estado `1.x`;
- 19 testes dedicados;
- documentação dos schemas;
- ADR-007 proposta.

### Verificação

- 59 testes descobertos na suíte local;
- 49 aprovados;
- 10 integrações Docker desabilitadas na rodada local por design;
- nenhum framework importado pelo package público de contratos;
- wheel contém `asef` e `asef_spike` durante a transição;
- nenhuma alteração em LangGraph, gateway ou Docker neste incremento.

### Fricções e findings

- a primeira invocação do teste específico usou caminho como módulo em um diretório sem `__init__.py`; discovery corrigiu o harness;
- testes detectaram `ResourceWarning` por leitura sem context manager; foi corrigido com `Path.read_text`;
- estado do spike não possui dados suficientes para migração segura;
- budget precisa ser validado como parte do estado, não apenas durante execução;
- command evidence também pode carregar secrets e recebeu validação defensiva.
- a primeira build ainda produziu `asef-spike 0.0.1`; o metadata foi corrigido antes do checkpoint público.
- a primeira CI do checkpoint passou, mas alertou sobre actions baseadas em Node 20; checkout/setup-python foram atualizadas para v6/Node 24.

## Resultado do checkpoint 4.1

ADR-007 rejeitada. A revisão identificou que manter `asef` e `asef_spike` como dois núcleos aumentaria duplicação e retrabalho.

## Novo checkpoint requerido

Revisar `docs/reviews/2026-07-12-reavaliacao-apos-rejeicao-adr-007.md`. Nenhuma nova mudança estrutural deve ocorrer antes da decisão sobre a promoção completa para um package único e estado `1.1` importável.
