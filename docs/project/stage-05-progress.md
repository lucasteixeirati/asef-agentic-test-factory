# Progresso da Etapa 5 — Alpha Python

- **Plano:** `docs/project/stage-05-alpha-python-plan.md`
- **Gate:** `docs/project/gates/gate-05-acceptance-plan.md`
- **Estado atual:** Etapa 5 concluída; Gate 5 aprovado com condições por Lucas em 2026-07-18

## 5.1 — Contratos, ADRs e suíte de referência

### Entregas

- contratos neutros `DatasetCase`, `CoverageResult` e `MutationResult`;
- perfil Python com nível atual, alvo, markers, capabilities e limitações;
- quatro casos seed: SMK-001, SMK-002, SMK-003 e SMK-007;
- SUT correto e variante com defeito semeado;
- oracles curados fora dos inputs de geração;
- manifest SHA-256 das fontes dos SUTs;
- ADR-009 proposta;
- dez testes novos de contrato, fixtures, métricas e imports.

### Decisões de implementação

- `case.json` evita adicionar YAML ao core;
- o perfil publica capabilities planejadas sem alegá-las como disponíveis;
- os oracles são públicos, porém isolados do contexto do gerador;
- coverage e mutation possuem schemas agora e adapters somente em 5.6;
- a variante defeituosa permanece read-only e não representa código de produção.

### Evidência local inicial

- targeted 5.1: 10/10;
- core completo: 132 descobertos, 113 aprovados e 19 opt-in/desabilitados;
- branch coverage geral: 88%, acima do gate de 85%;
- frameworks/workflow opcional: 18/18;
- Docker/security: 11/11;
- nenhuma regressão detectada.

### Finding de execução

A primeira tentativa de rodar paths individuais com `python -m unittest -v tests\\...` não executou testes porque `tests` não é package. O harness foi corrigido para discovery, o comando canônico do projeto. A falha não foi contabilizada como falha do produto.

### Decisão humana

Lucas aprovou explicitamente a ADR-009 em 2026-07-13. Com contratos, fixtures e regressões locais aprovados, o 5.1 está concluído. A publicação e a CI final fazem parte da evidência de entrega; o próximo incremento autorizado é 5.2 — adapter `pytest` e normalização.

### Publicação e CI

- commit publicado: `3352dc4` (`feat: establish stage 5 alpha contracts and reference suite`);
- GitHub Actions: run `29276529459`;
- `core`: aprovado, incluindo branch coverage e secret scan;
- `docker-security`: aprovado, incluindo instalação pública e demo keyless fora do checkout;
- `framework-spikes`: aprovado, incluindo coverage do workflow opcional.

Com os três jobs aprovados, a condição de publicação do 5.1 está atendida.

## 5.2 — Adapter pytest e normalização

### Entregas implementadas

- `PytestDockerAdapter` fora do core;
- JUnit XML nativo, sem plugin adicional;
- `TestExecutionOutcome` neutro;
- `NormalizedExecutionResult 1.1.0` com ferramenta, versão, errors, skipped e raw result;
- distinção factual entre pass, assertion failure, test error, no tests, tool error e infraestrutura;
- resultado bruto persistível como evidência;
- imagem derivada com base por digest, versões e hashes de wheels pinados;
- image tag resolvido para image ID imutável antes da execução;
- output mount separado sem abrir escrita no workspace;
- build da imagem incluído no job Docker da CI.

### Evidência local

- testes unitários do adapter/parser: 7/7;
- integração pytest em Docker: 3/3;
- Docker/security completo: 14/14;
- core: 147 descobertos, 125 aprovados e 22 opt-in;
- branch coverage geral: 88%;
- branch coverage do adapter pytest: 93%;
- SUT preservou o hash durante tentativa de escrita.

### Fricções e correções

- o primeiro teste inválido de reconciliação acionava uma regra anterior antes da nova; os dados foram corrigidos para isolar a propriedade testada;
- exposição pública e isolamento do oracle já haviam sido separados no 5.1; no 5.2 a mesma disciplina separou workspace e output gravável;
- versões pinadas sem hashes foram consideradas insuficientes e o build passou a exigir SHA-256 dos wheels;
- uma imagem local por tag seria evidência mutável; o adapter agora resolve e executa pelo image ID.

### Limitações preservadas

- a imagem pytest ainda não é publicada em registry;
- a CLI pública continua usando o runner do skeleton;
- assertion failure continua `TEST_FAILURE` até a avaliação combinada do 5.3;
- suítes geradas com testes ignorados não são aceitas silenciosamente;
- o perfil Python permanece experimental/parcial.

### Decisão humana e próximo passo

Lucas aprovou explicitamente o incremento 5.2 em 2026-07-13. A publicação e os três jobs verdes da CI pública encerraram o incremento e autorizaram o planejamento detalhado do 5.3 — oracle e loop de correção.

### Publicação e CI

- commit publicado: `7d549a8` (`feat: add pytest docker adapter and structured results`);
- GitHub Actions: run `29287409883`;
- `core`: aprovado, incluindo 147 testes descobertos, branch coverage e secret scan;
- `docker-security`: aprovado, incluindo build pinado da imagem pytest, 14 integrações Docker, instalação pública e demo keyless fora do checkout;
- `framework-spikes`: aprovado, incluindo frameworks opcionais e coverage do workflow humano.

Com os três jobs aprovados, o incremento 5.2 está concluído. O próximo passo autorizado é planejar detalhadamente o 5.3; sua implementação dependerá de aprovação específica.

## 5.3 — Oracle e correção limitada

### Estado de desenvolvimento

A implementação interna foi autorizada e concluída em fatias em 2026-07-14. A primeira revisão rejeitou provisoriamente o incremento por sete findings. Todos foram corrigidos; a segunda revisão técnica, o empacotamento e a CI pública foram aprovados. O incremento foi publicado como pré-alpha `0.1.0a2`, mas ainda não está conectado à CLI pública.

Entregas presentes:

- matriz determinística entre teste gerado e oracle independente;
- classificação `SUT_DEFECT_SUSPECTED` somente com evidência do oracle;
- workspaces separados para geração, tentativas e oracle;
- evidências imutáveis por tentativa e papel;
- no máximo duas correções, com budgets públicos;
- feedback sanitizado, truncado e identificado por fingerprint;
- parada antecipada para diagnóstico repetido;
- checkpoint e revisão humana idempotente;
- coordenador interno que aceita, corrige, pausa ou encerra sem delegar transições ao modelo.

Evidência local após correções da revisão:

- 178 testes descobertos, 155 aprovados e 23 opt-in no core sem Docker;
- branch coverage de 88%, acima do gate de 85%;
- frameworks e workflow opcional: 18/18;
- Docker: 15 descobertos, 14 aprovados e um skip local por privilégio de symlink no Windows;
- integração Docker específica do 5.3 aprovada com teste e oracle em workspaces read-only distintos;
- artifacts corrigidos, identidade do oracle e avaliações preservados antes do cleanup;
- schema de estado `1.2.0`, com leitura comprovada de estado `1.1.0` sem os novos campos;
- falhas de provider e infraestrutura normalizadas com budgets persistidos.

