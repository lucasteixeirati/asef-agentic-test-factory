# Incremento 5.5 — Smoke Dataset executável

- **Data:** 2026-07-15
- **Estado:** implementação concluída; revisão local aprovada; CI pública pendente
- **Dependências:** incrementos 5.1 a 5.4 concluídos e publicados até `v0.1.0a3`
- **Gate relacionado:** G5-02 e G5-10, com evidência complementar para G5-05, G5-06, G5-07, G5-08, G5-09, G5-15, G5-17 e G5-20
- **Decisão para implementar:** aprovada explicitamente por Lucas em 2026-07-15

## 1. Objetivo

Transformar o catálogo Smoke em uma suíte demo executável, determinística, keyless e auditável que percorra dez comportamentos relevantes do WF-001. O resultado da suíte deve comparar fatos observados com expectativas versionadas, preservar evidências por caso e gerar relatórios JSON e Markdown agregados.

Um caso intencionalmente encerrado como espera humana, policy block, budget ou infraestrutura conta como aprovado quando esse resultado coincide com sua expectativa. O score da suíte mede conformidade da implementação com os casos curados; não mede qualidade universal do modelo e não constitui benchmark estatístico.

## 2. Escopo

### Incluído

- materializar `SMK-001` a `SMK-010` com `case.json`, requisito, oracle quando aplicável e fixture demo;
- carregar e validar todo o dataset antes de iniciar qualquer run;
- compor o fluxo Alpha já existente: análise, geração, static policy, execução pytest, oracle independente, correção limitada e checkpoint humano;
- executar em modo demo com cassettes gravados, sem rede de provider e sem `OPENAI_API_KEY`;
- usar Docker real nos casos que precisam de evidência de teste/oracle;
- usar fault injection explícita somente no caso de Docker indisponível;
- comparar status, classificação, ação, budgets e contadores esperados;
- produzir relatório agregado e fingerprint semântico de reprodutibilidade;
- disponibilizar comando público `asef smoke` com dataset e output explícitos;
- adicionar job de CI próprio para a suíte Smoke.

### Não incluído

- novas chamadas live ou gravação de novos cassettes a partir de provider;
- coverage e mutation do SUT, pertencentes ao 5.6;
- catálogo formal `SEC-001` a `SEC-012` e `asef doctor`, pertencentes ao 5.7;
- consolidação final da experiência pública e reports do Alpha, pertencente ao 5.8;
- execução estatística, comparação de modelos, ranking ou alegação de benchmark;
- paralelismo, execução distribuída ou correção automática do SUT;
- embutir o dataset no wheel. No 5.5, `--dataset-root` será explícito; a distribuição da experiência completa será decidida no 5.8.

## 3. Findings da baseline que o incremento deve resolver

1. Existem apenas quatro casos materiais: `SMK-001`, `SMK-002`, `SMK-003` e `SMK-007`.
2. `DatasetCase` descreve semântica e isolamento, mas não contém a fixture determinística necessária para executar a demo.
3. O contexto público atual autoriza somente `examples/calculator`, enquanto os casos Alpha apontam para `examples/python-alpha/*_sut`.
4. `UnitSkill` possui imports fixos para calculator/unittest e precisa receber uma allowlist composta para `reference_sut`, sem acoplar o core a pytest.
5. O adapter gravado atual reproduz somente análise e geração; o SMK-006 exige sequência imutável de geração e correção.
6. O coordenador do 5.3 existe internamente, mas ainda não há serviço que conecte uma run preparada e um artifact inicial ao fluxo Alpha completo.
7. O catálogo descreve o SMK-006 como erro de sintaxe. Sintaxe inválida é corretamente bloqueada pela static policy antes do Docker e, portanto, não alcança o loop de `TEST_ERROR`.

## 4. Decisões de desenho

### 4.1 Dataset semântico separado da fixture demo

`case.json` continuará neutro e descreverá objetivo, SUT, requisito, oracle, exposição e classificações aceitáveis. Cada caso receberá `demo.json`, validado por um novo contrato `SmokeDemoSpec`, para declarar somente:

- `schema_version`, `case_id` e `case_version` correspondentes ao `case.json`;
- contexto e system ID autorizados;
- cassette de análise;
- sequência ordenada de cassettes de artifact: geração inicial e até duas correções;
- tipo de executor: `PYTEST_DOCKER`, `INJECTED_DOCKER_UNAVAILABLE` ou `NOT_REACHED`;
- status, classificação e ação terminal esperados; ação aceita `ACCEPT`, `HUMAN_REVIEW`, `STOP` ou `NOT_REACHED` quando a avaliação combinada não ocorre;
- contadores esperados ou intervalos: model calls, provider retries, correções e tentativas executadas;
- flags esperadas: Docker chamado, oracle executado e checkpoint humano solicitado.

A fixture escolhe entradas e expectativas, mas não controla transições. Workflow, retries, budgets e decisões continuam na aplicação.

### 4.2 Contexto Alpha explícito

Será criado `examples/context/python-alpha-smoke-context.json` com dois sistemas/repositórios locais:

- SUT de referência: root autorizado em `examples/python-alpha/reference_sut/src`;
- SUT defeituoso: root autorizado em `examples/python-alpha/defective_sut/src`.

Os `read_scope` nomearão arquivos concretos sob `reference_sut/`. Oracle e `demo.json` permanecerão fora dos inputs autorizados de geração. A policy será `recorded`, permitirá análise, geração e correção, e não conterá credenciais.

### 4.3 Policy de imports composta

`UnitSkill` receberá allowlist explícita por composição, preservando o default atual para o calculator. A suíte Alpha autorizará somente `reference_sut` e imports mínimos já aceitos. A mudança terá testes provando que imports desconhecidos, relativos e APIs perigosas continuam bloqueados.

### 4.4 Sequência gravada sem autoridade de workflow

O adapter demo evoluirá para aceitar uma sequência limitada e imutável de cassettes de artifact e implementar `TestCorrectionPort`. Ele não decidirá quando corrigir; apenas entregará o próximo output quando a aplicação solicitar. Ausência, excesso ou schema incorreto será falha tipada e auditável.

### 4.5 Serviço de execução Alpha

Um application service comporá componentes já existentes:

1. preparar request e snapshot;
2. executar análise e geração via `GenerateUnitTestService`;
3. respeitar encerramentos anteriores ao Docker;
4. executar artifact e oracle via `AlphaEvaluationCoordinator`;
5. solicitar correção somente pela matriz determinística;
6. preservar espera humana sem responder automaticamente;
7. retornar estado, classification, ação, contadores e refs de evidência.

O runner Smoke dependerá desse serviço por porta. Ele não duplicará regras de avaliação.

### 4.6 Comparação e reprodutibilidade

Cada execução produzirá `SmokeCaseResult`. A comparação será feita sobre fatos estáveis. O fingerprint semântico incluirá:

- case ID e versões;
- status, classificação e ação terminal;
- contadores de chamadas, retries, correções e tentativas;
- hashes de artifact e oracle quando presentes;
- flags de execução/checkpoint e resultado da comparação.

Run ID, timestamps, paths absolutos, duração, stdout bruto e identidade local da imagem não participarão do fingerprint. Eles continuam registrados como evidência operacional.

Na CI, a suíte será executada duas vezes. Os dez casos devem corresponder às expectativas nas duas execuções, e o fingerprint semântico de cada caso deve permanecer igual.

## 5. Matriz executável

