# Etapa 5 — Plano detalhado do Alpha Python de referência

- **Estado:** vigente; incrementos 5.1 a 5.8 publicados até `v0.1.0a6`; preflight 5.9.2 `NOT_READY`; candidata corretiva local `0.1.0a7` pronta para checkpoint de publicação; Gate 5 pendente
- **Planejado em:** 2026-07-13
- **Pré-condição:** Gate 4 aprovado
- **Decisão registrada:** plano e quatro escolhas centrais aprovados; execução incremental, começando por 5.1

## 1. Resultado esperado

Entregar um Alpha Python instalável e auditável que complete o WF-001 com um SUT existente, gere testes `pytest` em modo demo ou live, execute-os em Docker Desktop, permita no máximo duas correções do teste gerado, use oracle independente, normalize coverage e mutation, produza evidências compreensíveis por um QE e preserve o core independente de Python, `pytest`, Docker e provider.

O Alpha será uma implementação de referência da arquitetura multilíngue, não a definição implícita de que ASEF é uma ferramenta apenas para Python.

## 2. Hipótese da etapa

Se os contratos do walking skeleton forem suficientes, um perfil Python real deve conseguir acrescentar tooling, correção, avaliação e provider live por adapters, sem transferir decisões de workflow ao modelo e sem introduzir conceitos Python no core.

Esta hipótese será refutada se a implementação exigir ramificações Python no runtime, se o oracle não conseguir distinguir erro de teste de possível defeito do SUT ou se o modo live não respeitar os mesmos contratos e budgets do modo demo.

## 3. Entradas e baseline

### Entradas aprovadas

- ADR-001: runtime ASEF controla fluxo, transições, policy e budgets;
- ADR-003: SUT, teste gerado e oracle permanecem independentes;
- ADR-005: gateway direto continua permitido, sem transformar provider em runtime;
- ADR-006: Docker Desktop é o sandbox experimental de referência;
- ADR-008: LangGraph permanece restrito à espera e retomada humana;
- WF-001, schemas `1.1`, capability contracts e QualityContext vigentes;
- Smoke Dataset `SMK-001` a `SMK-010` e Security Dataset `SEC-001` a `SEC-012` já catalogados;
- baseline do Gate 4: 123 testes descobertos, 104 aprovados no core, 19 opt-in, branch coverage de 89%, mutation pilot 13/13 e 11 testes Docker aprovados.

### Lacunas verificadas na implementação atual

- `asef run --mode live` ainda é rejeitado pela CLI pública;
- o gateway live existe como legado experimental, mas não implementa a porta agêntica pública completa;
- a execução atual classifica qualquer exit code funcional como `TEST_FAILURE`;
- `TEST_ERROR` e `SUT_DEFECT_SUSPECTED` estão no desenho do WF-001, mas não no enum público;
- o budget de correção existe, porém não há loop de correção após execução `pytest`;
- coverage e mutation existem apenas como ferramentas de qualidade do próprio ASEF, não como capabilities aplicadas ao SUT;
- o catálogo dos datasets ainda não possui casos executáveis versionados;
- não existe comando público de diagnóstico do ambiente.

## 4. Escopo obrigatório

### Produto

- perfil `python-pytest` com detecção explícita e capabilities declaradas;
- análise, risco, cenários e artifact rastreáveis por identificadores estáveis;
- execução `pytest` em container sem rede e com limites;
- oracle curado e isolado do prompt de geração;
- correção limitada exclusivamente ao teste gerado;
- classificações públicas coerentes para erro de teste, possível defeito no SUT, policy, budget e infraestrutura;
- modo demo integralmente offline e modo live por opção explícita;
- Smoke e Security Datasets executáveis;
- adapters Python de coverage e mutation com resultados normalizados;
- relatórios JSON e Markdown com fatos, inferências e recomendações separadas;
- `asef doctor` para verificar Python, Docker, extra opcional e configuração live sem revelar secrets;
- instalação limpa, CI e pacote de evidências do Gate 5.

### Documentação e experiência open source

