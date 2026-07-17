# Incremento 5.8 — Relatórios e experiência pública

- **Data:** 2026-07-16
- **Estado:** concluído e publicado em `v0.1.0a6`
- **Dependências:** incrementos 5.1 a 5.7 concluídos e publicados até `v0.1.0a5`
- **Gate relacionado:** G5-05, G5-14 e G5-18, com evidência complementar para G5-01, G5-02, G5-09, G5-15, G5-17, G5-19 e G5-20
- **Decisão vigente:** Lucas aprovou separadamente as seis fatias, o checkpoint de commit/push/CI e a publicação. 5.9, Gate 5 e Etapa 6 continuam sem autorização

## 1. Objetivo

Transformar o Alpha Python já executável em uma experiência pública coerente, auditável e ensinável para as personas P1 e P2: uma engenheira de qualidade deve conseguir instalar, diagnosticar, executar a demo e interpretar o resultado; um SDET deve conseguir rastrear requisito, análise, cenários, artifact, execução, oracle, quality capabilities e evidências sem depender de explicação oral do autor.

O incremento também substituirá o relatório ad hoc do walking skeleton por um contrato público do Alpha. JSON e Markdown serão duas representações da mesma projeção determinística, com fatos, inferências, recomendações e limitações explicitamente separados.

O 5.8 prepara a experiência para avaliação posterior. Ele não alegará validação por usuário externo, não fechará o Gate 5 e não produzirá conclusão retrospectiva final da Etapa 5.

## 2. Escopo

### Incluído

- contrato neutro e versionado para `AlphaRunReport 1.0.0`;
- schema JSON publicável e validação sem dependência obrigatória de framework externo;
- IDs estáveis para requisito, comportamentos, riscos, cenários, artifact, tentativas e evidências;
- projeção determinística dos fatos já persistidos na run;
- separação explícita entre fatos observados, inferências derivadas, recomendações allowlisted e limitações;
- referências de evidência relativas à run, com SHA-256 e verificação de integridade;
- report final para todos os terminais públicos com identidade e diretório de run já persistidos, alcançáveis por `asef run`, `resume` e `cancel`;
- paridade semântica entre `report.json` e `report.md`;
- atualização aditiva do stdout da CLI com paths JSON e Markdown;
- README reduzido a entrada pública e navegação, sem concentrar todo o tutorial;
- quickstart instalado e keyless;
- tutorial completo da demo WF-001;
- guia live separado, com budget e secret somente no host;
- guia de interpretação do relatório;
- troubleshooting orientado por `asef doctor`, classificação e exit code;
- arquitetura real do Alpha Python;
- matriz de suporte e limitações atuais;
- atualização da estratégia de avaliação, segurança, evidências e contexto;
- contribuição, código de conduta e orientação para adapters/perfis;
- verificador offline de links, anchors, versões e comandos documentados;
- job de CI `public-experience`, separado dos seis jobs atuais;
- package audit em diretório limpo, execução do quickstart e publicação de report sanitizado;
- revisão final, journal, progresso, Gate 5, baseline e candidata pré-alpha esperada `0.1.0a6`.

### Não incluído

- sessão observada com participante externo real;
- declarar que o relatório foi compreendido sem ajuda pelo público-alvo;
- Developer Preview com 3–5 QEs, pertencente à Etapa 7;
- retrospectiva final, lição aprendida ou pacote decisório do Gate 5, pertencentes ao 5.9;
- relatório agregado de toda a Etapa 5 ou comparação estatística entre releases;
- dashboard, HTML, PDF, UI, servidor web ou upload remoto;
- telemetria de leitura, analytics ou coleta de dados do usuário;
- novo provider, skill, MCP, perfil de linguagem ou capability de tooling;
- alteração do SUT, correção automática de produto ou recomendação gerada por LLM;
- publicação automática de prompts, respostas, source do SUT, logs brutos ou environment completo;
- tradução integral da documentação para inglês;
- suporte anunciado para macOS, Linux nativo, ARM64, TypeScript ou Java;
- release estável, aprovação do Gate 5 ou início da Etapa 6.

## 3. Findings da baseline

