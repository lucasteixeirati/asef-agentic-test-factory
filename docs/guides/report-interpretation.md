# Como interpretar o Alpha report

`report.json` é normativo. `report.md` é uma view determinística do mesmo `AlphaRunReport 1.0.0`; não deve acrescentar fatos, contagens, conclusões ou recomendações.

O report descreve uma run, não amplia o suporte do produto. Consulte a [matriz canônica de suporte e limitações](../project/support-and-limitations.md).

## Ordem de leitura

1. `schema_version`, `status`, `classification` e `terminal`;
2. `functional_result` e `attempts`;
3. `evidence.integrity_status`;
4. `facts` e a base de cada `inference`;
5. `quality`;
6. `recommendations` e `limitations`.

Uma recommendation não é executada pelo report e não muda status, classification, policy ou budget.

## Status e classification

Status descreve o ponto do workflow. Classification interpreta o resultado dentro da matriz pública. Combinações relevantes:

| Classification | Leitura correta | Próxima verificação |
|---|---|---|
| `ACCEPTED` | testes gerados satisfizeram a regra funcional desta run | contagens, evidence integrity e limitações |
| `TEST_FAILURE` | execução terminou, mas a regra funcional não foi satisfeita | artifact, outcome e contagens normalizadas |
| `TEST_ERROR` | teste não pôde ser coletado/executado como teste válido | static validation, resultado da ferramenta e evidence refs |
| `SUT_DEFECT_SUSPECTED` | evidência combinada justificou checkpoint humano | oracle/evaluation e decisão humana; não trate como defeito confirmado |
| `POLICY_VIOLATION` | runtime bloqueou input, artifact ou operação | erro tipado e policy aplicável |
| `BUDGET_ERROR` | um hard stop de chamadas, retries, tokens, tempo ou custo foi atingido | budgets versus usage observado |
| `PROVIDER_ERROR` | provider não produziu resultado utilizável | diagnóstico sanitizado, retry já consumido e disponibilidade externa |
| `INFRASTRUCTURE_ERROR` | Docker, filesystem, tooling ou persistência impediu a operação | doctor, daemon, imagem, paths e hashes |
| `WAITING_HUMAN` | run está pausada e não é terminal | checkpoint e comando `resume`/`cancel` |
| `CANCELLED_BY_USER` | decisão humana encerrou a run | intervention code e audit trail |
| `INCONCLUSIVE` | evidência disponível não sustenta conclusão mais forte | limitations e evidências faltantes |
| `INPUT_ERROR` / `CONTEXT_ERROR` | validação falhou antes ou na fronteira de contexto | argumento/contexto; pode não existir report se a run não foi criada |

`terminal=false` não deve ser lido como falha concluída. Espera humana produz state/checkpoint, mas não fabrica report terminal.

## Resultado funcional

`functional_result.accepted=true` exige:

- `tests > 0`;
- `passed == tests`;
- `failed == 0`;
- `errors == 0`;
- `skipped == 0`.

`null` significa não observado. Não converta `null` em zero. `conclusion_code` é uma conclusão fechada do runtime; texto livre do provider não controla esse código.

## Facts, inferences, recommendations e limitations

- fact: observação tipada com source e evidence refs opcionais;
- inference: conclusão que lista facts e evidence usados;
- recommendation: template allowlisted, sem executor;
- limitation: fronteira informativa, warning ou bloqueio interpretativo.

Se uma inference não apontar para IDs existentes, o contrato é inválido. Se uma recommendation não estiver ligada a inference ou limitation conhecida, também é inválida.

## Integridade de evidências

| Estado | Significado |
|---|---|
| `VERIFIED` | arquivo regular contido na run e SHA-256 reconciliado |
| `MISSING` | referência válida, mas arquivo não encontrado |
| `MISMATCH` | conteúdo/hash divergiu ou o path envolveu link/junction inseguro |
| `NOT_CHECKED` | integridade não foi verificada por esta emissão |

Evidence publicável precisa ser simultaneamente sanitizada e `VERIFIED`. `MISSING` ou `MISMATCH` exige `EVIDENCE_INTEGRITY_FAILURE`; o terminal funcional original permanece visível, mas a trilha não deve ser tratada como íntegra.

## Traceability

O report permite somente:

- requirement→behavior/risk/scenario;
- artifact→scenario (`COVERS_SCENARIO`);
- execution→artifact (`EXECUTES_ARTIFACT`).

Ele não infere risco→cenário. IDs `BEH`, `RSK` e `SCN` são contíguos; artifact e execution reconciliam com attempt.

## Quality capabilities

| Status | Leitura |
|---|---|
| `COMPLETED` | capability terminou e possui facts/evidence |
| `PARTIAL` | observação incompleta, com limitation explícita |
| `UNAVAILABLE` | capability não estava disponível no ambiente |
| `FAILED` | ferramenta/capability falhou |
| `BUDGET_EXHAUSTED` | admission/tempo/mutantes atingiu o teto |
| `NOT_REQUESTED` | esta run não solicitou a capability |

Coverage e mutation são sinais delimitados pelo escopo, versão e budget registrados. Não existe threshold universal embutido e quality não altera a acceptance funcional.

## Claims que o report não sustenta

Mesmo com `ACCEPTED` e todas as evidências verificadas, o report não prova:

- correção universal do SUT ou do teste;
- segurança para produção;
- isolamento absoluto contra código arbitrariamente hostil;
- certificação, pentest ou validação externa;
- causalidade de defeito sem decisão humana/evidência apropriada.

Em caso de inconsistência, não edite JSON/manifest manualmente. Preserve a run e siga [troubleshooting](troubleshooting.md).
