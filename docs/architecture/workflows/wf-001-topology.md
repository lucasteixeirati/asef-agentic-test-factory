# WF-001 — Topologia do workflow

## Objetivo

Definir o fluxo controlado para transformar requisito e SUT existente em cenários, testes executáveis e evidências de qualidade, sem permitir que o agente controle sozinho retries, budgets ou encerramento.

## Estados

| Estado | Natureza | Responsabilidade | Saída principal |
|---|---|---|---|
| `RECEIVED` | Determinística | Registrar e identificar a solicitação | Run criada |
| `VALIDATING_INPUT` | Determinística | Validar schema, caminhos e políticas iniciais | Input válido ou erro |
| `INSPECTING_SUT` | Mista | Descobrir projeto e extrair contexto permitido | Manifest do SUT |
| `ANALYZING_REQUIREMENT` | Agêntica tipada | Extrair comportamentos, restrições e ambiguidades | Análise estruturada |
| `WAITING_FOR_CLARIFICATION` | Humana | Pausar diante de ambiguidade bloqueadora | Resposta ou cancelamento |
| `ANALYZING_RISK` | Agêntica tipada | Priorizar riscos e áreas de teste | Risk assessment |
| `DESIGNING_SCENARIOS` | Agêntica tipada | Criar cenários e oracles candidatos | Test design |
| `REVIEWING_TEST_DESIGN` | Mista | Validar rastreabilidade, formato e políticas | Design aceito ou feedback |
| `GENERATING_TESTS` | Agêntica tipada | Gerar testes no perfil escolhido | Test artifacts |
| `STATIC_VALIDATION` | Determinística | Validar arquivos, sintaxe, imports e políticas | Validation result |
| `EXECUTING_TESTS` | Determinística isolada | Executar testes no Docker Desktop | Execution result |
| `EVALUATING_EVIDENCE` | Mista | Correlacionar resultados, coverage e oracles | Evaluation result |
| `WAITING_FOR_HUMAN_REVIEW` | Humana | Revisar possível defeito ou exportação | Decisão humana |
| `CORRECTING_TESTS` | Agêntica tipada | Corrigir exclusivamente testes e configuração permitida | Novo artifact set |
| `GENERATING_REPORT` | Mista | Consolidar fatos, inferências e recomendações | Relatório e manifest |
| `SUCCEEDED` | Terminal | Encerrar com critérios atendidos | Run bem-sucedida |
| `FAILED` | Terminal | Encerrar com falha classificada | Run falha |
| `CANCELLED` | Terminal | Encerrar por decisão humana ou cancelamento | Run cancelada |
| `POLICY_BLOCKED` | Terminal | Encerrar por violação de política | Evidência da violação |
| `BUDGET_EXHAUSTED` | Terminal | Encerrar ao atingir limite | Evidência do budget |

## Fluxo principal

