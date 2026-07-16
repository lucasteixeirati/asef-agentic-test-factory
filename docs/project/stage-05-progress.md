# Progresso da Etapa 5 — Alpha Python

- **Plano:** `docs/project/stage-05-alpha-python-plan.md`
- **Gate:** `docs/project/gates/gate-05-acceptance-plan.md`
- **Estado atual:** incrementos 5.1 a 5.6 concluídos; pré-alpha `v0.1.0a4` publicada

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

O commit documental `f55be73` (`docs: approve stage 5.6 candidate after ci`) também foi publicado e a CI de fechamento `29461247717` aprovou novamente os cinco jobs. A tag anotada e a pré-release [`v0.1.0a4`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a4), com wheel e sdist auditados, foram publicadas em 2026-07-15. O incremento 5.6 está concluído; o 5.7 depende de novo planejamento e aprovação explícita.