### Publicação e CI

- commit funcional publicado: `1cf687f` (`feat: complete stage 5.3 oracle correction workflow`);
- versão do pacote: `0.1.0a2`;
- execução pública: `29360824309`;
- jobs `core`, `framework-spikes` e `docker-security`: aprovados;
- wheel e sdist construídos, inspecionados e aprovados pelo secret scan;
- instalação limpa do wheel e execução da demo keyless: `SUCCEEDED/ACCEPTED`.

Com a revisão, o empacotamento e os três jobs aprovados, o incremento 5.3 está concluído. A exposição desse fluxo na CLI permanece uma decisão futura e não faz parte desta publicação.

## 5.4 — Adapter live e budgets

O incremento foi autorizado por Lucas em 2026-07-14. O plano executável está em `docs/project/stage-05-increment-54-plan.md`. A implementação promove o gateway live experimental para as portas públicas de análise, geração e correção, sem alterar a autoridade do runtime nem tornar rede ou chave obrigatórias no modo demo.

### Evidência de desenvolvimento

- `AgenticTestPort` e `TestCorrectionPort` implementados pelo adapter live;
- Responses API com Structured Outputs estrito, `store: false` e transporte substituível;
- source limitado aos arquivos concretos do `read_scope`, com teto de 64 KiB e bloqueio sensível;
- chamadas reservadas e persistidas antes do transporte;
- tokens, latência e custo estimado preservados também para recusa, output inválido e falha de cassette;
- provider retry separado do contador de correção;
- CLI `generate`/`run` seleciona live somente por contexto, modelo, budget e tarifas explícitos;
- cassette opt-in sem prompt integral, headers ou chave;
- estado persistido evoluído para `1.3.0`, com leitura de `1.2.0` sem custo live;
- core: 199 descobertos, 183 aprovados e 16 opt-in; branch coverage de 87%;
- frameworks/workflow opcional: 18/18;
- Docker: 15 descobertos, 14 aprovados e um skip conhecido de symlink no Windows;
- secret scan e `git diff --check`: aprovados.

### Aceite local

O smoke live manual foi explicitamente autorizado e aprovado em 2026-07-14 com uma única chamada. O provider retornou `gpt-5.4-2026-03-05`: 194 tokens de entrada, 138 de saída, latência de 4.515 ms e custo estimado de R$ 0,01533, dentro do teto de R$ 0,10. Nenhuma repetição foi necessária.

Na revisão de fechamento, valores monetários não finitos (`NaN`/`Infinity`) foram identificados como bypass possível das comparações de budget. Contratos, gateway e configuração live passaram a rejeitá-los antes do transporte, com regressões dedicadas. Com o finding encerrado, regressão, coverage, integrações, secret scan e integridade do diff aprovados, o incremento compõe a candidata pré-alpha `0.1.0a3`.

Wheel e sdist `0.1.0a3` foram construídos em ambiente isolado e passaram no secret scan. O wheel foi instalado sem dependências em venv novo; a demo keyless fora do checkout terminou `SUCCEEDED`/`ACCEPTED`. Os hashes e o parecer estão em `docs/reviews/2026-07-14-revisao-final-incremento-54.md`.

### Publicação e CI

- commit funcional publicado: `1d41383` (`feat: add live provider budgets and release candidate`);
- execução pública: `29415101383`;
- jobs `core`, `framework-spikes` e `docker-security`: aprovados;
- instalação do package e demo keyless fora do checkout: aprovadas na CI;
- publicação recomendada como pré-alpha `v0.1.0a3`;
- commit de fechamento: `f64f85d` (`docs: approve stage 5.4 release after ci`);
- CI de fechamento: `29415300777`, aprovada;
- tag anotada e pré-release `v0.1.0a3` publicadas em 2026-07-15.

## 5.5 — Smoke Dataset executável

O planejamento detalhado foi produzido e aprovado em 2026-07-15 e está em `docs/project/stage-05-increment-55-plan.md`. A implementação começou pela fatia 5.5.1, dedicada aos contratos tipados, loader global e testes adversariais. O plano mantém o dataset demo offline/keyless, materializa exatamente dez casos, conecta o coordenador Alpha do 5.3 e separa resultados esperadamente negativos de falhas da própria suíte.

Na abertura da 5.5.1 foram introduzidos os contratos `SmokeDemoSpec`, `SmokeCaseResult` e `SmokeSuiteReport`, expectativas exatas ou intervalares de uso, fingerprint semântico e validações de coerência. O loader foi desenhado para aceitar somente `SMK-001` a `SMK-010`, validar todos os pares `case.json`/`demo.json`, limitar bytes, impedir escapes e vazamento do oracle e calcular o hash efetivo do dataset antes de qualquer run.

As seis fatias foram implementadas: os dez casos e cassettes estão materializados; o contexto Alpha separa SUT de referência e defeituoso; a allowlist da skill é composta; correções gravadas são consumidas somente quando o coordenador solicita; e o runner produz comparação, fingerprints estáveis e reports JSON/Markdown atômicos. O comando `asef smoke` e o job `alpha-smoke` completam a superfície pública.

Na revisão local, uma primeira execução encontrou excesso de comprimento nos nomes temporários aninhados da evidência no Windows. O ajuste encurtou apenas nomes internos, preservando paths finais e atomicidade. Em seguida, o Smoke passou 10/10 e 20/20 no Docker real, sem chave, com hash efetivo `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`. A regressão descobriu 221 testes, executou 197 e ignorou 24 opcionais; coverage permaneceu em 85%. As integrações Docker ficaram 14 aprovadas de 15, com o skip conhecido de symlink no Windows. O wheel instalado isoladamente também executou Smoke 10/10. Source, wheel e evidências passaram no secret scan.

O commit funcional `06cc892` foi publicado em `main`. A CI `29442732993` aprovou os quatro jobs: `core`, `framework-spikes`, `docker-security` e o novo `alpha-smoke`. Este último confirmou 20/20 em duas repetições keyless, validou o report, passou no secret scan e publicou os reports sanitizados. O incremento 5.5 está concluído; o próximo passo depende de aprovação explícita para planejar o 5.6.

A revisão da baseline corrigiu o desenho do SMK-006: sintaxe inválida continua bloqueada antes do Docker; o caso usa erro de coleta sintaticamente válido, alcança `TEST_ERROR`, consome exatamente uma correção e termina aceito.

## 5.6 — Coverage e mutation do SUT

O planejamento detalhado foi produzido e aprovado em 2026-07-15 e está em `docs/project/stage-05-increment-56-plan.md`. A implementação local das seis fatias foi concluída; publicação e confirmação da CI permanecem pendentes.

