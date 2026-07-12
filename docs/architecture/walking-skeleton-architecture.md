# Arquitetura planejada do Walking Skeleton

- **Estado:** planejada; deve ser atualizada após a implementação real
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

## Questões que a implementação deve responder

- LangGraph ficará encapsulado sem vazar `Command` ou snapshots ao domínio?
- checkpoint por run é suficiente ou um banco compartilhado melhora operação local?
- como distinguir artifact inválido de provider inválido sem duplicar retry?
- qual representação normalizada de `unittest` será estável para pytest/JUnit/Vitest futuros?
- quanto do QualityContext precisa ser persistido versus referenciado por hash?

Respostas deverão atualizar este documento e, quando arquiteturalmente relevantes, gerar ADR.