1. `JsonRunStore.save_report()` constrói diretamente um `dict` e Markdown, misturando contrato, composição, persistência e apresentação.
2. O report atual contém status, classificação, requirement, avaliação, quality, execution, usage e refs, mas não possui contrato de domínio próprio nem parser/validator público.
3. O JSON não separa fato, inferência e recomendação, deixando G5-14 e FR-055 parciais.
4. O Markdown mostra apenas uma fração do JSON e pode omitir análise, riscos, cenários, attempts, oracle, budget, evidências, intervenção humana e limitações.
5. `asef run` pode terminar em policy, budget ou provider failure antes de existir workspace; nesses caminhos, o resultado público pode não possuir report final.
6. A composição Alpha usada pelo Smoke persiste análise, design, attempts, oracle e avaliação combinada, mas não possui uma etapa única de report final.
7. Comportamentos, riscos e cenários são persistidos como listas. Cenários já recebem `SCN-NNN`; comportamentos e riscos ainda precisam de IDs derivados sem inventar relações inexistentes.
8. O artifact declara `scenario_ids`, permitindo rastreabilidade cenário→teste. Não existe relação explícita risco→cenário; o report deve publicar essa limitação em vez de fabricar links.
9. `EvidenceRef` já exige path relativo e SHA-256, porém o report atual não prova que cada referência ainda existe e concilia com o conteúdo persistido.
10. O manifest recebe status, classificação, usage e refs, mas ainda não referencia formalmente o report final e seu hash.
11. O README contém quickstart, live, datasets, doctor e cleanup num único documento; a navegação funciona, mas a jornada progressiva e o troubleshooting ainda não estão consolidados.
12. Não existem documentos dedicados para quickstart, tutorial demo, tutorial live, interpretação de report, troubleshooting, suporte/limitações ou arquitetura real do Alpha.
13. `CONTRIBUTING.md` é correto, porém curto para orientar execução da matriz, fronteiras do core e criação de adapter/perfil.
14. A estratégia open source exige código de conduta; `CODE_OF_CONDUCT.md` ainda não existe. Templates de issue e PR já existem.
15. A documentação conceitual ainda contém versões e estados anteriores em alguns pontos, inclusive referência da distribuição `0.1.0a4`.
16. A CI comprova package e demo fora do checkout, mas não executa uma jornada pública dedicada nem valida automaticamente links internos e schema do report instalado.
17. G5-05, G5-14 e G5-18 permanecem parciais e são a responsabilidade principal deste incremento.

## 4. Princípios e fronteiras

### 4.1 O report é projeção, não nova fonte de verdade

O report será derivado de request, state, snapshot, manifests e resultados validados. Ele não reexecutará provider, Docker, oracle ou quality tooling; não lerá arquivos arbitrários do projeto; não alterará classificação; e não criará fatos ausentes.

Quando um dado não foi observado, o report usará ausência explícita ou limitation code. `unknown`, `not_observed` e `not_applicable` não serão convertidos em zero, sucesso ou inferência.

### 4.2 Fato, inferência e recomendação são tipos distintos

- **Fato:** entrada validada ou observação mensurada, com origem e evidência quando aplicável.
- **Inferência:** conclusão derivada por regra identificável, com `basis_fact_ids` e `evidence_refs`.
- **Recomendação:** próxima ação allowlisted, ligada a uma classificação ou limitation code; não muda o resultado.
- **Limitação:** fronteira de validade, dado ausente ou capability não comprovada.

Texto explicativo não mudará a categoria semântica. Recomendações não serão produzidas pelo provider no 5.8.

### 4.3 Sem rastreabilidade inventada

O runtime pode derivar IDs canônicos pela ordem validada:

- `REQ-001` para o requisito da run;
- `BEH-001..N` para comportamentos;
- `RSK-001..N` para riscos;
- `SCN-001..N` para cenários;
- `ART-ATTEMPT-NNN` para artifacts;
- `EXEC-ATTEMPT-NNN-{generated|oracle}` para execuções.

Os links permitidos são somente os comprovados:

- requisito→comportamentos/riscos/cenários produzidos na análise;
- cenário→artifact pelos `scenario_ids`;
- artifact→execução/evaluation pela attempt;
- conclusão→evaluation/evidence refs;
- quality observation→native/driver/normalized refs.

O report não ligará risco específico a cenário específico quando essa relação não existir no contrato de análise.

### 4.4 JSON é normativo; Markdown é uma view

`report.json` será a representação normativa. `report.md` será renderizado exclusivamente a partir de um `AlphaRunReport` já validado. O Markdown não poderá acrescentar conclusão, número ou recomendação ausente no JSON.