O plano separa qualidade da aceitação funcional, propõe uma imagem Docker própria para coverage/mutation e mantém o SUT original read-only. Coverage usará JSON nativo com linhas e branches separados. A primeira fatia deverá caracterizar mutmut `3.6.0`, seus estados e uma forma honesta de limitar mutantes antes de consolidar o adapter.

G5-12 e G5-13 estão atendidos localmente e aguardam a prova do novo job público. As capabilities `coverage` e `mutation` foram promovidas para `available` somente depois das provas de conformance e integração no SUT de referência.

### Fatia 5.6.1 — caracterização e contratos

Lucas aprovou o plano em 2026-07-15. A versão pinada do mutmut foi caracterizada a partir do wheel oficial: a ferramenta possui metadata JSON interna e seleção por nomes, mas não oferece `--max-mutants`. O desenho passou a usar descoberta, admissão canônica e execução somente do subconjunto admitido, sempre sob hard timeout do host.

Foram implementados `QualityCapabilityRequest`, `QualityCapabilityObservation`, `QualityEvaluationReport`, estados explícitos de disponibilidade/parcialidade e `MutationAdmission`. `MutationResult` agora diferencia total descoberto de total processado: o budget limita os processados e `not_run` preserva os deferidos.

A caracterização está em `docs/quality/mutmut-3.6.0-characterization.md`. A imagem pinada e os adapters confirmaram no container Linux que a descoberta pode ser separada da execução e que somente os mutantes admitidos pelo budget são enviados ao comando público.

### Fatias 5.6.2 a 5.6.6 — imagem, adapters, orquestração e CI

Foi criada a imagem separada `asef/python-quality:coverage-7.10.7-mutmut-3.6.0`, baseada no mesmo digest Python do perfil e com dependências transitivas fixadas por hashes. O driver executa coverage com branch mode e JSON nativo. Para mutation, copia o workspace read-only para `/tmp`, substitui a configuração do SUT por uma configuração controlada, descobre metadata da versão pinada, admite nomes canônicos e chama `mutmut run` apenas para o subconjunto admitido.

A fixture de conformance congelou coverage em 7/8 linhas e 1/2 branches. Mutation descobriu cinco mutantes, admitiu três e deferiu dois; entre os admitidos houve um morto e dois sobreviventes. O adapter resolve a tag para image ID, mantém rede bloqueada, root filesystem e fonte read-only, output gravável separado, limites de CPU/memória/PIDs e hard timeout com remoção do container.

O serviço `QualityEvaluationService` só enriquece runs funcionalmente `SUCCEEDED/ACCEPTED`. Outputs nativos, driver, stdout/stderr, resultados normalizados e observations são persistidos atomicamente por `EvidenceRef`; indisponibilidade, falha, output inválido e budget esgotado não fabricam métricas nem alteram a classificação funcional. Reports JSON/Markdown receberam uma seção irmã `quality` sem threshold universal.

Na baseline real do SUT de referência, coverage observou 11/11 linhas e 2/2 branches. Mutation descobriu nove mutantes, admitiu oito, matou cinco, deixou três sobreviventes e registrou um deferido, com score informativo de 62,5%. A duração local observada foi cerca de 6,4 segundos, variável por ambiente. Os hashes dos fontes permaneceram idênticos.

A regressão local descobriu 253 testes, executou 226 e ignorou 27 integrações opcionais, alcançando branch coverage de 86%. A matriz Docker aprovou 17 de 18 testes; o único skip é a limitação já conhecida de privilégio para criar symlink no Windows. O Smoke Dataset permaneceu 20/20 com o hash estável `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`. O workflow ganhou o job `quality-capabilities`, que constrói a imagem, executa conformance/baseline, testa falha/timeout, faz secret scan e publica evidências sanitizadas por sete dias.

Durante a revisão foram corrigidos cinco findings: serialização aninhada perdia percentuais derivados; o store misturava paths absolutos e relativos no Windows; uma falha de normalização poderia descartar o output nativo; stdout/stderr precisavam de sanitização explícita; e o report Alpha precisava ser reemitido após o enriquecimento. A composição da CI também recebeu opt-in separado para a imagem de quality, preservando o job Docker histórico. O incremento compõe a candidata `0.1.0a4`, pronta para commit e validação pública; ainda não está publicado.

Wheel e sdist `0.1.0a4` foram construídos em ambiente isolado, inspecionados e aprovados pelo secret scan. O wheel foi instalado sem dependências em venv novo, identificado como `0.1.0a4`, e a demo keyless fora do checkout terminou `SUCCEEDED`/`ACCEPTED`. Hashes, findings e parecer estão em `docs/reviews/2026-07-15-revisao-final-incremento-56.md`.

O commit funcional `654cd6d` (`feat: add bounded Python quality capabilities`) foi publicado em `main`. A CI `29461154744` aprovou os cinco jobs: `core`, `framework-spikes`, `docker-security`, `alpha-smoke` e o novo `quality-capabilities`. Este último construiu a imagem pinada, aprovou conformance e baseline, executou os cenários de falha/timeout, passou no secret scan e publicou evidências sanitizadas. A candidata está aprovada tecnicamente; resta o commit documental de fechamento e sua CI antes da tag/pré-release.

O commit documental `f55be73` (`docs: approve stage 5.6 candidate after ci`) também foi publicado e a CI de fechamento `29461247717` aprovou novamente os cinco jobs. A tag anotada e a pré-release [`v0.1.0a4`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a4), com wheel e sdist auditados, foram publicadas em 2026-07-15. O incremento 5.6 está concluído; naquele fechamento, o 5.7 ainda dependia de novo planejamento e aprovação explícita.

## 5.7 — Segurança, diagnóstico e retenção

O planejamento detalhado foi produzido em 2026-07-15 e está em `docs/project/stage-05-increment-57-plan.md`. Lucas aprovou explicitamente o plano em 2026-07-16 e autorizou em sequência todas as seis fatias, mantendo publicação, Gate 5 e Etapa 6 como decisões separadas.

A auditoria de abertura encontrou nove vetores Docker já cobertos, três controles preventivos na skill/contratos, rotação local de logs e retenção de sete dias para evidências públicas da CI. Permanecem sem prova integrada os doze casos `SEC-001` a `SEC-012`, o diagnóstico público do ambiente, a limpeza observável após interrupções e uma política explícita para retenção, debug e descarte local.

O desenho propõe contratos neutros, casos versionados com executores internos, comando offline `asef security`, hardening do ciclo de vida dos containers, `asef doctor` estritamente diagnóstico e `asef cleanup` em dry-run por padrão. Evidências finais locais não serão apagadas automaticamente; limpeza mutável exigirá `--apply`, contenção por path, identidade verificável e tombstone. O caso `SEC-004` não poderá contar como aprovado quando a primitiva real de symlink/junction não for demonstrável no ambiente.

