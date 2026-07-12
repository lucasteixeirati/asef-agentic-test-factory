# Etapa 4 — Progresso do Walking Skeleton

## Status

Em andamento desde 2026-07-12 sob a Opção C. ADR-007 rejeitada; 4.R1 e 4.R2 concluídos.

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

A Opção C foi aprovada. O próximo incremento é 4.R2 — QualityContext, fixture calculator e estado `1.1` importável.

## Incremento 4.R1 — Consolidação em package único

### Concluído

- todos os módulos migrados para `src/asef`;
- namespaces `adapters`, `runtime`, `evidence` e `legacy` explícitos;
- `src/asef_spike` removido da distribuição e sem source rastreado;
- testes e spikes migrados para imports `asef`;
- scripts `asef` e alias temporário `asef-spike` apontam para a mesma CLI;
- README e referência do contexto atualizados;
- wheel contém somente o package raiz `asef`;
- demo legada executada em `SUCCEEDED`.

### Verificação

- 60 testes descobertos localmente: 50 aprovados e 10 integrações desabilitadas por design;
- 10 testes de frameworks aprovados;
- 10 integrações Docker aprovadas;
- wheel `asef-agentic-test-factory 0.1.0a1` com 17 módulos ASEF;
- nenhum módulo `asef_spike` no wheel;
- zero imports residuais do package removido em source, testes e spikes.

### Finding do harness

O primeiro teste de ausência do package antigo encontrou sua própria string de busca e falhou. O detector passou a construir o nome dinamicamente e toda a regressão foi repetida.

### Limite

`asef.legacy` preserva o comportamento antigo dentro do package único. Ele não é API alvo e será reduzido à medida que application service e estado `1.1` assumirem o fluxo.

## Incremento 4.R2 — Contexto e estado 1.1

### Concluído

- schema corrigido de `2.0.0` provisório para `1.1.0`;
- origens `NEW`, `IMPORTED` e `REPLAY` explícitas;
- resolução `CONTEXT_UNRESOLVED`/`CONTEXT_RESOLVED`;
- importador estrito de `1.0.0`, sem alegar resume;
- preservação de facts, history, errors, attempts, usage e budgets originais;
- replay com novo `run_id` e vínculo ao source;
- resolução explícita do contexto antes de efeitos colaterais;
- resolver de `QualityContext` e fixtures versionadas do calculator e do spike.

| Operação | Identidade | Contexto | Pode executar? |
|---|---|---|---|
| Nova run | novo `run_id` | inicialmente não resolvido | somente após snapshot |
| Import | preserva identidade do documento | não resolvido | não; serve como evidência |
| Replay | novo `run_id`, vinculado ao import | snapshot obrigatório | sim, desde o início |

Import não é resume. Replay não continua no meio de um nó e zera o consumo da nova run, preservando dados anteriores como proveniência.

### Verificação

- 67 testes descobertos: 57 aprovados e 10 integrações Docker desabilitadas por design;
- 26 testes dos contratos do skeleton e 6 de contexto;
- import de versão diferente de `1.0.0` rejeitado.

A proteção contra secrets no import também foi exercitada. A primeira regra confundiu `input_tokens` com credencial; o falso positivo foi detectado e a política passou a usar nomes sensíveis específicos.

### Fricção registrada

A primeira execução específica usou paths como módulos em uma pasta `tests` sem `__init__.py`. Nenhum teste do produto rodou nessa tentativa; o harness foi corrigido para discovery.

### Próximo incremento

4.R3 — ports, application service e CLI pública para o primeiro fluxo determinístico.