- README e quickstart atualizados para o Alpha;
- tutorial completo do WF-001 em demo e guia separado para live;
- arquitetura real, threat model, avaliação, limitações e troubleshooting;
- contribuição, governança e orientação para criar novos perfis sem copiar decisões Python para o core.

### Livro e pesquisa da jornada

- journal factual em cada incremento;
- registro de modelo/IA, tempo em dias, interações estimadas, custo, decisões humanas, retrabalho e falhas;
- notas editoriais incrementais, sem esperar a v1.0;
- retrospectiva do Alpha somente depois das evidências do Gate 5;
- artigo apenas se os resultados sustentarem uma tese clara e reproduzível.

## 5. Fora de escopo

- executar repositórios arbitrários ou código deliberadamente hostil;
- corrigir automaticamente o SUT;
- TypeScript ou Java end-to-end;
- MCP real, interface web ou execução distribuída;
- concorrência multiusuário e múltiplos writers sobre o mesmo checkpoint;
- instalação automática de dependências não aprovadas ou acesso de rede no sandbox;
- benchmark estatístico de qualidade de modelos; dez casos Smoke medem regressão, não desempenho geral;
- promover PydanticAI, LangGraph ou qualquer SDK a autoridade do workflow;
- declarar uso em produção ou segurança absoluta.

## 6. SUT de referência e independência do oracle

### Decisão proposta

Criar uma suíte pública e pequena em `examples/python-alpha/`, composta por funções puras de aritmética e normalização de texto. Ela terá:

- implementação de referência correta para o caminho principal;
- variantes controladas com defeito semeado para provar `SUT_DEFECT_SUSPECTED`;
- requisitos e critérios de aceite versionados;
- manifests e hashes para detectar alteração durante a run;
- zero dependência de runtime além da biblioteca padrão.

Os oracles curados ficarão em fixtures próprias, não serão incluídos no prompt nem no workspace durante geração e só serão materializados na fase de avaliação. Como o repositório é público, “oculto” significa **isolado do componente avaliado**, não confidencial para o leitor do GitHub.

### Regra de interpretação

| Teste gerado | Oracle independente | Classificação/ação |
|---|---|---|
| coleta, sintaxe ou import inválido | não necessário | `TEST_ERROR`; pode corrigir dentro do budget |
| falha e oracle passa no mesmo comportamento | passa | `TEST_ERROR`; evidência indica teste incoerente |
| passa e oracle falha | falha | `SUT_DEFECT_SUSPECTED`; revisão humana |
| falha e oracle confirma divergência do SUT | falha | `SUT_DEFECT_SUSPECTED`; revisão humana |
| ambos passam | passa | candidato a `ACCEPTED` |
| oracle inconclusivo ou infraestrutura falha | inconclusivo | não alegar defeito; classificar a causa comprovável |

Nenhuma classificação de defeito será baseada apenas na opinião do modelo.

## 7. Fronteira do modo live

O modo live implementará `AgenticTestPort` por um adapter próprio e usará o `ModelGateway` como borda de transporte. A mesma aplicação, schemas, validação, policies, budgets e máquina de estados usada pelo demo será preservada.

Regras obrigatórias:

- ativação explícita com `--mode live` e budget positivo;
- credencial somente por variável de ambiente, nunca por argumento, state, evento ou report;
- modelo configurável e sempre registrado com provider, versão retornada, uso e latência;
- chamadas de análise, geração e correção contabilizadas no mesmo budget central;
- retry de provider separado do budget de correção de teste;
- rede permitida apenas ao processo host do provider; container continua sem rede e sem credencial;
- prompt e schema versionados; conteúdo enviado descrito no manifest;
- demo não depende de SDK, rede ou API key;
- indisponibilidade, recusa e output inválido recebem erros normalizados.

Antes de implementar o adapter, a documentação oficial vigente da API será novamente verificada. O plano não congela endpoint, modelo default ou formato de transporte experimental.

## 8. Política de correção limitada