A entrega foi dividida em seis fatias: contratos e threat model; dataset e runner; hardening Docker; doctor; retenção/cleanup/debug; e CI/revisão. O novo job `alpha-security` deverá provar 12/12, diagnóstico sanitizado, ausência de órfãos e secret scan. G5-11, G5-15 e G5-16 permanecem abertos até as evidências executáveis; o Gate 5 e a Etapa 6 não avançam automaticamente.

### Fatia 5.7.1 — threat model, contratos e política

A primeira fatia introduziu contratos públicos e neutros para `SecurityCaseSpec`, `SecurityCaseResult`, `SecuritySuiteReport`, checks/reports do doctor, política de retenção, requests/tombstones de cleanup e caracterização de segurança do filesystem. A matriz `SEC-001` a `SEC-012` associa cada ID a um executor interno e outcome fechado; manifests não podem definir shell, argv, imagem ou mount.

`UNSUPPORTED` é distinto de pass e impede aceite 12/12. Checks do doctor usam códigos estáveis, facts limitados e recomendações pertencentes a uma enumeração revisada. A política default mantém efêmeros com remoção imediata, evidência final e tombstones sob cleanup explícito, logs com rotação de 1 MiB e dois backups, reports de CI por sete dias e debug somente sanitizado. Cleanup nasce em `DRY_RUN`, com raiz fixa `.asef`; nenhum executor de deleção foi implementado nesta fatia.

A caracterização local em Windows 11, Python 3.13.5, confirmou `Path.is_junction()`, mas `shutil.rmtree.avoids_symlink_attacks` é falso e remoção por `dir_fd` não está disponível. O contrato, portanto, publica `RECURSIVE_APPLY_DRY_RUN_ONLY` e proíbe alegar suporte a apply recursivo seguro nesse perfil. A inspeção pura rejeita root, target externo, arquivo, symlink e junction antes de qualquer remoção.

A fatia adicionou 25 testes direcionados. A regressão final descobriu 278 testes, executou 249 e ignorou 29 integrações opcionais; todos os executados passaram. Branch coverage geral ficou em 86,90% e `security_contracts.py` em 94,78%. Os dois skips novos são fixtures de symlink sem privilégio no Windows e permanecem evidência ausente, não pass. `git diff --check`, compilação dos módulos e secret scan foram aprovados. Nenhuma entrega da 5.7.2 foi iniciada.

Na revisão técnica foram encontrados quatro findings: status agregado/duração/timeout ausentes no doctor; fingerprints e plan hash não reconciliados; arrays JSON que podiam ser interpretados a partir de strings; e raiz de cleanup em link/junction sem rejeição explícita. Todos foram corrigidos. Facts do doctor passaram a ser allowlisted por check e retenção passou a congelar exatamente logs, cassettes, reports CI e debug. Uma prova real de junction no Windows retornou `JUNCTION` e preservou o target controlado.

Com os findings encerrados e a validação final verde, a 5.7.1 está aprovada localmente. O próximo passo depende de decisão explícita sobre a 5.7.2.

### Fatia 5.7.2 — Security Dataset e runner

Lucas autorizou explicitamente a segunda fatia. Foram materializados `SEC-001` a `SEC-012`, cada um com manifest, README e fixture pública. O loader exige exatamente os doze IDs, fileset conhecido, JSON sem chaves duplicadas, UTF-8, limites de bytes, referências canônicas e ausência de symlink/junction.

Os manifests selecionam somente executores enumerados. Comandos Docker, imagem, mounts e budgets permanecem compilados no package. O runner continua após control failure, distingue `FAILED`, `ERROR` e `UNSUPPORTED`, persiste facts/resultados JSON e report Markdown e expõe `asef security` com exits 0/2/4/7.

A primeira execução real terminou 11/12 porque o argv interno de criação da junction estava incorreto; o caso ficou `UNSUPPORTED` e não foi convertido em pass. Após correção e prova isolada, a execução `security-20260716T115701Z-322d5aef` terminou 12/12, zero failure/error/unsupported, hash `e386538869acc970a86d935b7068c794e5522b884caf327a953b3b4434b1818b`. Nenhum container `asef-*` permaneceu.

A regressão final descobriu 287 testes, executou 258 e ignorou 29 opcionais; todos os executados passaram. Branch coverage geral ficou em 85,78%. Source e evidência 12/12 passaram no secret scan e `git diff --check` permaneceu verde. Labels, interrupção e orphan detection continuam reservados à 5.7.3.

A revisão técnica corrigiu o argv de junction, uma dependência indevida application→adapter, validação UTF-8 do dataset, a exigência factual de preservação do target e a continuidade após control failure. A 5.7.2 está aprovada localmente; o início da 5.7.3 depende de nova decisão.

### Fatia 5.7.3 — hardening do lifecycle Docker

Lucas autorizou explicitamente a terceira fatia. O `DockerRunner` passou a rotular cada execução com ownership, capability e identidade (`com.asef.managed`, `com.asef.capability` e `com.asef.execution`). O socket Docker continua ausente dos mounts e SEC-011 agora concilia essa ausência com os labels compilados no package.

Timeout, `KeyboardInterrupt` e falhas inesperadas do executor solicitam remoção forçada pelo nome aleatório da execução e verificam a ausência do container. Em encerramento normal, a ausência também é inspecionada e eventual residual recebe uma segunda tentativa de remoção. O resultado funcional e a observação de cleanup permanecem separados: exit zero não oculta `CONTAINER_RESIDUAL` ou `CONTAINER_INSPECTION_FAILED`.

A orphan detection usa exclusivamente os dois labels de ownership/capability, sem prefix matching amplo. Cada caso Docker do Security Dataset exige cleanup bem-sucedido e confirma zero IDs gerenciados restantes antes de ser aceito. A execução real `security-20260716T132831Z-b165d7fe` terminou 12/12, sem failure/error/unsupported, com o hash estável `e386538869acc970a86d935b7068c794e5522b884caf327a953b3b4434b1818b`; a inspeção final por labels retornou vazia.

A regressão final descobriu 290 testes, executou 261 e ignorou 29 integrações opcionais; todos os executados passaram. Branch coverage ficou em 85,64%. Compilação, `git diff --check` e secret scan do source e da evidência 12/12 passaram. A 5.7.3 está aprovada localmente; a 5.7.4 (`asef doctor`) depende de nova decisão explícita.

### Fatia 5.7.4 — diagnóstico do ambiente

Lucas autorizou explicitamente a quarta fatia. Foram implementados `DoctorRequest`, runner neutro, executor substituível, store atômico JSON/Markdown e a CLI `asef doctor`. Os doze checks cobrem Python, distribuição instalada, host, output root, CLI/daemon/engine Docker, imagens pytest/quality, contexto opcional, presença booleana da chave live e containers gerenciados.