### 4.5 Experiência pública continua offline por padrão

Quickstart, tutorial demo, validação de report e CI serão keyless. O guia live será separado, opt-in, com budget positivo, tarifas fornecidas pelo operador, secret somente no host e aviso de custo/variabilidade.

### 4.6 Documentação não altera nível de suporte

Descrever Python, TypeScript, Java, macOS ou Linux não os torna suportados. A matriz usará estados fechados como `reference`, `experimental`, `planned`, `validated-host` e `not-validated`.

## 5. Contrato `AlphaRunReport 1.0.0`

### 5.1 Cabeçalho e identidade

Campos obrigatórios:

- `schema_version`;
- `report_id`, igual à identidade da run ou derivado sem nova autoridade;
- `asef_version`;
- `run_id`, `workflow_id` e `workflow_version`;
- `status`, `classification` e `terminal`;
- `execution_mode`;
- `language_profile`;
- `support_level`;
- `context_snapshot_ref`;
- `report_generated_from_state_schema`.

O contrato rejeitará enum desconhecida, versão incompatível, IDs vazios, paths absolutos, traversal, boolean como inteiro e coleções duplicadas.

O schema será distribuído em `src/asef/schemas/alpha-run-report.schema.json`. O runtime continuará validando pelo contrato Python sem dependência obrigatória; testes/CI poderão usar um validador JSON Schema pinado como dependência exclusiva de qualidade para comprovar conformidade com o documento publicado.

### 5.2 Seções normativas

O JSON conterá, no mínimo:

1. `requirement`;
2. `traceability`;
3. `artifacts`;
4. `attempts`;
5. `functional_result`;
6. `quality`;
7. `human_interventions`;
8. `policy_and_budgets`;
9. `usage`;
10. `evidence`;
11. `facts`;
12. `inferences`;
13. `recommendations`;
14. `limitations`.

Seções sem observação permanecem presentes com estado explícito ou coleção vazia validada. Não haverá estrutura variável controlada por provider.

### 5.3 Facts

Cada fact terá:

- `fact_id`;
- `category`;
- `statement_code`;
- `value` limitado a tipo permitido;
- `source_kind`;
- `source_ref` opcional;
- `evidence_refs`;
- `observed` ou `not_observed`.

Statements e categories serão enums/registries fechados. Facts não conterão prompt, resposta integral, source, stdout/stderr brutos, variável de ambiente ou path absoluto.

### 5.4 Inferences

Cada inference terá:

- `inference_id`;
- `kind`;
- `conclusion_code`;
- `statement`;
- `basis_fact_ids`;
- `evidence_refs`;
- `uncertainty` ou limitation associada quando a conclusão não for completa.

Uma inference sem base factual ou com referência desconhecida é inválida.

### 5.5 Recommendations

Cada recommendation terá:

- `recommendation_id`;
- `recommendation_code`;
- `applies_to`;
- `statement` proveniente de template revisado;
- `blocking`;
- `related_inference_ids` ou `limitation_codes`.

Exemplos iniciais: revisar possível defeito do SUT, corrigir teste gerado, executar `asef doctor`, revisar policy, aumentar budget conscientemente, fornecer esclarecimento, consultar evidência e não usar em produção.

### 5.6 Evidence e integridade

Cada item publicável terá:

- `evidence_id`;
- `kind`;
- `relative_path`;
- `sha256`;
- `schema_version`;
- `integrity_status`: `VERIFIED`, `MISSING`, `MISMATCH` ou `NOT_CHECKED`;
- `publishable`;
- `sanitized`.

Paths serão resolvidos somente abaixo da run. Link, junction, path externo, arquivo ilegível ou hash divergente nunca serão `VERIFIED`.

Uma falha de integridade não será ocultada. O report ainda deverá poder ser emitido para diagnosticar a run, mas incluirá limitation/inference bloqueante e a CLI retornará o exit code correspondente ao resultado original, sem transformá-lo em sucesso.

### 5.7 Paridade Markdown

O Markdown seguirá ordem fixa:

1. resumo executivo;
2. status e classificação;
3. requisito;
4. análise e rastreabilidade;
5. attempts e resultado funcional;
6. oracle e intervenção humana;
7. quality capabilities;
8. budgets e usage;
9. evidências;
10. fatos;
11. inferências;
12. recomendações;
13. limitações;
14. como interpretar o resultado.