```text
RECEIVED
  ↓
VALIDATING_INPUT
  ├── inválido ───────────────────────────────→ FAILED
  └── válido
       ↓
INSPECTING_SUT
  ├── perfil ausente/incompatível ───────────→ FAILED
  └── contexto válido
       ↓
ANALYZING_REQUIREMENT
  ├── ambiguidade bloqueadora → WAITING_FOR_CLARIFICATION
  │                                ├── resposta → ANALYZING_REQUIREMENT
  │                                └── cancelar → CANCELLED
  └── análise suficiente
       ↓
ANALYZING_RISK
  ↓
DESIGNING_SCENARIOS
  ↓
REVIEWING_TEST_DESIGN
  ├── inválido e retry disponível → DESIGNING_SCENARIOS
  └── aceito
       ↓
GENERATING_TESTS
  ↓
STATIC_VALIDATION
  ├── violação de política ───────────────────→ POLICY_BLOCKED
  ├── teste corrigível e retry disponível ───→ CORRECTING_TESTS
  └── válido
       ↓
EXECUTING_TESTS
  ├── infraestrutura sem retry ───────────────→ FAILED
  ├── infraestrutura com retry ───────────────→ EXECUTING_TESTS
  └── resultado disponível
       ↓
EVALUATING_EVIDENCE
  ├── teste inválido e retry disponível ─────→ CORRECTING_TESTS
  ├── possível defeito no SUT ───────────────→ WAITING_FOR_HUMAN_REVIEW
  ├── critérios atendidos ───────────────────→ GENERATING_REPORT
  └── falha não corrigível ──────────────────→ GENERATING_REPORT

CORRECTING_TESTS → STATIC_VALIDATION

WAITING_FOR_HUMAN_REVIEW
  ├── classificar como defeito → GENERATING_REPORT
  ├── autorizar correção de teste → CORRECTING_TESTS
  ├── exportar/aceitar resultado → GENERATING_REPORT
  └── cancelar → CANCELLED

GENERATING_REPORT
  ├── resultado aceito → SUCCEEDED
  ├── violação registrada → POLICY_BLOCKED
  ├── budget encerrado → BUDGET_EXHAUSTED
  └── falha registrada → FAILED
```

Qualquer estado não terminal poderá transitar para `CANCELLED`, `POLICY_BLOCKED` ou `BUDGET_EXHAUSTED` quando a respectiva condição ocorrer.

## Critérios de parada

Uma execução deve parar quando ocorrer primeiro:

- sucesso dos critérios obrigatórios;
- cancelamento humano;
- violação não recuperável de política;
- budget total ou específico esgotado;
- limite de correções atingido;
- falha de infraestrutura classificada como não recuperável;
- input ou perfil incompatível;
- revisão humana determinar encerramento.

## Política inicial de retries

| Categoria | Tentativas adicionais propostas | Condição |
|---|---:|---|
| Correção de teste | 2 | Somente arquivos de teste permitidos |
| Design inválido por schema | 1 | Feedback estruturado disponível |
| Chamada de provider transitória | 2 | Backoff e budget disponíveis |
| Execução de infraestrutura transitória | 1 | Ambiente pode ser recriado |
| Violação de política | 0 | Encerramento imediato |
| Possível defeito no SUT | 0 automático | Exige revisão humana |
| Input inválido | 0 automático | Requer nova solicitação |

Retries pertencem ao runtime e à política do workflow, não ao agente. Os valores serão validados na Etapa 3.

## Idempotência e efeitos colaterais

- nós anteriores a uma interrupção devem ser idempotentes ou registrar chave de deduplicação;
- artefatos são gravados por tentativa e nunca sobrescritos sem histórico;
- criação e remoção de container usam identificador da run;
- decisões humanas são append-only;
- exportação para fora do workspace exige aprovação explícita;
- retomada usa o último checkpoint consistente.

## Falhas classificadas

| Classe | Exemplo | Próxima ação |
|---|---|---|
| `INPUT_ERROR` | requisito ou caminho inválido | Encerrar e solicitar novo input |
| `TEST_ERROR` | teste não coleta ou possui sintaxe inválida | Corrigir dentro do budget |
| `SUT_DEFECT_SUSPECTED` | teste válido revela comportamento divergente | Revisão humana |
| `POLICY_VIOLATION` | rede, arquivo ou dependência proibida | Bloquear |
| `INFRASTRUCTURE_ERROR` | Docker indisponível | Retry limitado ou encerrar |
| `PROVIDER_ERROR` | timeout ou structured output inválido | Retry limitado |
| `BUDGET_ERROR` | tokens ou duração excedidos | Encerrar |
| `INCONCLUSIVE` | evidência insuficiente | Relatar e solicitar decisão |

## Aprovações humanas

- esclarecimento de requisito bloqueador;
- classificação final de possível defeito no SUT;
- autorização para exportar testes;
- alteração de política ou budget durante a run;
- continuidade após resultado inconclusivo, quando permitido.