O doctor não lê Docker config, não persiste stdout/stderr bruto, não publica paths de home ou valor/comprimento da chave e não instala, inicia, corrige, faz pull/build/prune ou chama provider. Campos retornados pelo daemon passam por formatos fechados antes de virar facts. Contexto informado é obrigatório e bloqueante quando inválido; contexto ausente e chave live no modo demo são skips opcionais e produzem `DEGRADED` com exit zero.

A primeira execução real via `PYTHONPATH=src` produziu `BLOCKED` somente em `asef-package`, demonstrando que checkout não é confundido com distribuição instalada. O wheel foi então construído, instalado sem dependências em venv e diretório temporários fora do checkout e executou `asef doctor`: 10 passes, dois skips opcionais, `DEGRADED/READY` e exit zero. CLI, daemon, engine Linux, imagens, output e ausência de órfãos foram comprovados sem mutação do host.

Security permaneceu 12/12 na execução `security-20260716T145041Z-c826cba6`; Smoke permaneceu 20/20 na execução `smoke-20260716T145440Z-25eec06c`. A regressão final descobriu 300 testes, executou 271 e ignorou 29 opcionais, com branch coverage de 85,54%. Source, wheel, sdist e report instalado passaram no secret scan. A 5.7.4 está aprovada localmente; a 5.7.5 depende de nova decisão explícita.

### Fatia 5.7.5 — retention, cleanup e debug

Lucas autorizou explicitamente a quinta fatia. A policy `asef-local-retention@1.0.0` foi publicada e passou a integrar os tombstones. A CLI `asef cleanup` seleciona `runs|smoke|security|quality|doctor|logs|containers|all`, exige idade positiva, mantém root fixa `.asef`, opera em dry-run sem `--apply` e nunca usa prune ou prefix matching amplo.

Suites e doctor usam IDs temporais conciliados com JSON; runs usam `state.json`; logs usam timestamps JSONL; containers usam label, Created e ID completo. Quality sob run herda a idade da run. Targets legados/malformed são `SKIPPED`, sem fallback para `mtime`. Tree identities incluem paths, metadata, conteúdo, inode/device e bloqueiam links, junctions, mudança de filesystem, excesso de entradas e alteração entre plano/apply.

No Windows caracterizado, apply recursivo real continua recusado com `RECURSIVE_APPLY_UNSUPPORTED`. Arquivos regulares e containers possuem apply após revalidação; a remoção recursiva foi exercitada somente em fixtures temporárias com capability injetada e precisa de prova Linux na 5.7.6. Nenhum log/evidência real elegível foi apagado durante a revisão.

O dry-run real `cleanup-20260716T181517Z-1796bf2b` combinou todas as classes: um backup de log elegível, 13 targets ignorados, zero deleções/falhas e policy/hash reconciliados. O report doctor legado sem timestamp e a quality evidence sem manifest foram explicitamente `MANIFEST_INVALID`.

`ignore_errors=True` foi removido de `src`. Workspaces de geração, oracle, attempts e quality agora produzem observações comuns e falham como infraestrutura se deixarem resíduo. DEBUG continua com os mesmos campos allowlisted e não coleta prompt, environment ou resposta bruta.

O scanner passou a rejeitar links/junctions, tornar unreadable/oversize/archive inválido visíveis, limitar members/bytes, inspecionar wheel e tar.gz e detectar atribuições sensíveis em formatos de dados sem imprimir valores. Security permaneceu 12/12 em `security-20260716T181419Z-5fd57b4b`; Smoke permaneceu 20/20 em `smoke-20260716T181431Z-c1e2a470`.

A regressão final descobriu 316 testes, executou 285 e ignorou 31 opcionais, com branch coverage de 85,16%. Source, wheel, sdist, Security, Smoke, doctor e cleanup reports passaram no scanner; nenhum container ASEF permaneceu. A 5.7.5 está aprovada localmente com apply recursivo Windows deliberadamente bloqueado. A 5.7.6 depende de nova decisão explícita.

### Fatia 5.7.6 — CI, package audit e candidata

Lucas autorizou explicitamente a fatia final. O workflow recebeu o sexto job independente, `alpha-security`. Ele instala o package, constrói as imagens pytest/quality, remove `OPENAI_API_KEY`, exige Security 12/12, valida doctor instalado, prova symlink e cleanup recursivo Linux, executa cleanup dry-run/apply em raiz temporária, verifica ausência de órfãos, escaneia reports/logs e publica somente JSON/Markdown sanitizados por sete dias.

O comando Linux foi antecipado localmente dentro da imagem Python fixada por digest, com repo read-only, rede bloqueada e hard budgets. Os dois testes passaram: apply recursivo removeu somente a suite controlada e symlink foi `SKIPPED`, preservando o target externo.

O package audit instalou o wheel sem dependências em venv/diretório fora do checkout. O doctor terminou `DEGRADED/READY`; a demo terminou `SUCCEEDED/ACCEPTED`; cleanup instalado comprovou dry-run e apply de log controlado; toda a `.asef` gerada passou no scanner. A candidata foi promovida para `0.1.0a5`, preservando a release `v0.1.0a4`. Uma segunda instalação confirmou metadata `0.1.0a5`. Após o fechamento documental, os artefatos foram reconstruídos no commit marcado; wheel e sdist publicados possuem SHA-256 `6b4d191705a9ddf4a513b3e33f4df021bae477e4a77b5149e713a42b055e937c` e `783c1c8a2beb6285f3cbef5a127a8c59cd778e3ae23c682c795e6a0bb76080fc`.

A matriz Docker/quality local descobriu 20 integrações: 17 passaram e três foram ignoradas pelo host Windows; as duas provas Linux ignoradas localmente passaram no container separado. A regressão final descobriu 318 testes, executou 285 e ignorou 33 opcionais, com branch coverage de 85,16%.

A implementação das seis fatias está concluída. O checkpoint `2de3c44` acionou a CI pública `29528937211`, que aprovou `core`, `framework-spikes`, `docker-security`, `alpha-smoke`, `quality-capabilities` e `alpha-security`. O commit documental `4c8073c` passou novamente nos seis jobs na CI `29530753021`. Após aprovação explícita de Lucas, a tag anotada e a [pré-release `v0.1.0a5`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a5) foram publicadas com wheel e sdist auditados. O incremento 5.7 está encerrado; Gate 5, 5.8 e Etapa 6 permanecem decisões separadas.

## 5.8 — Relatórios e experiência pública

Lucas aprovou o planejamento detalhado e autorizou separadamente as fatias 5.8.1, 5.8.2 e 5.8.3. A baseline encontrou três lacunas principais: o report da run era composto diretamente pelo store e não possuía contrato público próprio; fatos, inferências, recomendações e limitações não eram tipos distintos; e a experiência pública permanecia concentrada no README, sem jornada dedicada de quickstart, tutorial, interpretação e troubleshooting.

O plano executável está em `docs/project/stage-05-increment-58-plan.md`. Ele propõe seis fatias: contrato/schema; builder e cobertura de terminais; jornada pública; arquitetura/contribuição; package audit e job `public-experience`; revisão/candidata. Participante externo real, retrospectiva final e Gate 5 permanecem fora do 5.8.

