# Etapa 4 — Plano executável do Walking Skeleton

- **Data de início do planejamento:** 2026-07-12
- **Status:** planejamento concluído; implementação ainda não iniciada
- **Gate de entrada:** Gate 3 aprovado
- **Objetivo:** provar um fluxo vertical reproduzível e explicável, da entrada contextual até a execução isolada e o relatório.

## 1. Resultado esperado

Uma pessoa deve conseguir clonar o repositório, executar um único comando em modo demo e observar o ASEF:

1. carregar e validar um `QualityContext` fictício;
2. resolver sistema, repositório, perfil Python e skill `unit`;
3. validar requisito, SUT, políticas e budgets;
4. executar análise e geração por respostas gravadas;
5. gerar um teste unitário em workspace efêmero;
6. validar path, tamanho, schema e sintaxe;
7. executar o teste no Docker sem rede e sem acesso de escrita ao repositório original;
8. classificar o resultado;
9. produzir eventos, estado, manifest, snapshot contextual e relatórios;
10. explicar por que a run passou, aguardou uma pessoa ou falhou.

## 2. Recorte funcional

### Incluído

- WF-001, versão `0.1.0-skeleton`;
- Python 3.13 por imagem fixada em digest;
- SUT controlado: função pura `calculator.add(a, b)`;
- skill ASEF `unit`, nível skeleton;
- testes com `unittest` da biblioteca padrão;
- modo demo obrigatório e live opcional;
- gateway OpenAI Responses direto;
- LangGraph para grafo, checkpoint e interrupção;
- checkpoint SQLite por execução;
- Docker Desktop/WSL2 como sandbox experimental;
- JSONL, JSON, Markdown e hashes SHA-256;
- caminhos de sucesso, espera humana, input/contexto inválido, política e budget.

### Fora do escopo

- implementação completa das seis skills;
- pytest, coverage e mutation operacional;
- Node/TypeScript ou Java end-to-end;
- MCP real ou acesso a repositórios remotos;
- edição/exportação automática ao SUT original;
- interface web;
- execução paralela ou distribuída;
- correção completa de testes;
- deploy centralizado e OpenTelemetry;
- alegação de segurança para produção.

O metapacote PydanticAI permanece disponível no ambiente experimental, mas não participa do caminho padrão do skeleton.

## 3. Entradas do comando

Comando alvo:

```powershell
asef run `
  --context examples/context/walking-skeleton-context.json `
  --system calculator-service `
  --skill unit `
  --title "Add two integers" `
  --requirement "add(a, b) returns the arithmetic sum" `
  --mode demo `
  --output .asef/runs
```

Entradas obrigatórias:

- arquivo de contexto;
- `system_id`;
- skill solicitada ou seleção automática explicitamente habilitada;
- título e descrição do requisito;
- referência autorizada ao SUT;
- modo `demo` ou `live`;
- diretório de evidências dentro da raiz ASEF.

No modo live, API key no host e budget positivo continuam obrigatórios. O Gate 4 não depende de chamada live.

## 4. Resolução contextual

O contexto específico do skeleton deverá conter:

- perfil de QA fictício;
- equipe fictícia;
- sistema `calculator-service`;
- repositório local de exemplo;
- perfil `python-pytest`, mesmo usando `unittest` no skeleton;
- capabilities `unit`;
- skill `unit` habilitada;
- nenhum MCP selecionado na run;
- política LLM em modo gravado;
- scopes de leitura do exemplo e escrita apenas em `.asef`.

A run persiste somente snapshot sanitizado com IDs, versões, hashes, scopes efetivos e integrações utilizadas. Secrets e campos desnecessários ficam ausentes.

## 5. Fluxo ponta a ponta

```text
CLI
 ↓
carregar contexto → validar referências/scopes → selecionar skill/profile
 ↓
criar run + checkpoint + snapshot
 ↓
validar requisito e inspecionar SUT autorizado
 ↓
análise gravada/live
 ├─ ambiguidade → WAITING_FOR_CLARIFICATION → retomar mesma run
 └─ suficiente
 ↓