Controle de caracteres, Markdown injection, tabelas, links e conteúdo longo serão testados. Texto vindo de input será escapado e truncado conforme o contrato.

## 6. Composição e persistência

### 6.1 Fronteiras propostas

- `report_contracts.py`: tipos, enums, validação e serialização neutra;
- `application/build_alpha_report.py`: composição determinística a partir de state e observações tipadas;
- `application/ports.py`: porta mínima para integridade/persistência;
- `adapters/report_evidence.py`: verificação de refs sob a run;
- `adapters/alpha_report_store.py`: escrita atômica JSON/Markdown e atualização do manifest;
- `adapters/alpha_report_markdown.py`: renderer puro a partir do contrato;
- `src/asef/schemas/alpha-run-report.schema.json`: schema público empacotado;
- `JsonRunStore`: deixa de construir conteúdo e delega persistência do report.

Nomes finais podem variar durante a implementação, mas contrato, aplicação, verificação e apresentação permanecerão separados.

### 6.2 Ciclo de vida

- estados intermediários continuam em `state.json` e `events.jsonl`;
- report final é obrigatório quando uma operação pública atinge terminal após a criação persistida da run;
- input/contexto rejeitado antes de existir diretório de run continua como diagnóstico da CLI e não fabrica report sem evidência;
- espera humana pode produzir state/checkpoint sem alegar report terminal;
- `resume` e `cancel` produzem o report correspondente ao novo terminal;
- quality pode enriquecer a run antes do report final;
- report terminal é persistido atomicamente;
- manifest recebe refs e hashes de `report.json` e `report.md`;
- reemissão idempotente com o mesmo state produz conteúdo semanticamente idêntico;
- divergência entre state, manifest e report é erro de infraestrutura, nunca sucesso.

### 6.3 CLI

Mudança aditiva no JSON do stdout:

- `report_json`;
- `report_markdown`;
- `report_schema_version`.

`report_path` pode permanecer durante compatibilidade, apontando para Markdown. Nenhum texto humano adicional será impresso em stdout. Orientações continuam em stderr/log ou dentro do report.

Não será criado novo comando `asef report` nesta etapa, salvo finding técnico que demonstre necessidade e receba aprovação específica.

## 7. Jornada pública

### 7.1 README

O README permanecerá a entrada de cinco minutos:

- propósito e estado experimental;
- o que está comprovado e o que não está;
- requisitos mínimos;
- quickstart curto;
- exemplo de resultado;
- mapa da documentação;
- suporte e limitações;
- segurança e contribuição;
- roadmap.

Detalhes operacionais serão movidos para guias dedicados, reduzindo duplicação.

### 7.2 Quickstart instalado

Criar `docs/getting-started/quickstart.md` com:

1. Python 3.13, Docker e Git;
2. instalação a partir da release/wheel ou checkout;
3. `asef doctor --mode demo`;
4. `asef run`;
5. leitura dos paths retornados;
6. validação do resultado esperado;
7. interpretação mínima de `ACCEPTED`;
8. cleanup dry-run;
9. próximos links.

O caminho principal não usa chave, extra opcional, provider ou dataset completo.

### 7.3 Tutorial demo WF-001

Criar `docs/tutorials/wf-001-demo.md` cobrindo:

- contexto fictício;
- requirement e SUT da demo;
- análise, riscos e cenários;
- artifact e static validation;
- Docker e resultado;
- report e evidence refs;
- diferença entre resultado funcional e quality evidence;
- classificações negativas relevantes;
- limitações da cassette.

### 7.4 Guia live

Criar `docs/tutorials/wf-001-live.md` separado:

- precondições e riscos;
- `OPENAI_API_KEY` somente no host;
- model e tarifas informados pelo operador;
- budget positivo e hard stops;
- contexto live fictício;
- comando mínimo;
- recording de cassette somente quando autorizado;
- custos estimados versus observados;
- falhas/provider exits;
- sanitização e cleanup;
- nenhuma garantia de disponibilidade/preço/modelo.

Nenhum live smoke obrigatório será executado no 5.8 sem autorização específica de custo.

### 7.5 Interpretação do report

Criar `docs/guides/report-interpretation.md` com exemplos para:

- `ACCEPTED`;
- `TEST_ERROR`;
- `SUT_DEFECT_SUSPECTED`;
- `POLICY_VIOLATION`;
- `BUDGET_ERROR`;
- `INFRASTRUCTURE_ERROR`;
- `WAITING_HUMAN` quando aplicável;
- quality `COMPLETED`, `PARTIAL`, `UNAVAILABLE`, `FAILED` e `BUDGET_EXHAUSTED`.

O guia explicará que coverage/mutation são evidências, não thresholds universais.

### 7.6 Troubleshooting

Criar `docs/guides/troubleshooting.md`, organizado por:

- exit code;
- classification;
- doctor check;
- Docker CLI/daemon/image;
- contexto;
- provider/live key/budget;
- policy do artifact;
- filesystem/cleanup;
- report/evidence integrity;
- onde abrir bug ou vulnerabilidade.

Cada ação será segura e delimitada. O guia não recomendará prune amplo, desabilitar security controls, copiar secret para arquivo ou executar no host.

## 8. Arquitetura, suporte e contribuição

### 8.1 Arquitetura real

Criar `docs/architecture/alpha-python-architecture.md` descrevendo o fluxo implementado:

```text
CLI/request
  -> context + policies
  -> recorded/live agent adapter
  -> skill/static validation
  -> ephemeral workspace
  -> Docker execution
  -> curated oracle + correction loop
  -> optional quality capabilities
  -> typed report + evidence
```

O documento distinguirá core, application ports, adapters, tooling containers, datasets, reports, logs e decisões humanas.

### 8.2 Evidência, avaliação e segurança

Atualizar:

- `evidence-model.md` com árvore real, report hash e integridade;
- `alpha-python-contracts.md` com `AlphaRunReport`;
- `evaluation-strategy.md` com interpretação e limites;
- `security-strategy.md` com superfície de publicação;
- observabilidade, doctor, cleanup e live provider com links canônicos;
- `language-matrix.md` com suporte realmente comprovado.

### 8.3 Limitações e suporte

Criar `docs/project/support-and-limitations.md` como fonte única para:

- host de referência;
- versões suportadas;
- capabilities por perfil;
- níveis de suporte;
- limitações de sandbox;
- ausência de produção/hostile-code guarantee;
- modo live experimental;
- restrições de cleanup Windows;
- ambientes não validados;
- limites do Smoke e Security Dataset.

README, SECURITY e guias apontarão para esse documento sem copiar listas divergentes.

### 8.4 Contribuição

Atualizar `CONTRIBUTING.md` e criar `docs/contributing/adapter-guide.md` com:

- setup mínimo e extras;
- matriz local de testes;
- testes Docker opt-in;
- secret scan;
- fronteiras de imports;
- como adicionar capability/adapter;
- como propor perfil sem contaminar o core;
- contratos, fixtures e conformance;
- impacto documental;
- uso responsável de IA em contribuição.

Criar `CODE_OF_CONDUCT.md` com política pública adequada ao projeto. Templates existentes serão auditados, não recriados sem necessidade.

## 9. Validação automatizada da documentação

Criar um verificador offline, sem crawler externo, para:

- links relativos e anchors internos;
- arquivos referenciados;
- versão atual em documentos canônicos;
- existência dos guias obrigatórios;
- comandos públicos conhecidos;
- paths de exemplo;
- ausência de links locais absolutos;
- ausência de claims proibidas como “produção segura”, “certificado” ou suporte não validado;
- ausência de placeholders e marcadores pendentes em documentos de uso;
- consistência entre README, support matrix e CLI help.

O verificador não substituirá revisão editorial. Links externos serão tratados como texto ou verificados separadamente sem tornar a CI dependente da internet.

## 10. Estratégia de testes

### Contratos e unitários

- contrato aceita report completo válido;
- campos ausentes, extras, duplicados ou com versão inválida falham;
- enums e IDs desconhecidos falham;
- fatos, inferências e recomendações não se misturam;
- inference exige facts/evidence existentes;
- recommendation exige código allowlisted;
- trace links apontam apenas para IDs existentes;
- ausência de relação risco→cenário não gera link fabricado;
- paths absolutos/traversal/link são rejeitados;
- Markdown é renderizado somente de report validado;
- Markdown escapa input, pipes, HTML, backticks e controle;
- JSON e Markdown reconciliam status, classificação, contagens e códigos;
- report não contém prompt, source, raw environment ou secret;
- builder não importa Docker, OpenAI, pytest, coverage, mutmut ou LangGraph;
- store escreve atomicamente e atualiza manifest com hashes;
- reemissão idempotente não muda semântica.