Contrato/schema/threat model da 5.8.1, publicação da 5.8.2, jornada pública da 5.8.3, arquitetura/contribuição da 5.8.4, experiência instalada/CI da 5.8.5 e revisão/candidata da 5.8.6 foram concluídos. O commit `9739c1e` foi enviado à `main` após aprovação explícita e passou na matriz pública de sete jobs.

### Fatia 5.8.1 — contrato, schema e threat model do report

Após a aprovação do plano, foi iniciada somente a primeira fatia. `AlphaRunReport 1.0.0` define requirement, traceability, artifacts, attempts, resultado funcional, quality, intervenções humanas, policy/budgets, usage, evidence, facts, inferences, recommendations e limitations. O parser é estrito, o JSON Schema usa Draft 2020-12 e o módulo permanece neutro em relação a tooling, provider e workflow engine.

O contrato rejeita links de rastreabilidade inventados, IDs não contíguos, references desconhecidas, status/classification incoerentes, acceptance sem pass integral, evidence publicável não verificada/sanitizada, paths externos, assinaturas sensíveis, inference sem base e recommendation fora da allowlist. Ao encerramento desta primeira fatia, builder, Markdown, store, CLI e reports reais permaneciam reservados à 5.8.2.

A revisão local aprovou 13 testes específicos e a regressão integral de 331 testes, com 33 skips opcionais e branch coverage geral de 85,10%. JSON Schema Draft 2020-12 validou uma instância real, e wheel/sdist incluem o módulo e o schema. O parecer está em `docs/reviews/2026-07-16-revisao-fatia-581.md`.

### Fatia 5.8.2 — builder, evidências, renderer, store e terminais

`BuildAlphaReportService` passou a compor deterministicamente o contrato a partir de state, snapshot, avaliação e observações tipadas de evidência, sem acessar filesystem ou presentation. `ReportEvidenceVerifier` confina refs à run, rejeita paths não canônicos, não segue links/junctions e distingue `VERIFIED`, `MISSING` e `MISMATCH`. `AlphaReportMarkdownRenderer` recebe somente contrato validado e mantém a ordem pública fixa, com escape de conteúdo não confiável.

`AlphaReportStore` valida JSON reaberto, persiste JSON/Markdown/manifest em transação recuperável e reconcilia hashes existentes antes de qualquer reemissão. `JsonRunStore` apenas delega publicação. O manifest referencia os dois reports por SHA-256; a CLI acrescenta `report_json`, `report_markdown` e `report_schema_version`, preservando `report_path`. Runs terminalizadas após persistência — inclusive policy, budget, cancel, resume e falha de infraestrutura — recebem report; esperas humanas continuam sem alegar terminal.

A regressão aprovou 337 testes, com 33 skips opcionais e branch coverage geral de 85,34%. Seis testes específicos cobrem idempotência, mismatch/missing, tamper, escape Markdown, rollback transacional e terminal anterior ao artifact. O parecer está em `docs/reviews/2026-07-16-revisao-fatia-582.md`.

### Fatia 5.8.3 — jornada pública de uso

O README passou a comunicar propósito, estado experimental, evidência comprovada/não comprovada, quickstart curto, mapa documental, suporte e roadmap sem concentrar todos os detalhes operacionais. A distinção entre a release publicada `v0.1.0a5` e o report 5.8 ainda local ficou explícita.

Foram criados quickstart instalado keyless, tutorial WF-001 demo, tutorial live opt-in, guia de interpretação do report e troubleshooting seguro. A jornada começa por doctor, usa os paths retornados pelo CLI, diferencia demo linear do oracle combinado 5.3, trata `null` como não observado, explica todos os estados de quality e não fixa modelo/preço/câmbio. Live exige secret somente no host, tarifas do operador e budget positivo; troubleshooting proíbe prune amplo, relaxamento de sandbox e execução de código gerado no host.

Links locais, paths, flags, classifications e estados documentados foram confrontados com o código. Secret scan dos seis documentos, `git diff --check` e regressão de 337 testes/33 skips com branch coverage de 85,34% foram aprovados. O parecer está em `docs/reviews/2026-07-17-revisao-fatia-583.md`.

### Fatia 5.8.4 — arquitetura, suporte e contribuição

A arquitetura real do Alpha Python passou a documentar o fluxo implementado, autoridades de core/application/adapters/tooling/datasets, jornada linear versus oracle combinado, quality opcional, checkpoint humano e publicação tipada. O documento histórico do walking skeleton agora aponta para essa autoridade vigente.

O modelo de evidências foi reconciliado com `context-snapshot.json`, state/events/manifest, `results`, artifacts, attempts, oracle, quality e reports. Estratégias de avaliação e segurança passaram a explicitar interpretação, validade, superfície publicável e integridade `VERIFIED`/`MISSING`/`MISMATCH`. Observabilidade, doctor, cleanup e live apontam para fontes canônicas.

`support-and-limitations.md` tornou-se a fonte única para host, níveis, capabilities, sandbox, live, cleanup e alcance de Smoke/Security. A matriz não promove Node/Java além da inicialização histórica; `python-pytest` permanece experimental. CONTRIBUTING ganhou setup/extras, matriz de testes, opt-ins Docker, scanner, fronteiras e governança de IA; adapter guide e código de conduta foram criados. Os templates existentes foram preservados, com apenas um check de fronteira/suporte no PR.

A revisão de 115 arquivos Markdown aprovou todos os links locais. A regressão permaneceu em 337 testes aprovados, 33 skips opcionais e branch coverage de 85,34%; secret scan documental e `git diff --check` passaram. Nenhum Docker/live, commit, push, CI, package/version ou release foi executado. O parecer está em `docs/reviews/2026-07-17-revisao-fatia-584.md`.

### Fatia 5.8.5 — experiência instalada e CI

`tools/docs_check.py` introduziu validação offline e sem crawler externo para arquivos obrigatórios, links/anchors, versão canônica, comandos do CLI, paths de exemplo, links locais absolutos, claims proibidas, placeholders e consistência README/suporte. O checker final percorreu 117 arquivos e 103 links sem findings; testes adversariais cobrem target/anchor ausente, path absoluto e placeholder.

`tools/public_experience_audit.py` valida JSON estrito e containment antes de reconciliar doctor, stdout da run, state, manifest, parser público, schema Draft 2020-12 empacotado, hashes e seções Markdown. Somente após nove checks aprovados ele copia report JSON/Markdown e resumo sanitizado para a superfície publicável. Durante a primeira prova, a captura local do PowerShell adicionou BOM e foi recusada; a normalização da captura para UTF-8 sem BOM permitiu auditar a mesma run, sem mascarar falha funcional.

