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

## Incremento 4.R3 — Application service determinístico

### Concluído

- ports `QualityContextPort` e `RunStorePort` independentes de frameworks;
- `PrepareRunService` como primeiro application service do WF-001;
- adapter de QualityContext em arquivo, com contenção no workspace;
- validação de repository local, scopes concretos e existência dos arquivos autorizados;
- `JsonRunStore` para estado, snapshot, manifest e eventos;
- CLI pública `asef prepare`, separada do alias legado `asef-spike`;
- SUT controlado `examples/calculator/calculator.py`;
- preparação determinística até a fronteira `ANALYZING_REQUIREMENT`;
- falhas de input/contexto retornam exit code 2 sem criar diretório de run.

### Limite honesto

4.R3 não conclui o WS-001 e não classifica a run como sucesso. Exit code 0 indica que a operação de preparação terminou corretamente; o estado permanece não terminal e `UNCLASSIFIED`, pronto para análise. Geração do artifact, execução e avaliação ainda não ocorreram.

### Verificação

- 73 testes descobertos: 63 aprovados e 10 integrações Docker desabilitadas por design;
- 6 testes novos de application service e CLI;
- execução manual da CLI produziu JSON legível por máquina e os quatro documentos mínimos;
- application core sem imports de OpenAI, LangGraph, Docker, PydanticAI ou adapters de filesystem.

### Finding

O contexto do calculator já existia em 4.R2, mas apontava para um diretório de SUT ainda ausente. A inspeção do 4.R3 revelou e corrigiu a lacuna antes de qualquer alegação de fluxo vertical.

### Próximo incremento

4.R4 — gateway gravado, artifact tipado, skill `unit`, policy e workspace efêmero. O checkpoint de nova ADR continua condicionado ao WS-001 funcional.

## Incremento 4.R4 — Artifact, skill unit e workspace

### Concluído

- ports tipados para análise, geração e workspace;
- adapter agêntico gravado com cassettes separados de análise e artifact;
- duas chamadas contabilizadas em usage sem dar ao adapter controle do fluxo;
- análise suficiente avança; ambiguidade termina em `WAITING_FOR_CLARIFICATION` antes da geração;
- geração de `UnitTestArtifact` com hash calculado localmente;
- rastreabilidade exata entre design e `scenario_ids` do artifact;
- skill `unit` baseada em AST para sintaxe, imports, chamadas proibidas e presença de testes;
- path, extensão, profundidade e limite de 20 KiB continuam protegidos pelo contrato;
- artifact rejeitado salvo em quarentena com nome controlado;
- workspace copia somente arquivos allowlisted e verifica hashes da origem e da cópia;
- SUT original verificado como não modificado;
- CLI `asef generate` encerra em `STATIC_VALIDATION`, pronta para execução.

### Fronteiras preservadas

- cassettes fornecem dados, não transições, paths efetivos ou autorização de escrita;
- policy pertence à skill/runtime, não ao adapter de modelo;
- nenhum artifact é exportado ao repositório do SUT;
- nenhum Docker ou LangGraph foi acoplado antes das portas estabilizarem;
- modo `live` não é aceito silenciosamente pelo comando gravado.

### Verificação

- 81 testes descobertos: 71 aprovados e 10 integrações Docker desabilitadas por design;
- 8 testes novos do 4.R4;
- 10 testes dos frameworks preservados;
- caminho manual produz artifact, static validation e workspace;
- os 4 testes gravados foram executados localmente contra a cópia do calculator e passaram;
- WS-004 parcialmente comprovado: path traversal resulta em `POLICY_BLOCKED` e nenhum workspace é criado.

### Findings

- a primeira implementação deixava o adapter classificar path inválido; a autoridade foi movida para a skill/runtime;
- um artifact bloqueado seria inicialmente persistido usando seu path não confiável; a revisão criou quarentena controlada;
- a checagem de secret do 4.R2 e a policy AST mostram o mesmo padrão: controles amplos demais geram falsos positivos, enquanto controles vagos deixam bypasses. Os testes adversariais calibram a fronteira.

### Próximo incremento

4.R5 — executar o workspace no Docker Desktop, normalizar evidências e avançar o WS-001 até avaliação/relatório. LangGraph/SQLite só será conectado se ainda agregar valor ao fluxo já funcional.

## Incremento 4.R5 — Execução, avaliação e relatório

### Concluído

- `TestExecutionPort` e output bruto independente de Docker;
- `DockerUnitTestAdapter` usando exatamente a imagem por digest do snapshot;
- política Docker com rede bloqueada, rootfs read-only, capabilities removidas, usuário 65534, limites de CPU/memória/PIDs e timeout;
- comando `unittest` com bytecode desabilitado no workspace read-only;
- normalização de duração, exit code, contagens, timeout e truncamento;
- stdout/stderr persistidos com SHA-256 e referências no estado/manifest;
- `execution.json`, `report.json` e `report.md`;
- avaliação determinística exige exit 0, ao menos um teste e todos aprovados;
- falha funcional, timeout e infraestrutura Docker recebem classificações distintas;
- exit codes Docker 125–127 tratados como infraestrutura;
- oracle usa a última contagem do `unittest`, evitando spoofing por output anterior;
- CLI `asef run` termina o WS-001 em `SUCCEEDED`/`ACCEPTED`;
- output público contido dentro de `.asef`.

### Evidência

- 90 testes descobertos: 79 aprovados e 11 Docker opt-in;
- 11/11 integrações Docker aprovadas localmente;
- 10/10 testes dos frameworks preservados;
- WS-001 real: 4 testes executados e aprovados no container;
- execução Docker observada em aproximadamente 2 segundos na rodada registrada;
- state, manifest e reports convergem em `SUCCEEDED`;
- wheel e CI serão novamente validados no checkpoint público.

### Findings e correções

- a fixture usava digest ilustrativo; passou a usar a imagem Python já comprovada;
- a primeira tentativa específica do E2E falhou no harness antes do Docker por invocação incorreta do `unittest`;
- `TemporaryDirectory` global/no Windows criou permissões incompatíveis com UID 65534; o E2E passou a usar pasta normal sob `.asef`, igual ao uso público;
- essa falha revelou que a CLI aceitava output fora da raiz declarada; agora rejeita antes de criar a run;
- o primeiro parser usava a primeira linha `Ran N tests`; agora usa a última para reduzir spoofing;
- exit 125 do Docker foi separado de falha do teste.

### Resultado

O primeiro WS-001 está funcional e reproduzível. Isso satisfaz a condição definida após a rejeição da ADR-007 para realizar um novo checkpoint arquitetural baseado em implementação real.

### Próximo passo

Revisar a arquitetura executada e decidir, em nova ADR, se LangGraph/SQLite agregam valor suficiente para entrar no runtime. Depois seguir para 4.R6 com WS-002 a WS-007; o Gate 4 permanece aberto até essas pendências serem sanadas.

## Checkpoint arquitetural pós-WS-001

- revisão baseada no fluxo funcional concluída;
- três opções comparadas: substituição total, runtime próprio e adoção limitada;
- substituição total não recomendada;
- ADR-008 proposta para LangGraph/SQLite somente em checkpoint e retomada humana;
- runtime explícito permanece canônico para WS-001;
- extra opcional preserva core sem dependências obrigatórias;
- dez critérios objetivos definidos para WS-002/WS-007;
- ADR-008 aceita explicitamente pelo responsável;
- implementação de WS-002/WS-007 autorizada dentro dos limites da decisão;
- nenhuma dependência foi adicionada ao core durante o checkpoint documental.