- uma geração inicial e no máximo duas correções;
- somente arquivos produzidos pela skill de teste podem ser substituídos;
- fonte, configuração e dependências do SUT são somente leitura;
- cada tentativa recebe um novo hash e preserva a anterior;
- feedback para correção contém diagnóstico estruturado e trecho sanitizado/truncado, não stdout/stderr ilimitado;
- erro idêntico repetido encerra cedo quando não houver nova evidência;
- provider retry não reinicia o contador de correção;
- esgotamento termina em `BUDGET_EXHAUSTED`, sem fallback silencioso;
- correção bem-sucedida não apaga a falha anterior do audit trail.

## 9. Datasets e validade

### Smoke Dataset

Os dez casos `SMK-001` a `SMK-010` serão materializados em schema versionado, cada um com fixture, expectativa, oracle, modo permitido e critérios de reprodutibilidade.

- todos os dez executam em demo na CI;
- um subconjunto pequeno e declarado poderá executar live sob acionamento manual e teto de custo;
- resultados live não serão tratados como determinísticos;
- `SMK-004` e `SMK-005` exigem esclarecimento/inconclusão, não geração forçada;
- `SMK-006` prova correção limitada;
- `SMK-007` prova suspeita de defeito sem alterar o SUT;
- `SMK-008` prova recuperação ou falha tipada de structured output;
- `SMK-009` e `SMK-010` provam infraestrutura e policy.

### Security Dataset

Todos os doze casos `SEC-001` a `SEC-012` serão automatizados. O Gate 5 exige que todos passem no ambiente de referência; nenhum será convertido em teste meramente informativo. Isso inclui ausência de secrets, bloqueio de rede, path traversal, symlink escape, fork/process storm, memória, timeout, truncamento de output, dependência proibida, prompt injection, Docker socket e artifact superdimensionado.

### Coverage e mutation

- adapters Python produzem schemas neutros, incluindo ferramenta/versão, escopo, totais, exclusões, duração e resultado bruto por referência;
- coverage reporta linha e branch separadamente e não é apresentado como sinônimo de qualidade;
- mutation reporta mortos, sobreviventes, inválidos e timeout;
- fixture de conformance com resultado conhecido valida a normalização;
- baseline do Alpha será publicada, mas não haverá alegação estatística nem threshold universal para projetos externos;
- o budget de mutation limita mutantes e tempo no Alpha;
- a Etapa 6 generaliza esses contratos para outros ecossistemas e compara resultados entre linguagens.

## 10. Observabilidade, evidências e retenção

Cada run deve permitir reconstruir:

- request, contexto resolvido, policy, perfil e skill;
- prompt/schema versions, provider/model e uso, sem secret;
- análise, riscos, cenários e ligações com o teste;
- tentativa inicial e correções, com motivo e hashes;
- container image por digest, comando autorizado, limites e duração;
- resultados gerado/oracle, coverage, mutation e classificação;
- fatos, inferências, recomendações e decisões humanas.

Eventos públicos continuam append-only e logs operacionais continuam JSONL. Saídas são truncadas antes de persistir. O workspace executável é removido ao fim por padrão; artifacts, manifests e resultados sanitizados seguem a política de retenção. Uma opção de debug poderá preservar workspace somente com aviso explícito e nunca na CI pública.

## 11. Incrementos executáveis

### 5.1 — Contratos, ADRs e suíte de referência

**Entregas:**

- formalizar o perfil `python-pytest`, schemas de dataset e resultados coverage/mutation;
- materializar SUT correto, variante defeituosa e oracles isolados do prompt;
- criar ADR sobre interpretação combinada de teste gerado e oracle;
- testar que o core não importa `pytest`, coverage, mutation ou adapter Python.

**Aceite:** fixtures têm hashes estáveis; oracle não aparece no payload de geração; schemas rejeitam campos inválidos; nenhuma alteração funcional no SUT ocorre.

### 5.2 — Adapter `pytest` e normalização

**Entregas:** execução real, parser/normalizador, distinção entre collection error, assertion failure e tooling/infra, raw result por referência.