A prova também revelou que a imagem `python-quality`, opcional ao caminho linear, bloqueava doctor embora o plano construísse apenas pytest. A ausência agora é `WARN/DEGRADED`; pytest continua obrigatório. Quickstart e limites declaram que o wheel não contém imagem Docker e que seu build usa o tooling da mesma revisão.

Wheel e sdist foram construídos sob metadata ainda intencionalmente `0.1.0a5`, em diretório isolado, e passaram no scanner. O wheel inclui contrato e schema. Uma venv temporária fora do checkout instalou o wheel com `--no-deps`; doctor terminou `DEGRADED/READY`, demo keyless `SUCCEEDED/ACCEPTED`, os nove checks passaram, o scanner aprovou toda `.asef` e nenhum container gerenciado permaneceu.

O workflow ganhou o sétimo job independente `public-experience`: checker, build/scan, instalação limpa, somente imagem pytest, doctor/demo keyless, auditor, scanner, orphan check e publicação por sete dias apenas dos dois reports e dois resumos. A regressão final aprovou 344 testes, com 33 skips opcionais e branch coverage de 85,34%. A composição YAML contém sete jobs, mas nenhuma CI pública foi acionada nesta fatia. O parecer está em `docs/reviews/2026-07-17-revisao-fatia-585.md`.

### Fatia 5.8.6 — revisão final e candidata

A metadata foi promovida para `0.1.0a6`. CLI e builder agora possuem fallbacks reconciliados com `pyproject.toml`. `jsonschema==4.25.1` entrou apenas no extra de teste/auditoria; o wheel continua sem dependências obrigatórias. O auditor passou a executar validação Draft 2020-12 completa.

O walkthrough frio partiu de diretório vazio, instalou o wheel com `--no-deps` e, seguindo os documentos, executou doctor, demo, parser, checklist, cleanup e rotas comunitárias. Terminou `DEGRADED/READY`, `SUCCEEDED/ACCEPTED`, evidência somente `VERIFIED` e `DRY_RUN_COMPLETE`, sem finding novo.

Smoke `smoke-20260717T151010Z-359283e8` permaneceu 20/20; Security `security-20260717T151032Z-e354e383` permaneceu 12/12. A matriz Docker/quality descobriu 20 integrações, aprovou 17 e manteve três skips conhecidos do host Windows; as duas provas Linux ignoradas localmente passaram 2/2 em container isolado. A regressão aprovou 345 testes, com 33 skips opcionais e branch coverage de 85,34%.

Lucas aprovou o checkpoint de commit/push/CI. O commit `9739c1e` foi enviado à `main` e a [CI pública `29597109452`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29597109452) aprovou `core`, `framework-spikes`, `docker-security`, `alpha-smoke`, `quality-capabilities`, `alpha-security` e `public-experience`. O fechamento `ddeeb3a` repetiu os sete jobs com sucesso na CI `29597666988`. Após nova autorização explícita, a tag anotada e a [pré-release `v0.1.0a6`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a6) foram publicadas com wheel e sdist auditados. O incremento 5.8 está concluído; 5.9, Gate 5 e Etapa 6 permanecem decisões separadas. Parecer: `docs/reviews/2026-07-17-revisao-fatia-586.md`; walkthrough: `docs/reviews/2026-07-17-walkthrough-frio-58.md`.

## 5.9 — Avaliação final, livro e Gate 5

O planejamento detalhado foi produzido e aprovado em 2026-07-17 e está em `docs/project/stage-05-increment-59-plan.md`. A execução divide o fechamento em seis fatias: inventário/contrato de evidências; ensaio da release; sessão com QE externo; triagem/remediação; baseline/retrospectiva/livro; e pacote decisório do Gate 5.

O plano exige participante humano externo real, consentimento e resultado anonimizado; preflight do mantenedor ou IA não conta. Finding crítico/alto bloqueia recomendação de aprovação. Uma candidata `0.1.0a7` só será proposta se houver mudança material no package ou na jornada pública avaliada.

### Fatia 5.9.1 — inventário e contrato de evidências

Lucas autorizou somente a primeira fatia. O inventário JSON congelou `v0.1.0a6`, commit da tag, commit funcional, wheel/sdist, tamanhos, SHA-256 e três execuções públicas com os sete jobs. A matriz inicial possui G5-01 a G5-20 em ordem e 40 referências locais: 18 `MET`, G5-18 `MET_WITH_RESIDUAL_RISK` até a sessão externa e G5-19 `PARTIAL` até baseline/retrospectiva final.

O protocolo `ASEF-EXT-ALPHA 1.0.0` define elegibilidade, consentimento, coleta mínima, tarefas EXT-01 a EXT-08, intervenções, rubrica e severidade. Nenhum participante foi contatado e `results` permanece vazio. O checker offline rejeita alterações nos digests congelados, jobs/IDs/paths inválidos, aprovação contraditória, PII inclusive aninhada, consentimento/privacidade ausentes, intervenção central e crítico/alto aberto em sessão marcada válida. O `public-experience` passou a executar o checker sem adicionar job ou chamada externa.

O docs checker ganhou consistência da release canônica entre README, quickstart e suporte, corrigindo duas referências históricas encontradas no planejamento. Nove testes do checker e cinco testes documentais passaram; a regressão completa aprovou 355 testes com 33 skips opcionais e branch coverage de 85%. A 5.9.1 está pronta para revisão humana. 5.9.2, participante, sessão, release, Gate 5 e Etapa 6 continuam não autorizados.

Lucas aprovou a 5.9.1 e autorizou somente a 5.9.2.

### Fatia 5.9.2 — ensaio da release e kit do participante

Wheel e sdist foram baixados da release oficial em diretório temporário fora do checkout. Os hashes conferiram; a venv instalou `0.1.0a6` sem dependências; a imagem pytest foi construída do sdist. Doctor retornou `DEGRADED/READY` com 12 checks, a demo terminou `SUCCEEDED/ACCEPTED`, o auditor passou 9/9, cleanup ficou em `DRY_RUN_COMPLETE`, scanner passou e nenhum container gerenciado permaneceu.

O ensaio encontrou `PREFLIGHT-F-001`: README, quickstart e suporte dentro da tag `v0.1.0a6` afirmam que `v0.1.0a5` é a última release e que `0.1.0a6` não foi publicada. A correção existe apenas na árvore local posterior à tag. Como EXT-01/EXT-02 exigem identidade documental imutável, o finding foi classificado alto e aberto. O preflight terminou `BLOCKED/NOT_READY`; kit e checklist ficaram `HOLD`. Nenhum participante foi contatado.

A 5.9.2 satisfez sua regra de parada: runtime aprovado, finding conhecido transformado em bloqueio explícito. A regressão final aprovou 356 testes com 33 skips opcionais e branch coverage de 85%; checker 10/10 e documentação 126 arquivos/107 links permaneceram verdes. A 5.9.3 não está autorizada nem tecnicamente pronta. O próximo checkpoint é decidir se uma candidata corretiva deve ser preparada e auditada antes da sessão.

