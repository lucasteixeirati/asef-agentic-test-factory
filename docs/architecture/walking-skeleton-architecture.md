# Arquitetura planejada do Walking Skeleton

- **Estado:** package consolidado em 4.R1; contexto/estado 1.1 implementados em 4.R2
- **Etapa:** 4

## Componentes e autoridade

| Componente | Responsabilidade | Não pode fazer |
|---|---|---|
| CLI | parsear input, invocar runtime, mapear exit code | decidir política ou esconder falha |
| ContextLoader/Resolver | validar e resolver contexto efetivo | obter secret ou ampliar scope |
| Runtime ASEF | estados, budgets, policies, retries e evidências | delegar autoridade ao modelo |
| LangGraph adapter | grafo, checkpoint e interrupção | definir semântica de domínio |
| Gateway | uma chamada tipada e uso reportado | retry autônomo ou transição |
| Skill `unit` | gerar/validar plano e artifact unitário | escrever no SUT original |
| WorkspaceManager | copiar allowlist e armazenar tentativas | montar path fora da raiz ASEF |
| DockerRunner | executar comando permitido com limites | receber secret ou rede implícita |
| EvidenceWriter | eventos, hashes, snapshots e reports | transformar inferência em fato |

## Dependências

```text
CLI → ApplicationService → RuntimePort
                         ├→ ContextPort
                         ├→ WorkflowEnginePort → LangGraphAdapter
                         ├→ ModelGatewayPort → Recorded/OpenAI Gateway
                         ├→ SkillPort → UnitSkill
                         ├→ SandboxPort → DockerRunner
                         └→ EvidencePort → FilesystemEvidenceWriter
```

Domínio e application service não importam LangGraph, OpenAI ou Docker diretamente. Adapters traduzem seus resultados para contratos ASEF.

## Estado e persistência

- estado persistido usa tipos primitivos e referências;
- SQLite contém checkpoints, não secrets nem artifacts volumosos;
- eventos são append-only;
- cada tentativa cria path próprio;
- retomada usa `run_id` e decisão humana identificada;
- report é derivado de fatos persistidos, não de memória do chat.

## Separação de fatos e inferências

Fatos:

- hashes, comandos, imagem, exit code, duração, testes e policy findings.

Inferências:

- risco sugerido pelo modelo, possível causa e recomendação.

O relatório identifica a natureza de cada afirmação e sua evidência relacionada.

## Decisões de implementação antecipadas

- Python package deixa de usar o nome conceitual de spike no caminho público quando o skeleton estiver estável;
- `DemoWorkflowRunner` não será expandido indefinidamente; servirá de baseline durante a extração do application service;
- cassettes continuam em fixtures e possuem schema/versionamento;
- PydanticAI não entra no caminho padrão;
- `unittest` reduz dependências no skeleton; pytest retorna no alpha Python conforme o profile.

## Realizado no incremento 4.1

- package `asef` criado sem imports de frameworks;
- contratos-base `1.0.0`, execução `1.1.0` e estado persistido `1.3.0` com métricas live do 5.4;
- status, classificações e exit codes separados;
- estado `1.x` dos spikes explicitamente incompatível;
- budgets e evidências serializáveis em tipos primitivos;
- ADR-007 submetida ao checkpoint humano.

## Revisão após rejeição da ADR-007

- ADR-007 rejeitada;
- implementação consolidada em um único package `asef`;
- adapters, runtime, evidence e baseline legada agora são namespaces internos;
- package `asef_spike` removido da distribuição;
- o estado `1.1` distingue nova run, import e replay;
- import preserva evidência `1.0`, mas não concede capacidade de execução;
- replay cria nova identidade e exige snapshot contextual válido;
- o resolver transforma `QualityContext` validado em snapshot primitivo antes dos efeitos;

## Implementação 4.R3

O primeiro application service termina na fronteira agêntica `ANALYZING_REQUIREMENT`:

```text
CLI pública
  -> FileQualityContextAdapter
  -> PrepareRunService (ports)
  -> JsonRunStore
```

O serviço conhece somente contratos e protocols. Paths e JSON pertencem aos adapters. A validação completa de request, contexto, scopes e existência do SUT ocorre antes da criação do diretório da run. O estado preparado contém manifest mínimo do SUT, mas não afirma que análise, geração ou execução já aconteceram.

## Implementação 4.R4

```text
GenerateUnitTestService
  -> AgenticTestPort -> RecordedAgentAdapter
  -> UnitSkill (contrato + AST + rastreabilidade)
  -> WorkspacePort -> EphemeralWorkspaceAdapter
  -> RunStorePort -> evidências e quarentena
```

O adapter gravado retorna apenas análise e artifact candidatos. O application service controla usage e transições. A skill decide se o artifact pode chegar ao workspace. Paths rejeitados nunca são usados para escrita: o conteúdo é preservado em `artifacts/rejected/attempt-001.txt`. O workspace contém cópias allowlisted e o teste gerado; hashes comprovam que o SUT original não foi alterado durante o staging.

## Implementação 4.R5

```text
CompleteWorkflowService
  -> GenerateUnitTestService
  -> TestExecutionPort -> DockerUnitTestAdapter -> DockerRunner
  -> RunStorePort -> execution + reports + estado terminal
```

O application service avalia apenas `ExecutionOutput`/`NormalizedExecutionResult`; não importa Docker. O adapter executa a imagem fixada pelo snapshot. A aceitação exige exit 0, contagem positiva, zero falhas e igualdade entre testes executados e aprovados. Falhas do daemon/CLI Docker (125–127) e timeout são infraestrutura, não defeitos funcionais.

O WS-001 termina em `SUCCEEDED`/`ACCEPTED`. LangGraph continua fora do runtime principal: agora existe evidência suficiente para comparar seu valor contra este fluxo explícito, em vez de decidir por expectativa.

## Implementação 4.R6a — waits humanos

```text
HumanCheckpointPort
  -> LangGraphHumanCheckpointAdapter
  -> checkpoint.sqlite por run

HumanDecisionService
  -> load state + snapshot ASEF
  -> resume/cancel validado
  -> continuar application services explícitos
```

O adapter importa LangGraph somente dentro da operação e pertence ao extra `workflow-langgraph`. O core continua instalável e testável sem a dependência. A decisão confirmada no checkpoint é idempotente; se o processo falhar depois do `Command(resume)`, uma nova invocação recupera a mesma decisão.

Antes de continuar, o serviço recarrega e valida `state.json`, compara o snapshot persistido com o QualityContext atual, sanitiza a resposta humana e grava uma decisão append-only. Resume mantém a mesma `run_id`; cancelamento não cria artifact, workspace ou container.
- nova ADR será criada apenas após o primeiro WS-001 funcional.

## Questões que a implementação deve responder

- LangGraph ficará encapsulado sem vazar `Command` ou snapshots ao domínio?
- checkpoint por run é suficiente ou um banco compartilhado melhora operação local?
- como distinguir artifact inválido de provider inválido sem duplicar retry?
- qual representação normalizada de `unittest` será estável para pytest/JUnit/Vitest futuros?
- quanto do QualityContext precisa ser persistido versus referenciado por hash?

Respostas deverão atualizar este documento e, quando arquiteturalmente relevantes, gerar ADR.