**Aceite:** fixture conhecida prova contagens e classificações; falha do parser não vira defeito do SUT; Docker permanece sem rede e read-only para a fonte original.

### 5.3 — Oracle e loop de correção

**Entregas:** avaliação combinada, no máximo duas correções, feedback podado, detecção de repetição, tentativas imutáveis e checkpoint humano para suspeita de defeito.

**Aceite:** cenários `TEST_ERROR`, correção aceita, budget esgotado e `SUT_DEFECT_SUSPECTED` passam; teste pode mudar, SUT não; retomada não repete tentativa concluída.

### 5.4 — Adapter live e budgets

**Entregas:** adapter público para análise/geração/correção, configuração segura, erros normalizados, métricas de uso e cassette gravável/sanitizável quando autorizado.

**Aceite:** contract tests usam transporte falso; um teste live manual e barato comprova integração; secret scan passa; demo continua funcionando sem extra, rede ou chave.

### 5.5 — Smoke Dataset executável

**Entregas:** runner, casos `SMK-001` a `SMK-010`, relatório agregado e comparação entre execução e expectativa.

**Aceite:** dez casos demo reproduzíveis; cada falha indica caso, expectativa e evidência; dataset não é apresentado como benchmark estatístico.

### 5.6 — Coverage e mutation do SUT

**Entregas:** adapters Python, budgets, fixtures de conformance e integração ao report.

**Aceite:** totais normalizados conciliam com outputs nativos; timeout/inválido são explícitos; resultados não alteram o SUT original; ausência da capability é informada, não mascarada.

### 5.7 — Segurança, diagnóstico e retenção

**Entregas:** `SEC-001` a `SEC-012`, `asef doctor`, política de cleanup/debug, sanitização e regressão de logs/evidências.

**Aceite:** 12/12 no ambiente de referência; doctor distingue requisito ausente de falha interna; nenhum secret em source, wheel, logs ou artifacts; recursos Docker são removidos.

### 5.8 — Relatórios e experiência pública

**Entregas:** report JSON/Markdown do Alpha, README, quickstart, tutorial demo/live, arquitetura, avaliação, segurança, limitações, troubleshooting e contribuição.

**Aceite:** um QE externo consegue instalar, diagnosticar, executar demo e explicar a classificação usando somente documentação publicada; JSON valida contra schema e Markdown aponta para evidências.

### 5.9 — Avaliação final, livro e Gate 5

**Entregas:** regressão completa, instalação a partir do wheel em diretório vazio, baseline Alpha, pacote de evidências, retrospectiva, lição aprendida e proposta de release.

**Aceite:** todos os critérios G5 possuem evidência ou risco explícito; CI pública passa; decisão continua humana; nenhuma release estável ou início da Etapa 6 ocorre automaticamente.

**Plano detalhado aprovado:** `docs/project/stage-05-increment-59-plan.md`. O desenho separa preflight de sessão externa real, exige consentimento/minimização, impede simulação por IA e torna qualquer nova pré-release condicional a mudança material. A 5.9.1 foi aprovada; o preflight 5.9.2 passou tecnicamente, mas bloqueou o kit por divergência nos documentos da tag. Nenhuma sessão foi iniciada.

## 12. Dependências e ordem

```text
5.1 contratos/SUT
        ↓
5.2 pytest ──→ 5.3 oracle/correção ──→ 5.4 live
        │               │
        └────→ 5.5 Smoke Dataset
                        │
             5.6 coverage/mutation
                        ↓
             5.7 segurança/doctor
                        ↓
             5.8 documentação
                        ↓
             5.9 auditoria/Gate 5
```

5.4 pode começar após os contratos de 5.1, mas só fecha depois de 5.3 para compartilhar budgets e correção. A documentação é atualizada durante todos os incrementos; 5.8 consolida a experiência pública.

## 13. Estratégia de testes e CI

Jobs mínimos:

1. **core:** unitários, contratos, branch coverage e import boundaries sem extras;
2. **python profile:** pytest adapter, normalização, oracle e correção;
3. **workflow opcional:** LangGraph/checkpoint e retomada;
4. **Docker/security:** integração e `SEC-001` a `SEC-012` no ambiente suportado;
5. **datasets:** `SMK-001` a `SMK-010` em demo;
6. **quality capabilities:** coverage e mutation com budgets conhecidos;
7. **package audit:** wheel limpo, instalação fora do checkout, demo sem chave e secret scan;
8. **live manual:** nunca obrigatório em PR e sempre protegido por budget/secret do repositório.

O threshold de branch coverage do core permanece no mínimo em 85%. Mutation do core continua como regressão periódica; mutation do SUT mede a capability e sua baseline, sem impor score universal ao usuário.

## 14. Critérios de parada e rollback

Parar o incremento se:

- qualquer secret for persistido ou enviado ao container;
- o SUT original for alterado;
- o modelo ou adapter controlar transições/retries fora do runtime;
- o oracle entrar no prompt de geração;
- uma falha inconclusiva for rotulada como defeito;
- budgets não interromperem loops;
- o core passar a importar tooling Python.

Rollback preserva schemas públicos compatíveis, mantém o modo demo do Gate 4 e desativa a capability/adaptor incompleto com erro orientativo. Não haverá fallback silencioso para execução no host.

## 15. Riscos principais

| Risco | Tratamento | Evidência exigida |
|---|---|---|
| overfitting aos dez casos Smoke | declarar finalidade de regressão e manter Eval Dataset separado | relatório de validade |
| falso diagnóstico de defeito | oracle curado + estado inconclusivo + revisão humana | casos positivo e negativo |
| custo/loop live | budgets separados, hard stop e teste manual pequeno | eventos de consumo e exaustão |
| parser acoplado ao texto do pytest | preferir resultado estruturado/plugin controlado e guardar raw | conformance fixtures |
| mutation lenta | limite de mutantes/tempo e execução opcional por policy | timeout e baseline |
| perfil Python contaminar core | ports neutras e teste de imports | job core sem extras |
| promessa de segurança excessiva | escopo experimental e Security Dataset público | limitações no report/README |
| documentação competir com código | journal curto por incremento e consolidação em 5.8/5.9 | métricas de esforço editorial |

## 16. Métricas da etapa

- dias corridos por incremento e até o Gate 5;
- interações aproximadas com IA e horas de colaboração;
- modelos/assistentes usados e papel de cada um;
- custo da licença já informado e consumo adicional de API;
- chamadas, tokens e latência por run live;
- correções de teste tentadas, aceitas e esgotadas;
- defeitos/retrabalhos introduzidos ou encontrados com IA;
- pass rate por dataset e estabilidade entre repetições demo;
- overhead Docker, coverage e mutation;
- findings humanos que mudaram uma proposta da IA.

Percentual de ganho de velocidade só será publicado se houver baseline comparável. Caso contrário, a conclusão permanecerá qualitativa e acompanhada dos dados brutos disponíveis.

## 17. Definition of Done

A Etapa 5 só estará pronta para decisão quando:

- 5.1 a 5.9 estiverem concluídos;
- matriz do Gate 5 estiver preenchida com links para evidências;
- instalação limpa e demo offline forem repetidas fora do checkout;
- um live smoke manual, explicitamente orçado, estiver documentado;
- Smoke 10/10 e Security 12/12 passarem no ambiente de referência;
- correção limitada e suspeita de defeito tiverem provas automatizadas;
- reports JSON/Markdown forem consistentes e compreensíveis;
- core permanecer neutro e a CI pública estiver verde;
- baseline, limitações, journal, retrospectiva e lição aprendida estiverem publicados;
- Lucas aprovar ou rejeitar explicitamente o Gate 5.

## 18. Decisão humana

Lucas aprovou em 2026-07-13 o plano e suas quatro escolhas centrais: suíte de SUTs pequenos em vez de um único calculator, oracle isolado do prompt, implementação live atrás de budget explícito e coverage/mutation Python nesta etapa como prova de adapter. A decisão autoriza iniciar o incremento 5.1; não aprova antecipadamente ADRs novos nem o Gate 5.