### Terminais e workflow

- `ACCEPTED` gera report completo;
- failure de teste gera report;
- policy antes do workspace gera report;
- budget antes/depois de provider gera report;
- provider/output inválido terminal gera report;
- infraestrutura Docker indisponível gera report;
- cancelamento gera report;
- suspeita de defeito após decisão humana gera report;
- report após quality inclui observations sem mudar acceptance;
- terminal sem report é falha de teste;
- state, manifest, stdout CLI e report reconciliam.

### Documentação e experiência

- quickstart instalado em diretório vazio;
- `asef doctor` retorna READY/DEGRADED esperado;
- demo keyless termina `SUCCEEDED/ACCEPTED`;
- JSON valida contra contrato/schema empacotado;
- Markdown contém todas as seções normativas;
- report guide explica corretamente fixtures de classificação;
- link/anchor checker passa;
- comandos documentados existem no `asef --help`;
- README aponta para guias canônicos;
- package contém schema e recursos necessários.

### Regressão

- branch coverage permanece >=85%;
- Smoke permanece 20/20;
- Security permanece 12/12;
- quality conformance permanece verde;
- doctor/cleanup permanecem verdes;
- seis jobs existentes não perdem independência;
- source, wheel, sdist, report, docs fixtures e artifacts passam no secret scan;
- nenhum container/workspace gerenciado permanece.

## 11. CI e evidências

Adicionar o sétimo job `public-experience`:

1. checkout e Python 3.13;
2. executar verificador documental offline;
3. construir wheel e sdist;
4. escanear os dois artifacts;
5. instalar o wheel sem dependências em venv/diretório limpo;
6. construir somente a imagem pytest pinada;
7. remover `OPENAI_API_KEY`;
8. executar `asef doctor --mode demo`;
9. executar o quickstart keyless fora do checkout;
10. validar stdout, state, manifest e `AlphaRunReport`;
11. validar JSON contra schema empacotado;
12. verificar paridade mínima do Markdown;
13. escanear a `.asef` gerada;
14. verificar ausência de containers gerenciados;
15. publicar somente report JSON/Markdown e resumo de auditoria sanitizados por sete dias.

O job não executará provider live, não receberá secret, não navegará links externos e não publicará prompt, source, stdout/stderr bruto ou workspace.

## 12. Fatias de implementação

1. **5.8.1 — Contrato e schema:** congelar `AlphaRunReport 1.0.0`, taxonomia fato/inferência/recomendação/limitação, trace IDs, JSON Schema e threat model de publicação.
2. **5.8.2 — Builder e terminais:** separar composição/store/renderer, verificar evidências, atualizar manifest/CLI e garantir report em todos os terminais públicos.
3. **5.8.3 — Jornada de uso:** README, quickstart, tutorial demo, guia live, interpretação do report e troubleshooting.
4. **5.8.4 — Arquitetura e contribuição:** arquitetura real, evidence/evaluation/security, suporte/limitações, contribuição, adapter guide e código de conduta.
5. **5.8.5 — Experiência instalada e CI:** verificador documental, package audit, quickstart fora do checkout e job `public-experience`.
6. **5.8.6 — Revisão e candidata:** regressões, scanner, walkthrough frio roteirizado, parecer, documentação de progresso e candidata esperada `0.1.0a6`.

Cada fatia termina com testes e revisão próprios. A autorização de uma fatia não autoriza automaticamente a seguinte, publicação ou Gate 5.

**Progresso em 2026-07-16:** a 5.8.1 foi concluída e aprovada localmente. Seus critérios 1 a 10 estão cobertos pelo contrato, parser estrito, schema empacotado, threat model e testes adversariais. Os critérios 11 em diante continuam deliberadamente pendentes das fatias seguintes.

**Progresso da 5.8.2 em 2026-07-16:** builder, verificador de evidências, renderer, store transacional, hashes no manifest, terminais persistidos e campos aditivos da CLI foram concluídos localmente. Os critérios 11 a 18 receberam implementação e testes; jornada pública, arquitetura consolidada, CI pública e candidata continuam nas fatias seguintes.