### Correção do bloqueio da 5.9.2 — candidata local `0.1.0a7`

Lucas autorizou preparar a candidata corretiva, sem autorizar 5.9.3, commit, push, CI, tag ou publicação. O novo `release-state.json` separa a última publicação `v0.1.0a6` da versão em desenvolvimento `0.1.0a7`; metadata, fallbacks e os três documentos canônicos foram reconciliados. O docs checker agora protege ambas as identidades.

Wheel e sdist locais foram construídos e escaneados. Fora do checkout, o sdist passou na auditoria de 126 arquivos/107 links; o wheel instalou sem dependências e reportou `0.1.0a7`; doctor terminou `DEGRADED/READY` com 12 checks; demo `SUCCEEDED/ACCEPTED`; auditor 9/9; cleanup `DRY_RUN_COMPLETE`; scanner verde; zero containers gerenciados. A regressão aprovou 357 testes, 33 skips e coverage de 85%.

Parecer: `READY_FOR_PUBLICATION_CHECKPOINT`. Como os artifacts ainda são locais e mutáveis, `PREFLIGHT-F-001` permanece alto/aberto, kit/checklist permanecem `HOLD` e a 5.9.3 continua bloqueada. Evidência: `docs/evaluations/2026-07-17-alpha-python-candidate-a7-preflight.json`; revisão: `docs/reviews/2026-07-17-revisao-candidata-corretiva-a7.md`.

O commit `58ea802` foi enviado à `main` após autorização humana. A [CI `29620941881`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29620941881) aprovou os sete jobs, incluindo o novo Gate checker dentro de `public-experience`. A candidata está pronta para decisão separada de tag/pré-release; ainda não existe asset remoto `v0.1.0a7` para reauditar.

### Publicação corretiva e postflight remoto

Lucas autorizou tag e pré-release. O commit de release `79fbeb0` passou nos sete jobs da [CI `29647693611`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29647693611). A tag anotada e a [pré-release `v0.1.0a7`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a7) foram publicadas com wheel SHA-256 `f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad` e sdist SHA-256 `d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af`.

Os assets oficiais foram baixados novamente e os hashes coincidiram. O sdist passou no docs checker com 128 arquivos/109 links; o wheel instalou sem dependências como `0.1.0a7`; doctor terminou `DEGRADED/READY` 12 checks; demo `SUCCEEDED/ACCEPTED`; auditor 9/9; cleanup `DRY_RUN_COMPLETE`; scanner verde; zero containers. `PREFLIGHT-F-001` foi resolvido, kit/checklist passaram a `READY` e a 5.9.3 continua não iniciada até nova autorização.

### Reconciliação documental e autorização do fechamento acelerado

Lucas autorizou reconciliar a documentação e avançar continuamente por 5.9.3–5.9.6, preservando apenas os checkpoints humanos indispensáveis. Planejamento Mestre, cabeçalhos das Etapas 4/5, plano 5.9, inventário G5, checker, critérios textuais, source map, proveniência, EXP-001 e mapa de governança foram alinhados ao estado remoto de `v0.1.0a7` e ao postflight aprovado.

O inventário foi promovido inicialmente à revisão `1.1.0`, sem resultado fictício. O checker passou a congelar a revisão a7 e a validar o arquivo de resultado anonimizado quando a avaliação externa mudar para `COMPLETED` ou `BLOCKED`. Treze testes adversariais específicos, regressão completa de 360 testes com 33 skips opcionais, os 20 critérios/40 evidências e o checker documental sobre 130 arquivos/117 links passaram sem findings.

A indisponibilidade de QE externo foi confirmada por Lucas. Em vez de simular independência, o inventário `1.2.0` marca a avaliação externa `DEFERRED` e abre uma avaliação interna acompanhada separada, com `I01` no papel declarado de autor/mantenedor, consentimento confirmado e chat como canal. O protocolo externo foi corrigido para `v0.1.0a7`/`1.0.1`; o protocolo interno preserva o resultado como `INFORMATIVE_INTERNAL`. Nenhuma feature ou atividade da Etapa 6 foi iniciada.

### Fatias 5.9.3–5.9.4 — avaliação interna e triagem

A sessão `I01` foi concluída como `INFORMATIVE_INTERNAL`, com assistência técnica da IA e revisão/decisão de Lucas declaradas. EXT-03 não foi tentada; EXT-01/02/04/05/07/08 tiveram intervenção e EXT-06 teve recuperação. O resultado anonimizado omite terminal bruto, paths e identidade civil.

`INT-F-001` HIGH, sobre maturidade/segurança, e `INT-F-003` MEDIUM, sobre fail-closed no cleanup, foram corrigidos durante a sessão. `INT-F-002` MEDIUM permanece `ACCEPTED_RISK`: o participante pulou a instalação humana isolada; o postflight a7 é mitigação técnica, não evidência de usabilidade. A triagem escolheu caminho A, sem feature, correção material ou nova release. O inventário `1.3.0` passou a `INTERNAL_EVALUATED`; avaliação externa continua `DEFERRED`.

### Fatia 5.9.5 — baseline, retrospectiva, Lesson 003 e livro

A baseline foi fechada sem inventar horas ou interações posteriores ao Dia 5. A retrospectiva da Etapa 5 e a Lesson 003 separam fatos, percepção autoral, estruturação por IA, correções e decisões humanas. A proposta de Lucas de experimentar futuramente um sistema público foi preservada como hipótese de backlog, sem convertê-la em feature ou automação web.

Source map e proveniência passaram a incluir a autovalidação I01 e o limite da independência. G5-19 tornou-se `MET`; o inventário foi promovido a `1.4.0`. A redação do livro permanece `rascunho assistido`, pois aprovação de Gate não equivale a aprovação editorial da voz.

### Fatia 5.9.6 — candidata local do Gate 5

A regressão local aprovou 362 testes, 33 skips opt-in e branch coverage geral de 85%. Gate checker, docs checker e verificações de higiene passaram. O pacote decisório recomenda `APPROVE_WITH_CONDITIONS` somente após CI pública final, mantendo avaliação externa e instalação humana isolada como condições.

O produto/package `v0.1.0a7` não mudou. Após autorização, o commit `2e7655e` foi publicado e a CI `29654457005` aprovou os sete jobs. O inventário `1.5.0` está `FINAL` com recomendação `APPROVE_WITH_CONDITIONS`; resta a decisão explícita de Lucas. Nenhuma feature ou Etapa 6 foi iniciada.

### Decisão do Gate 5

Lucas aprovou explicitamente o Gate 5 com as condições propostas: feedback externo posterior, repetição da jornada instalada por pessoa externa à autoria, linguagem experimental, planejamento separado para SUT público e nenhuma implementação da Etapa 6 sem plano próprio. A Etapa 5 está concluída; somente o planejamento detalhado da Etapa 6 foi autorizado.
