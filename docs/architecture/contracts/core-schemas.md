# Schemas conceituais do core

## Convenções gerais

- todos os schemas possuem `schema_version`;
- identificadores são estáveis e não carregam significado de negócio;
- timestamps usam UTC;
- enums rejeitam valores desconhecidos, salvo estratégia explícita de compatibilidade;
- texto não confiável possui limite e origem;
- artefatos volumosos são referenciados por hash;
- secrets nunca fazem parte dos schemas persistidos;
- a implementação inicial poderá usar Pydantic, sujeito aos spikes.

## `WorkflowRequest`

| Campo | Tipo | Regra |
|---|---|---|
| `request_id` | UUID | Gerado na entrada |
| `workflow_id` | string | Deve ser `WF-001` |
| `requirement` | `RequirementInput` | Obrigatório |
| `sut` | `SutInput` | Obrigatório |
| `language_profile` | string | Perfil registrado |
| `execution_mode` | enum | `demo` ou `live` |
| `provider_config_ref` | reference/null | Nunca contém secret |
| `policy_id` | string | Política registrada |
| `budget_overrides` | object/null | Somente reduções sem aprovação especial |
| `requested_outputs` | enum[] | Testes, relatório e artefatos permitidos |

## `RequirementInput`

| Campo | Tipo | Regra |
|---|---|---|
| `title` | string | 1–200 caracteres |
| `description` | string | Limite configurado |
| `acceptance_criteria` | string[] | Pode ser vazio, mas gera alerta |
| `constraints` | string[] | Restrições conhecidas |
| `examples` | object[] | Dados sanitizados |
| `source` | enum | `user`, `file`, `fixture` |

## `SutInput`

| Campo | Tipo | Regra |
|---|---|---|
| `workspace_ref` | path reference | Dentro de raiz autorizada |
| `entrypoint` | string | Função/componente permitido |
| `read_scope` | glob[] | Allowlist validada |
| `excluded_paths` | glob[] | Secrets, builds e diretórios proibidos |
| `expected_profile` | string/null | Pode solicitar autodetecção |
| `content_digest` | hash/null | Calculado na inspeção |

## `RequirementAnalysis`

| Campo | Tipo |
|---|---|
| `behaviors` | `Behavior[]` |
| `constraints` | `Constraint[]` |
| `ambiguities` | `Ambiguity[]` |
| `assumptions` | `Assumption[]` |
| `clarification_required` | boolean |
| `confidence_note` | string |

Cada item contém identificador, descrição, origem/evidência e severidade quando aplicável. “Confiança” será explicação qualitativa, não probabilidade inventada.

## `RiskAssessment`

| Campo | Tipo |
|---|---|
| `risks` | `RiskItem[]` |
| `prioritization_method` | string |
| `coverage_recommendation` | string[] |

`RiskItem` contém `risk_id`, comportamento relacionado, probabilidade ordinal, impacto ordinal, prioridade derivada e justificativa.

## `TestDesign`

| Campo | Tipo |
|---|---|
| `scenarios` | `TestScenario[]` |
| `coverage_summary` | object |
| `uncovered_items` | reference[] |
| `design_warnings` | string[] |

`TestScenario` contém identificador, requisito e risco relacionados, categoria, precondições, dados, passos conceituais, oracle proposto e prioridade.

## `GeneratedArtifact`

| Campo | Tipo |
|---|---|
| `artifact_id` | UUID |
| `attempt` | integer |
| `relative_path` | safe path |
| `media_type` | string |
| `content_hash` | hash |
| `size_bytes` | integer |
| `scenario_ids` | string[] |
| `generator_metadata_ref` | reference |

## `StaticValidationResult`

| Campo | Tipo |
|---|---|
| `valid` | boolean |
| `syntax_status` | enum |
| `policy_findings` | `Finding[]` |
| `dependency_findings` | `Finding[]` |
| `files_checked` | reference[] |
| `next_action` | enum |

## `ExecutionResult`

| Campo | Tipo |
|---|---|
| `execution_id` | UUID |
| `adapter_id` | string |
| `started_at` / `finished_at` | datetime |
| `exit_code` | integer/null |
| `status` | enum |
| `tests` | `NormalizedTestResult[]` |
| `summary` | object |
| `coverage` | `CoverageResult/null` |
| `mutation` | `MutationResult/null` |
| `stdout_ref` / `stderr_ref` | reference |
| `resource_usage` | object |
| `policy_events` | reference[] |

## `EvaluationResult`

| Campo | Tipo |
|---|---|
| `classification` | enum |
| `criteria` | `CriterionResult[]` |
| `facts` | `EvidenceClaim[]` |
| `inferences` | `EvidenceClaim[]` |
| `recommendations` | `EvidenceClaim[]` |
| `human_review_required` | boolean |
| `allowed_next_actions` | enum[] |

Classificações iniciais: `ACCEPTED`, `TEST_ERROR`, `SUT_DEFECT_SUSPECTED`, `POLICY_VIOLATION`, `INFRASTRUCTURE_ERROR`, `PROVIDER_ERROR`, `BUDGET_EXHAUSTED`, `INCONCLUSIVE`.

## `HumanDecision`

| Campo | Tipo |
|---|---|
| `decision_id` | UUID |
| `run_id` | UUID |
| `decision_type` | enum |
| `outcome` | enum |
| `reason` | string |
| `actor` | string sanitizada |
| `timestamp` | datetime |
| `related_evidence` | reference[] |

## `RunReport`

| Campo | Tipo |
|---|---|
| `run_id` | UUID |
| `final_status` | enum |
| `executive_summary` | string |
| `traceability` | object[] |
| `facts` | object[] |
| `inferences` | object[] |
| `recommendations` | object[] |
| `limitations` | string[] |
| `metrics_ref` | reference |
| `manifest_ref` | reference |
| `artifact_refs` | reference[] |

## Compatibilidade

Breaking changes incrementam versão major do schema. Leitores devem rejeitar versões incompatíveis de forma explícita. Migrações serão adicionadas somente quando houver mais de uma versão persistida real.

