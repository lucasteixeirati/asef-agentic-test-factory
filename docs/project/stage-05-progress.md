# Progresso da Etapa 5 — Alpha Python

- **Plano:** `docs/project/stage-05-alpha-python-plan.md`
- **Gate:** `docs/project/gates/gate-05-acceptance-plan.md`
- **Estado atual:** incrementos 5.1, 5.2 e 5.3 concluídos; versão pré-alpha `0.1.0a2` publicada

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