geração tipada de um artifact de teste
 ↓
política de path/tamanho/conteúdo + compile
 ├─ violação → POLICY_BLOCKED
 └─ válido
 ↓
montar workspace efêmero → Docker read-only → unittest
 ↓
normalizar execução → avaliar evidências → relatório
 ↓
SUCCEEDED ou FAILED classificado
```

## 6. Contratos que serão concretizados

### `SkeletonRunRequest`

- contexto, sistema e skill;
- requisito;
- SUT e profile resolvidos;
- modo;
- policy e budgets;
- outputs solicitados.

### `UnitTestArtifact`

- `schema_version`;
- `relative_path` dentro de `tests_generated/`;
- conteúdo UTF-8;
- IDs de cenários;
- attempt;
- hash calculado pelo runtime, nunca aceito do modelo.

### `ContextSnapshot`

- hash do QualityContext de origem;
- QA/team/system/repository/skill IDs;
- profile e imagem por digest;
- MCPs efetivamente usados — vazio no skeleton;
- provider/model/mode;
- scopes e policy IDs;
- sanitização aplicada.

### `NormalizedExecutionResult`

- comando registrado;
- exit code e classificação;
- duração;
- stdout/stderr truncados e indicadores;
- contagem de testes/passes/falhas quando disponível;
- imagem e limites;
- referências a evidências.

## 7. Workspace e segurança

- SUT original permanece read-only e nunca é alterado;
- runtime copia somente arquivos allowlisted para `.asef/runs/<run_id>/workspace/`;
- teste gerado é escrito apenas nessa cópia efêmera;
- container recebe o workspace montado read-only;
- bytecode é desabilitado ou redirecionado ao `/tmp`;
- rede, capabilities, rootfs, memória, PIDs, CPU e timeout seguem ADR-006;
- paths são normalizados após resolução de symlinks;
- arquivo gerado máximo: 20 KiB no skeleton;
- somente um arquivo `.py` em `tests_generated/`;
- imports permitidos: SUT do exemplo e biblioteca padrão necessária ao teste;
- nenhuma dependência é instalada durante a run.

## 8. Artefatos de uma run

```text
.asef/runs/<run_id>/
├── events.jsonl
├── state.json
├── manifest.json
├── context-snapshot.json
├── checkpoint.sqlite
├── artifacts/
│   └── attempt-001/tests_generated/test_calculator.py
├── results/
│   ├── static-validation.json
│   └── execution.json
├── report.json
└── report.md
```

Todos os documentos incluem `schema_version`. Manifest referencia hashes e não duplica conteúdo volumoso.

## 9. Exit codes da CLI

| Código | Significado |
|---:|---|
| 0 | `SUCCEEDED` |
| 2 | input ou contexto inválido |
| 3 | aguardando esclarecimento/revisão humana |
| 4 | falha funcional ou teste falho |
| 5 | `POLICY_BLOCKED` |
| 6 | `BUDGET_EXHAUSTED` |
| 7 | falha de provider ou infraestrutura |
| 130 | cancelamento pelo usuário |

O JSON final no stdout sempre contém ao menos `run_id`, `status`, `classification` e `report_path` quando disponível. Diagnóstico vai para stderr sem secrets.

## 10. Cenários obrigatórios

| ID | Cenário | Resultado esperado |
|---|---|---|
| WS-001 | Demo com teste válido | `SUCCEEDED`, teste executado e relatório completo |
| WS-002 | Requisito ambíguo | pausa persistida e retomada sem repetir nós concluídos |
| WS-003 | Contexto com referência inválida | exit 2 antes de LLM/Docker |
| WS-004 | Artifact tenta escapar de `tests_generated/` | `POLICY_BLOCKED`, Docker não executado |
| WS-005 | Saída inválida repetida | `BUDGET_EXHAUSTED`, evidências preservadas |
| WS-006 | Docker indisponível ou timeout controlado | exit 7 e `INFRASTRUCTURE_ERROR` |
| WS-007 | Cancelamento durante espera humana | `CANCELLED`, exit 130 ou comando explícito equivalente |

## 11. Estratégia de testes

- unitários: contratos, context resolver, policies, exit codes e normalização;
- contract tests: skill `unit`, gateway, language profile e evidence writer;
- golden tests: cassettes, prompts e relatórios sanitizados;
- integração: Docker, checkpoint SQLite e filesystem efêmero;
- end-to-end: CLI para WS-001 a WS-007;
- regressão: spikes continuam verdes até migração explícita;
- CI: core, frameworks e Docker em jobs separados.

Nenhum teste live é obrigatório em pull request.

## 12. Incrementos de implementação

### 4.1 — Contratos e estado

- schemas concretos;
- novos campos/referências de contexto;
- versionamento e migração do estado de spike;
- exit codes;
- testes de contrato.

**Checkpoint humano:** revisar contratos antes de integrar frameworks.

### 4.2 — Intake contextual e fixture

- contexto e SUT fictícios do calculator;
- resolução de sistema/repositório/skill;
- snapshot sanitizado;
- falha segura antes de efeitos colaterais.

### 4.3 — Grafo e gateways

- LangGraph sob ADR-001/004;
- análise e geração gravadas;
- interrupção/retomada;
- gateway live opcional e budgetado.

### 4.4 — Skill unit e artifacts

- contrato mínimo da skill;
- artifact tipado;
- workspace efêmero;
- validação de política e sintaxe.

### 4.5 — Docker, normalização e evidências

- executar `unittest`;
- normalizar resultado;
- emitir artifacts, hashes, eventos e reports;
- classificar infraestrutura separadamente.

**Checkpoint humano:** demonstrar WS-001 antes dos caminhos adversariais.

### 4.6 — Caminhos adversariais e UX

- WS-002 a WS-007;
- mensagens e exit codes;
- quickstart limpo;
- teste em clone/ambiente novo.

### 4.7 — Revisão e Gate 4

- regressão total;
- revisão de segurança e documentação;
- métricas e retrospectiva;
- pacote do Gate 4 para decisão do responsável.

## 13. Estimativa inicial

| Entregável | Estimativa em dias de projeto |
|---|---:|
| 4.1 Contratos e estado | 1–2 |
| 4.2 Contexto e fixture | 1 |
| 4.3 Grafo e gateways | 1–2 |
| 4.4 Skill e artifacts | 1–2 |
| 4.5 Docker/evidências | 1–2 |
| 4.6 Adversarial/UX | 1–2 |
| 4.7 Revisão/Gate | 1 |
| **Faixa total sem somar paralelismo** | **4–8 dias de projeto** |

A estimativa é uma baseline, não compromisso. A medição oficial continuará em dias corridos por entregável. Velocidade dos spikes não será extrapolada automaticamente.

## 14. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Transformar spike em produto sem fronteiras | novos módulos e contratos; migração explícita |
| LangGraph dominar semântica | ADR-001/004 e testes contra baseline |
| Snapshot vazar informação | allowlist de campos, hashes e secret scan |
| Teste gerado alterar SUT | workspace copiado e exportação inexistente |
| Demo esconder integração real | Docker e artifact reais; apenas LLM gravada |
| Escopo crescer para seis skills | implementar somente `unit`; demais permanecem catálogo |
| Multilíngue antecipado | profiles registrados, mas skeleton Python |
| Relatório parecer conclusão do produto | banner experimental e limitações explícitas |

## 15. Livro e jornada

Durante a etapa serão registrados:

- previsão versus duração real de cada incremento;
- quantidade aproximada de interações com IA;
- código/documentos sugeridos, revisados e rejeitados;
- defeitos introduzidos por IA e detectados pelos testes;
- diferença entre spike funcional e arquitetura integrada;
- primeiro momento em que outra pessoa puder reproduzir a run;
- impacto do `QualityContext` na seleção da skill;
- o que o autor faria diferente no próximo skeleton.

## 16. Condições do Gate 4

O Gate 4 somente será submetido quando todos os critérios de `docs/project/gates/gate-04-acceptance-plan.md` tiverem evidência. Execução live, múltiplas skills e múltiplas linguagens não são precondições.