**Progresso da 5.8.3 em 2026-07-17:** README foi reduzido a uma entrada de cinco minutos; quickstart instalado, tutorial demo, guia live, interpretação do report e troubleshooting foram criados e reconciliados com CLI/contratos. Os critérios 19 a 24 foram atendidos localmente. Arquitetura/contribuição, verificador documental, CI pública e candidata continuam nas fatias seguintes.

**Progresso da 5.8.4 em 2026-07-17:** arquitetura real, evidência, avaliação, segurança e matriz de linguagens foram reconciliadas com a implementação. Suporte/limitações passou a ter fonte pública única; contribuição, adapter guide, código de conduta e templates foram auditados. Os critérios 25 a 28 foram atendidos localmente. Verificador documental, package audit, job `public-experience` e candidata continuam nas fatias 5.8.5 e 5.8.6.

**Progresso da 5.8.5 em 2026-07-17:** o checker offline passou a validar arquivos/links/anchors, versão, comandos, paths, claims, placeholders e fontes canônicas. O auditor instalado reconciliou doctor, stdout, state, manifest, contrato/schema empacotado, Markdown e hashes fora do checkout. A imagem quality foi corretamente reclassificada como opcional no doctor da demo. O sétimo job `public-experience` foi adicionado sem acoplar os seis existentes. Os critérios 29 e 30 foram atendidos localmente; execução pública, candidata e decisão final continuam na 5.8.6.

**Progresso da 5.8.6 em 2026-07-17:** metadata e fallbacks foram promovidos para `0.1.0a6`; JSON Schema passou a ser executado por validator Draft 2020-12 pinado; walkthrough frio em diretório vazio foi aprovado. Smoke 20/20, Security 12/12, Docker/quality 17/20 com três skips conhecidos, provas Linux 2/2, regressão de 345 testes/33 skips e coverage 85,34% ficaram verdes localmente. Após aprovação humana, o commit `9739c1e` foi enviado à `main` e os sete jobs da CI pública `29597109452` passaram. O fechamento `ddeeb3a` passou novamente nos sete jobs em `29597666988`; a tag e a pré-release `v0.1.0a6` foram publicadas com os dois artifacts auditados. Gate 5 não está autorizado.

## 13. Critérios de aceite

O incremento somente pode ser aprovado quando:

1. `AlphaRunReport 1.0.0` possui contrato neutro e schema público;
2. JSON rejeita fields extras, IDs inválidos, refs quebradas e enums desconhecidas;
3. facts, inferences, recommendations e limitations são coleções semanticamente distintas;
4. toda inference referencia sua base factual e evidência;
5. toda recommendation usa código/template allowlisted;
6. report não inventa relação risco→cenário;
7. requirement, behaviors, risks, scenarios, artifact e attempts possuem IDs estáveis;
8. cenário→artifact→execution/evaluation é rastreável;
9. evidence refs permanecem relativas, hasheadas e com integridade explícita;
10. JSON não contém secret, prompt integral, resposta integral, source do SUT ou environment bruto;
11. Markdown é derivado do contrato validado e não acrescenta fatos;
12. JSON e Markdown reconciliam status, classificação, contagens, usage e limitações;
13. manifest referencia os reports finais por hash;
14. `asef run` produz report em todos os terminais com run persistida;
15. `resume` e `cancel` produzem report terminal coerente;
16. quality evidence aparece sem alterar a classificação funcional;
17. CLI publica paths JSON/Markdown de forma aditiva;
18. report builder e contratos preservam neutralidade do core;
19. README comunica propósito/status em jornada curta;
20. quickstart funciona a partir do wheel em diretório vazio e sem chave;
21. tutorial demo percorre o WF-001 e liga cada etapa ao report;
22. guia live exige secret no host, budget e tarifas explícitas;
23. guia de report cobre as classificações públicas sem prometer causalidade indevida;
24. troubleshooting começa por doctor/exit/classification e não recomenda ações inseguras;
25. arquitetura publicada corresponde ao código atual;
26. support matrix não anuncia ambiente ou perfil sem evidência;
27. contribuição explica fronteiras, testes e criação de adapter/perfil;
28. código de conduta e templates públicos estão coerentes;
29. verificador documental passa offline;
30. job `public-experience` passa e publica somente artifacts sanitizados;
31. Smoke 20/20, Security 12/12, quality e branch coverage >=85% permanecem verdes;
32. source, wheel, sdist, docs e reports passam no secret scan;
33. G5-05, G5-14 e G5-18 recebem links de evidência reproduzível;
34. journal, progresso, baseline, Gate 5 e livro refletem resultados/limitações reais;
35. Lucas revisa o parecer e decide explicitamente sobre conclusão/publicação.