| Caso | Fixture/SUT | Caminho esperado | Terminal esperado | Ação | Invariantes principais |
|---|---|---|---|---|---|
| SMK-001 | referência/soma | geração + teste + oracle | `SUCCEEDED` / `ACCEPTED` | `ACCEPT` | sem correção; Docker e oracle executados |
| SMK-002 | referência/divisão | geração + teste de zero + oracle | `SUCCEEDED` / `ACCEPTED` | `ACCEPT` | `ValueError` coberto; sem correção |
| SMK-003 | referência/texto | geração + partições + oracle | `SUCCEEDED` / `ACCEPTED` | `ACCEPT` | vazio e whitespace cobertos |
| SMK-004 | requisito ambíguo | análise solicita clarificação | `WAITING_FOR_CLARIFICATION` / `WAITING_HUMAN` | `NOT_REACHED` | uma model call; sem artifact/Docker/oracle |
| SMK-005 | requisito contraditório | análise interrompe por clarificação | `WAITING_FOR_CLARIFICATION` / `WAITING_HUMAN` | `NOT_REACHED` | contradição não é resolvida silenciosamente |
| SMK-006 | referência + artifact com erro de coleta sintaticamente válido | pytest produz `TEST_ERROR`; uma correção; nova execução | `SUCCEEDED` / `ACCEPTED` | `ACCEPT` | duas tentativas; uma correção; SUT imutável |
| SMK-007 | SUT defeituoso | teste e oracle executam; oracle revela defeito | `WAITING_FOR_HUMAN_REVIEW` / `SUT_DEFECT_SUSPECTED` | `HUMAN_REVIEW` | zero correções; checkpoint solicitado; SUT não alterado |
| SMK-008 | output gravado inválido repetido | retry central limitado e esgotado | `BUDGET_EXHAUSTED` / `BUDGET_ERROR` | `NOT_REACHED` | um retry; nenhuma execução Docker |
| SMK-009 | geração válida + falha injetada do executor | infraestrutura indisponível | `FAILED` / `INFRASTRUCTURE_ERROR` | `NOT_REACHED` | fault injection declarada; suite continua |
| SMK-010 | artifact usa operação proibida | static policy bloqueia | `POLICY_BLOCKED` / `POLICY_VIOLATION` | `NOT_REACHED` | nenhum Docker; artifact rejeitado preservado |

O SMK-006 será renomeado no catálogo para “erro de coleta/execução sintaticamente válido”. A policy de sintaxe não será relaxada.

## 6. Contratos e artifacts

### `SmokeDemoSpec 1.0.0`

- rejeita campos desconhecidos, IDs/versões divergentes, mais de duas correções, paths absolutos/traversal, executor incompatível e expectations inválidas;
- referencia apenas arquivos dentro do workspace;
- exige `allowed_modes` contendo `demo` no `DatasetCase` correspondente;
- nunca permite oracle em cassettes ou inputs de geração.

### `SmokeCaseResult 1.0.0`

- expected e actual separados;
- `MATCHED`, `MISMATCH` ou `RUNNER_ERROR`;
- run ID e diretório relativo;
- status, classificação, ação e usage;
- artifact/oracle hashes e evidence refs;
- fingerprint semântico;
- mensagem limitada, sem traceback ou path absoluto no report público.

### `SmokeSuiteReport 1.0.0`

- suite ID, versão ASEF e hash do dataset efetivo;
- modo `demo`, número de repetições e ambiente declarado;
- total, matched, mismatched e runner errors;
- resultados por caso/repetição;
- fingerprints comparados;
- limitações: dataset curado, público, pequeno e não estatístico;
- refs para `suite.json`, `suite.md` e runs individuais.

Artifacts serão gravados atomicamente sob `.asef/smoke/<suite-id>/`. Uma execução existente nunca será sobrescrita.

## 7. Carregamento e segurança

Antes de criar runs, o loader deve:

1. encontrar exatamente `SMK-001` a `SMK-010`, sem ausências, extras ou duplicatas;
2. validar todos os `case.json` e `demo.json`;
3. confirmar correspondência entre diretório, case ID e versões;
4. resolver refs dentro do workspace e rejeitar traversal/symlink escape;
5. limitar tamanho de JSON, requisitos, cassettes e total carregado;
6. confirmar existência de SUT, requisito, cassettes e oracle aplicável;
7. provar que generation/evaluation inputs continuam disjuntos;
8. calcular hash canônico do dataset efetivo.

Falha nessa fase encerra a suíte sem model call, Docker ou run parcial. Depois da validação global, mismatch ou erro isolado de um caso é registrado e os demais casos continuam. Falha de integridade do próprio store encerra a suíte.