## 14. Critérios de parada

Interromper e revisar o desenho se:

- report precisar executar provider/tooling para ser construído;
- builder precisar ler source, prompt, raw environment ou path arbitrário;
- Markdown possuir semântica não representada no JSON;
- recomendação alterar classificação ou disparar ação;
- inferência não puder apontar para base factual;
- traceability exigir inventar relação ausente;
- report omitir terminal público;
- schema exigir dependência pesada no core;
- package audit depender do checkout;
- quickstart exigir chave, live call ou rede do provider;
- verificador documental depender de crawler externo;
- documentação anunciar suporte não validado;
- troubleshooting recomendar prune, desabilitar controle ou executar código gerado no host;
- o trabalho expandir para dashboard, UI, telemetria, multilíngue, Developer Preview ou Gate 5;
- report/public artifact expuser dado proibido;
- regressões de Smoke, Security, quality, coverage ou cleanup não forem explicadas e corrigidas.

## 15. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Report virar nova fonte de verdade | projeção determinística e reconciliação com state/manifest |
| Contrato excessivamente grande | seções tipadas, limites e escopo somente Alpha Python |
| Separação fato/inferência ser apenas cosmética | tipos distintos, refs obrigatórias e testes adversariais |
| Relações de rastreabilidade fabricadas | links fechados e limitation para relação não observada |
| Markdown divergir do JSON | renderer puro a partir do contrato e golden/parity tests |
| Report falhar justamente em terminais de erro | builder tolera ausência explícita e nunca exige resultado inexistente |
| Evidence hash gerar circularidade | report não referencia seu próprio hash; manifest referencia report após escrita |
| Dados sensíveis vazarem em texto explicativo | fields allowlisted, escaping, truncamento e scanner |
| README e guias divergirem | fontes canônicas, links e verificador de versão/comandos |
| Quickstart ficar específico do checkout | package audit fora do repositório |
| CI duplicar jobs existentes | `public-experience` concentra somente docs/package/report |
| Código de conduta genérico ou incompatível | revisão humana e link claro para enforcement |
| Documentação parecer validação externa | declarar walkthrough roteirizado, não teste com usuário |
| 5.8 absorver o 5.9 | excluir retrospectiva, package do Gate e decisão final |
| Candidata prometer maturidade excessiva | manter `0.1.0a6` pré-alpha e limitações explícitas |

## 16. Evidência esperada ao final

- contrato e schema `AlphaRunReport 1.0.0`;
- matriz de campos, origens e conteúdo proibido;
- fixtures válidas e adversariais de report;
- reports completos para terminais positivos e negativos;
- reconciliação report/state/manifest/evidence;
- quickstart instalado e keyless;
- tutorial demo e guia live;
- guia de interpretação e troubleshooting;
- arquitetura Alpha real;
- support/limitations matrix;
- contribuição, adapter guide e código de conduta;
- verificador documental offline;
- sétimo job `public-experience` verde;
- artifacts sanitizados com retenção de sete dias;
- regressão completa dos sete jobs;
- package isolado, secret scan e parecer final;
- candidata `0.1.0a6` publicada como pré-release após decisão humana.

## 17. Walkthrough frio do 5.8

Antes da revisão final, uma sessão roteirizada começará em diretório vazio e usará somente a documentação publicada:

1. localizar requisitos;
2. instalar o wheel;
3. executar doctor;
4. executar demo;
5. localizar report;
6. responder um checklist factual sobre status, classificação, evidências, limitações e próxima ação;
7. executar cleanup dry-run;
8. localizar como contribuir e reportar vulnerabilidade.

O executor poderá ser o próprio mantenedor ou automação, desde que não use conhecimento fora dos documentos. Esse walkthrough valida consistência operacional, não usabilidade externa. A compreensão por QEs reais continua reservada à Developer Preview.

## 18. Decisões que permanecem humanas

- aprovação deste plano;
- autorização de cada fatia;
- aceite de qualquer mudança incompatível no report;
- autorização de live smoke pago, se considerado necessário;
- aceitação de riscos residuais;
- criação de candidata/tag/release;
- conclusão do 5.8;
- início do 5.9;
- aprovação do Gate 5 ou Etapa 6.