## 8. CLI e exit codes

Comando proposto:

```powershell
asef smoke `
  --dataset-root datasets/smoke `
  --context examples/context/python-alpha-smoke-context.json `
  --output .asef/smoke `
  --repeat 1
```

Regras:

- apenas `--mode demo` no 5.5; live é rejeitado;
- `--repeat` entre 1 e 3; CI usa 2;
- output deve permanecer sob `.asef`;
- stdout contém somente resumo JSON machine-readable;
- exit `0`: todos os casos/repetições correspondem;
- exit `2`: dataset/context/argumento inválido antes da execução;
- exit `4`: ao menos um mismatch esperado/actual;
- exit `7`: runner/store/infra da suíte falhou de forma que impede evidência confiável.

Classificações negativas esperadas dentro de um caso não determinam o exit code da suíte.

## 9. Estratégia de testes

### Core/offline

- contratos aceitam os dez specs válidos;
- falta, extra, duplicata, unknown field, versão divergente e traversal falham antes de side effects;
- oracle nunca aparece nos inputs/cassettes de geração;
- expectations aceitam somente enums e contadores coerentes;
- adapter gravado consome sequência somente quando solicitado e respeita limite;
- runner compara resultados negativos como matches válidos;
- mismatch não interrompe casos posteriores;
- fingerprint ignora campos não determinísticos e muda com fatos relevantes;
- reports JSON/Markdown reconciliam totais e refs;
- CLI respeita paths, repeat e exit codes;
- execução demo não lê `OPENAI_API_KEY` nem cria gateway live.

### Integração Docker

- SMK-001, 002 e 003 passam com generated/oracle separados;
- SMK-006 falha na coleta, corrige uma vez e passa;
- SMK-007 usa SUT defeituoso, pausa e não corrige o SUT;
- workspaces são read-only e removidos;
- hashes do fixture manifest permanecem iguais antes/depois;
- SMK-009 usa injeção declarada, sem depender de parar o Docker host;
- suite completa termina 10/10.

### Regressão

- core mantém branch coverage mínima de 85%;
- jobs existentes permanecem verdes;
- demo `asef run` continua keyless;
- smoke live não é executado automaticamente;
- secret scan cobre source, cassettes, reports agregados e package.

## 10. CI e evidência

Adicionar job `alpha-smoke`:

1. instalar o package e dependências de teste;
2. construir a imagem pytest pinada;
3. remover `OPENAI_API_KEY` do ambiente;
4. executar `asef smoke ... --repeat 2`;
5. validar `suite.json` contra o contrato;
6. confirmar 20 matches, zero mismatch e zero runner error;
7. executar secret scan no output;
8. publicar somente reports sanitizados como artifact de CI com retenção curta.

O job não grava cassettes, não chama provider e não aprova o Gate 5 automaticamente.

## 11. Fatias de implementação

1. **5.5.1 — Contratos e loader:** `SmokeDemoSpec`, resultados, suite report, validação global e testes adversariais.
2. **5.5.2 — Fixtures:** materializar casos 004–006 e 008–010; completar cassettes/specs dos seeds; criar contexto Alpha e atualizar catálogo.
3. **5.5.3 — Composição Alpha:** policy de imports, sequência de correção gravada e serviço end-to-end sobre o coordenador 5.3.
4. **5.5.4 — Runner e reports:** execução ordenada, comparison, fingerprints e persistência atômica.
5. **5.5.5 — CLI e CI:** `asef smoke`, exit codes, job `alpha-smoke` e duas repetições.
6. **5.5.6 — Revisão:** regressão completa, Docker 10/10, instalação limpa, secret scan, documentação e parecer de publicação.

Cada fatia deve terminar com testes próprios. Não acumular os dez casos antes de provar o runner com um caminho feliz, um humano e um negativo esperado.

## 12. Critérios de aceite

O incremento somente pode ser aprovado quando:

1. exatamente dez casos versionados são carregados e executados em ordem;
2. todos os contratos e refs são validados antes do primeiro side effect;
3. a suíte demo roda sem chave e sem rede de provider;
4. duas repetições na CI produzem 20/20 matches e fingerprints semânticos estáveis;
5. SMK-006 prova uma correção real após `TEST_ERROR`, sem relaxar syntax policy;
6. SMK-007 pausa para humano e nunca modifica o SUT;
7. SMK-008 prova retry limitado sem Docker;
8. SMK-009 prova infraestrutura por fault injection explícita;
9. SMK-010 prova policy block antes do Docker;
10. relatório JSON reconcilia totais e Markdown aponta para evidências;
11. fixture manifest prova SUTs imutáveis;
12. secret scan e todas as regressões passam;
13. CI pública `alpha-smoke` fica verde;
14. README e catálogo dizem explicitamente que Smoke não é benchmark;
15. Lucas revisa o parecer e aprova a conclusão/publicação.

Atender G5-02 e G5-10 não aprova o Gate 5: critérios ligados a 5.6–5.9 continuam abertos.

## 13. Critérios de parada

Interromper e revisar o desenho se:

- qualquer oracle entrar em contexto/cassette de geração;
- o runner duplicar a matriz de decisão do 5.3;
- uma fixture puder comandar transições ou retries;
- o SUT original for alterado;
- um caso negativo precisar enfraquecer policy de segurança;
- demo depender de rede, chave ou custo;
- resultados esperados forem tratados como fatos observados;
- report omitir mismatch, runner error ou evidência;
- reprodutibilidade exigir esconder variabilidade relevante;
- o trabalho expandir para coverage, mutation, Security Dataset ou benchmark.

## 14. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Fixtures passam porque repetem a mesma interpretação | oracle curado isolado, casos negativos e expectations independentes do provider |
| Cassettes assumem autoridade do fluxo | sequência passiva; application service decide quando consumir |
| Casos esperadamente negativos parecem falha da suíte | comparação expected/actual separada da classificação da run |
| Report não é reproduzível por IDs/tempo | fingerprint semântico exclui campos operacionais variáveis |
| Suite fica lenta ou frágil | dez casos fixos, execução sequencial, budgets por caso e repeat máximo 3 |
| Docker indisponível quebra prova determinística | caso 009 injetado; job real ainda exige Docker para os demais casos |
| Dataset público é apresentado como benchmark | limitações obrigatórias em contrato, report, README e catálogo |
| Contexto Alpha expõe oracle | roots/read scopes concretos e teste de payload/refs |

## 15. Evidência esperada ao final

- dez diretórios `SMK-*` completos;
- contexto Alpha versionado;
- contratos e schemas do runner;
- cassettes demo sanitizados;
- suite report JSON/Markdown de 10/10;
- comparação de duas repetições;
- logs da CI e artifact sanitizado;
- hashes dos SUTs antes/depois;
- métricas de duração por caso e total;
- journal de implementação, findings e retrabalho;
- revisão final do incremento 5.5.

## 16. Evidência local de fechamento

Em 2026-07-15, as seis fatias foram implementadas. A suíte pública executou duas repetições completas no Docker real sem `OPENAI_API_KEY`: 20 resultados, 20 matches, zero mismatch e zero runner error. O hash efetivo, incluindo casos, demo specs, requisitos, cassettes, oracles, contexto e todos os arquivos autorizados pelo `read_scope`, foi `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`.

A revisão local também aprovou 221 testes descobertos, 197 executados e 24 opcionais ignorados, branch coverage global de 85%, 15 integrações Docker descobertas com 14 aprovadas e um skip conhecido de symlink no Windows, instalação isolada do wheel com Smoke 10/10, secret scan do source/wheel/evidências e `git diff --check`.

O primeiro ensaio Docker encontrou paths temporários longos demais no Windows ao persistir evidências. Os nomes internos foram encurtados sem alterar IDs ou paths finais, a regressão atômica permaneceu verde e as execuções seguintes terminaram 10/10 e 20/20. A aprovação final da fatia depende agora do novo job público `alpha-smoke`.
