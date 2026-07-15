# Planejamento Mestre — Fábrica de Testes Agêntica

> Documento vivo para orientar a construção da aplicação, da documentação pública e do futuro livro.

**Status:** vigente — incrementos 5.1 a 5.4 concluídos localmente; candidata `0.1.0a3` em fechamento, publicação vigente ainda em `0.1.0a2`
**Data de início:** 2026-07-11  
**Responsável:** Lucas  
**Natureza:** projeto open source, educacional, experimental e de portfólio  
**Público principal:** engenheiros de qualidade, profissionais de testes e pessoas interessadas em engenharia de sistemas com IA

---

## 1. Origem e contexto

Este projeto nasceu da intenção de demonstrar, de forma prática e pública, como um engenheiro de qualidade de software pode construir sistemas modernos baseados em IA contextualizada para geracao de automacoes de testes.

Os quatro documentos originais foram preservados em `concepcao/`. Eles representam o marco zero: a primeira visão, a revisão arquitetural, a mudança de uma coleção de agentes para um runtime e os primeiros modelos de registro. Esses documentos são fontes históricas, não a especificação vigente.

Este planejamento consolida o aprendizado obtido até aqui e passa a ser a referência para as próximas etapas. Ele deverá evoluir por decisões registradas e evidências produzidas durante a construção.

## 2. Propósito

Construir em público uma fábrica de testes agêntica robusta, moderna, auditável e educacional, registrando desde a concepção até as versões funcionais:

- decisões e alternativas arquiteturais;
- experimentos com modelos, prompts e frameworks;
- velocidade de construção com apoio de IA;
- resultados, falhas, retrabalho e lições aprendidas;
- práticas de Quality Engineering aplicadas a sistemas não determinísticos;
- participação humana nas decisões e revisões;
- evolução técnica e conceitual do projeto.

O resultado deverá permitir que outros engenheiros de qualidade executem, estudem, critiquem, modifiquem e ampliem a solução.

## 3. Visão do projeto

> Uma plataforma open source educacional e experimental para planejar, gerar, executar, avaliar e aprimorar atividades de teste de software por meio de workflows agênticos, com contratos tipados, execução controlada, aprovação humana e evidências auditáveis.

A plataforma terá arquitetura agnóstica de linguagem. O suporte será construído progressivamente por adaptadores, mas a primeira versão pública deverá demonstrar que o core não está acoplado a um único ecossistema de desenvolvimento.

O projeto será simultaneamente:

1. **Aplicação:** uma fábrica de testes agêntica funcional.
2. **Laboratório:** um ambiente para comparar hipóteses, modelos e abordagens.
3. **Referência educacional:** um repositório que ensina por meio de código, documentação e experimentos reproduzíveis.
4. **Jornada documentada:** a matéria-prima de artigos, palestras e um futuro livro.

## 4. O que o projeto não é

Nesta fase, o projeto não será:

- um produto comercial ou SaaS;
- uma promessa de substituir equipes de qualidade;
- uma plataforma para automatizar todo o SDLC;
- uma coleção de agentes antropomorfizados sem necessidade técnica;
- um benchmark científico universal de LLMs;
- uma solução enterprise pronta para produção;
- um pretexto para acumular frameworks modernos sem benefício demonstrável.

O projeto poderá crescer, mas cada expansão dependerá de evidência, utilidade educacional e capacidade de manutenção.

## 5. Público-alvo

### 5.1 Público principal

- Engenheiros de qualidade e automação de testes.
- QAs que desejam aprender aplicações práticas de IA.
- Líderes de qualidade interessados em avaliação e governança de IA.
- Desenvolvedores de ferramentas internas de engenharia.

### 5.2 Público secundário

- Arquitetos e desenvolvedores interessados em sistemas agênticos.
- Estudantes de engenharia de software.
- Criadores de ferramentas open source para SDLC.
- Pesquisadores e praticantes de LLM evaluation.

## 6. Proposta de valor educacional

Ao estudar o repositório, uma pessoa deverá conseguir entender:

- quando usar uma LLM e quando preferir código determinístico;
- como modelar workflows com estado, loops e critérios de parada;
- como definir contratos de entrada e saída para agentes e skills;
- como executar código gerado com limites e isolamento;
- como avaliar saídas probabilísticas com evidências objetivas;
- como registrar custo, latência, intervenções e falhas;
- como comparar alternativas tecnológicas sem depender de opinião;
- como a IA alterou — ou não — a velocidade e a qualidade da construção.

## 7. Princípios orientadores

### 7.1 Qualidade antes de autonomia

Autonomia só será ampliada quando houver mecanismos para observar, limitar, avaliar e interromper a execução.

### 7.2 Evidência antes de afirmação

Qualidade não será declarada apenas porque um agente produziu uma resposta plausível. Cada conclusão relevante deverá apontar para testes, métricas, artefatos ou decisão humana.

### 7.3 Determinístico sempre que possível

Validação de schema, execução de testes, lint, limites, políticas e cálculos serão implementados por código convencional. LLMs serão usadas onde interpretação, geração ou raciocínio contextual trouxerem benefício.

### 7.4 Humano no controle

Aprovações humanas serão exigidas para ações de maior risco, exportação de alterações e decisões que não possam ser verificadas automaticamente.

### 7.5 Complexidade conquistada

Uma nova tecnologia só entrará após a definição do problema, das opções e do benefício esperado. A escolha deverá ser registrada em experimento ou ADR.

### 7.6 Construção vertical e incremental

Cada incremento ou milestone deverá entregar um fluxo verificável de ponta a ponta antes de expandir capacidades horizontalmente. Uma versão pública poderá consolidar diversos incrementos previamente validados.

### 7.7 Reprodutibilidade

Exemplos, datasets, configurações, prompts versionados e relatórios deverão permitir comparação entre versões dentro dos limites inerentes aos modelos utilizados.

### 7.8 Segurança por padrão

Rede, filesystem, processos, tempo, CPU e memória deverão ser restritos por padrão em qualquer execução de artefato gerado.

### 7.9 Transparência

Limitações, falhas, custos e resultados negativos serão documentados. O objetivo é ensinar o processo real, não produzir uma narrativa artificial de sucesso contínuo.

## 8. Modelo conceitual

Interface (CLI inicialmente)
        │
        ▼
Workflow versionado
        │
        ▼
Runtime de execução
├── estado e checkpoints
├── limites e políticas
├── retries controlados
├── aprovação humana
└── eventos e rastreabilidade
        │
        ▼
Capacidades reutilizáveis
├── nós determinísticos
├── chamadas a modelos
├── skills locais tipadas
└── adaptadores externos/MCP
        │
        ▼
Ambiente isolado
        │
        ▼
Evidências
├── artefatos
├── resultados de testes
├── métricas
├── decisões
└── relatório final

### 8.1 Runtime

Responsável por executar o fluxo, controlar transições, persistir estado, impor limites, interromper ações e emitir eventos. O runtime é infraestrutura; não deve conter regras específicas de um tipo de teste.

### 8.2 Workflow

Define uma sequência versionada de atividades e decisões para resolver um caso de uso. Exemplos futuros: geração de testes, análise de requisitos, bug reproduction e avaliação de regressão.

### 8.3 Agente

Componente que usa um modelo para tomar uma decisão ou gerar uma saída dentro de limites definidos. Um agente não será criado quando uma função determinística resolver o problema.

### 8.4 Skill

Capacidade reutilizável com contrato explícito, como ler um arquivo permitido, aplicar um patch, executar pytest ou coletar cobertura. Skills internas serão interfaces normais; MCP será usado quando interoperabilidade externa justificar o protocolo.

### 8.5 Evidência

Registro verificável gerado pela execução: entrada, versão do workflow, modelo, configuração, chamadas de ferramentas, artefatos, resultados, custo, duração, decisões humanas e status final.

## 9. Mapa inicial de capacidades

O mapa descreve capacidades do domínio, não uma lista obrigatória de agentes.

### 9.1 Análise de requisitos

- identificar comportamentos esperados;
- encontrar ambiguidades;
- extrair restrições;
- propor perguntas de esclarecimento;
- criar rastreabilidade entre requisito e teste.

### 9.2 Análise de risco

- identificar áreas de maior impacto;
- estimar probabilidade e severidade;
- priorizar cenários;
- registrar justificativas.

### 9.3 Design de testes

- gerar cenários positivos, negativos e de fronteira;
- aplicar técnicas de design de testes;
- produzir exemplos BDD quando apropriado;
- verificar redundância e cobertura de requisitos.

### 9.4 Dados de teste

- gerar dados válidos e inválidos;
- respeitar restrições de schema;
- anonimizar ou sintetizar dados;
- assegurar repetibilidade quando necessário.

### 9.5 Geração de automação

- gerar testes a partir de contratos e cenários;
- seguir padrões definidos pelo projeto;
- limitar arquivos e dependências alterados;
- validar sintaxe e estrutura antes da execução.

### 9.6 Execução controlada

- executar testes em ambiente isolado;
- impor timeout e limites de recursos;
- capturar logs e artefatos;
- classificar erros de infraestrutura, produto e teste.

### 9.7 Análise de falhas

- resumir evidências;
- levantar hipóteses;
- diferenciar falha de teste de possível defeito;
- recomendar próxima ação sem ocultar incerteza.

### 9.8 Avaliação da qualidade

- medir cumprimento dos requisitos;
- executar testes ocultos quando aplicável;
- coletar cobertura e mutation score;
- comparar versões de prompt, modelo e workflow;
- registrar violações de política e intervenções humanas.

### 9.9 Relatórios

- produzir relatório legível e representação estruturada;
- relacionar requisitos, cenários, testes e resultados;
- exibir limitações, custo, duração e confiança;
- permitir auditoria da execução.

### 9.10 Contexto operacional de Quality Engineering

- representar o perfil profissional e as fronteiras de aprovação do QA sem armazenar dados pessoais desnecessários;
- registrar objetivos, riscos, compliance e convenções da equipe;
- descrever sistemas, fluxos críticos, ambientes, SLOs e owners;
- referenciar repositórios com escopos independentes de leitura e escrita;
- selecionar skills de web UI/WebView, backend/API, mobile, unitários, mutation e performance;
- autorizar MCPs e operações por contexto, skill e política;
- aplicar regras de provider, modelo, classificação de dados e budget;
- persistir snapshot sanitizado e versionado do contexto efetivo de cada run.

O `QualityContext` será entrada não confiável até validação. Secrets serão apenas referências resolvidas pelo host. Conteúdo do SUT não poderá alterar políticas, permissões ou precedência de instruções.

## 10. Primeiro workflow vertical de referência

### 10.1 Caso de uso

Receber uma especificação estruturada e uma função Python pura existente, analisar riscos e critérios, gerar cenários e testes, executar validações em ambiente isolado, realizar correção limitada dos testes e produzir um relatório de evidências.

Python será usado como primeira referência para validar o fluxo de ponta a ponta, e não como limite do produto. O mesmo contrato deverá ser posteriormente implementado em outros ecossistemas para provar que runtime, workflow, evidências e políticas permanecem independentes da linguagem.

Quando o projeto gerar também a implementação, ela será tratada como SUT sintético para laboratório. A implementação, os testes gerados e o oracle de avaliação terão responsabilidades separadas. Testes ocultos e oracles não poderão ser derivados apenas da mesma geração usada para criar o SUT.

### 10.2 Restrições do primeiro incremento técnico

- somente Python;
- somente funções pequenas e sem efeitos colaterais externos;
- workspace temporário e descartável;
- `pytest` como test runner;
- sem acesso de rede durante a execução;
- dependências previamente permitidas;
- sem alteração automática de repositório real;
- no máximo duas tentativas de correção;
- aprovação humana antes de exportar artefatos;
- um provider de modelo inicialmente.

Essas restrições pertencem ao walking skeleton e aos primeiros alphas internos. Elas não definem o escopo da `v0.1` pública.

### 10.3 Fluxo esperado

Especificação
    ↓
Validação determinística
    ↓
Análise de requisito, SUT e risco
    ↓
Design de cenários
    ↓
Geração de testes
    ↓
Validação estática
    ↓
Execução isolada
    ↓
Avaliação das evidências
    ├── sucesso → relatório
    ├── falha do teste corrigível → feedback → nova tentativa
    ├── possível defeito no SUT → evidência → revisão humana
    └── falha final/violação → relatório de falha
    ↓
Aprovação humana para exportação

### 10.4 Critério de conclusão do workflow de referência

Uma instalação limpa deverá conseguir executar o dataset inicial, registrar as transições, impedir ações fora da política e produzir relatórios que permitam explicar por que cada caso passou ou falhou.

### 10.5 Estratégia multilíngue

O core deverá depender de capacidades abstratas, e não de comandos específicos de Python. Não haverá um `LanguageAdapter` monolítico: perfis de linguagem serão compostos por adaptadores menores para descoberta, dependências, build, análise estática, testes, cobertura, mutação e normalização.

Prioridade inicialmente proposta:

1. **Python:** referência inicial e ecossistema natural de IA e automação.
2. **TypeScript:** validação em Node.js e aplicações web.
3. **Java:** validação em ecossistema corporativo com build e ferramentas distintas.
4. **Go ou .NET:** candidato posterior para testar a extensibilidade do contrato.

A seleção final das três primeiras linguagens será confirmada na Etapa 1 com critérios de relevância comunitária, diversidade de tooling, custo de manutenção e valor educacional.

Conformidade entre linguagens validará invariantes contratuais, não código ou resultados textuais idênticos. A especificação normativa está em `docs/architecture/language-adapters.md`.

## 11. Estratégia de arquitetura e tecnologia

### 11.1 Decisões iniciais

- Runtime implementado inicialmente em Python.
- Contratos de domínio, workflows e evidências independentes da linguagem do sistema sob teste.
- Suporte progressivo por `LanguageProfile` composto por adaptadores de capacidade.
- CLI como primeira interface.
- Schemas tipados para entradas, saídas, eventos e evidências.
- Testes automatizados desde o primeiro incremento.
- Prompts, workflows e datasets versionados.
- Execução isolada obrigatória para código gerado.
- Avaliação, segurança e observabilidade presentes antes da v0.1 pública.
- JSONL como formato inicial de eventos e evidências.
- Técnicas avançadas de QE preservadas no escopo e introduzidas por precondições técnicas.

### 11.2 Hipóteses a validar

- Máquina de estados Python explícita como baseline de comparação.
- LangGraph como candidato a engine de workflow e persistência, avaliado contra a baseline.
- PydanticAI como candidato a abstração para agentes tipados, avaliado separadamente da engine.
- Pydantic para todos os contratos centrais.
- OpenTelemetry para padronização futura de traces e métricas quando JSONL deixar de ser suficiente.
- DeepEval ou alternativa para parte da avaliação não determinística.
- Containers como mecanismo inicial de isolamento.
- MCP para integrações externas em versões posteriores.

### 11.3 Decisões adiadas

- Interface web.
- Extensão para VS Code.
- Memória vetorial e RAG.
- Memória de longo prazo entre execuções.
- Redis, PostgreSQL e serviços distribuídos.
- Jira, Slack, Confluence e integrações equivalentes.
- Suporte simultâneo a vários providers.
- Deploy multiusuário ou enterprise.
- Adoção definitiva de LangGraph.
- Adoção definitiva de PydanticAI.
- Instrumentação OpenTelemetry no walking skeleton.

### 11.4 Fronteiras de controle

Até que os spikes indiquem uma alternativa melhor, será aplicada a seguinte separação:

- **Workflow:** define estados, transições possíveis, critérios de parada e pontos de aprovação.
- **Runtime:** aplica transições, controla orçamento, persiste eventos e impõe políticas.
- **Agente:** produz análise, decisão ou artefato tipado; não controla sozinho o loop principal.
- **Skill:** executa uma capacidade limitada por contrato e política.
- **Adaptador:** traduz diferenças de linguagem, ferramenta, provider ou protocolo.

Um framework não poderá introduzir um segundo loop de controle concorrente sem que isso seja explicitamente avaliado e registrado.

### 11.5 Regra de adoção

Antes de incluir uma tecnologia, registrar:

1. problema observado;
2. hipótese de benefício;
3. alternativas consideradas;
4. experimento mínimo;
5. critérios de comparação;
6. resultado;
7. decisão e consequências.

## 12. Segurança e limites

A segurança será tratada como componente estrutural, não como agente futuro. Docker Desktop foi escolhido como ambiente inicial de containers, com Windows e backend WSL2 como ambiente de referência. Outros hosts só serão anunciados após validação explícita.

Código gerado, respostas de modelos, requisitos, repositórios e dependências externas serão tratados como entradas não confiáveis. `subprocess` não será considerado sandbox, e bloqueios de imports não serão tratados como fronteira de segurança.

Os controles obrigatórios abrangem isolamento externo, privilégio mínimo, rede desabilitada por padrão, workspace efêmero, budgets de recursos e custo, proteção de credenciais, sanitização e testes adversariais. A especificação normativa está em `docs/quality/security-strategy.md`.

## 13. Estratégia de Quality Engineering para IA

A estratégia preserva testes unitários, contratos, transições, integração, golden tests, regressão de prompts, avaliação por datasets, coverage, mutation testing, testes metamórficos, segurança e avaliação humana. As técnicas serão introduzidas conforme suas precondições, sem serem retiradas da visão.

Smoke, Development, Evaluation, Holdout, Adversarial/Security e Language Conformance Datasets terão finalidades e controles de exposição distintos. Oracles e testes ocultos deverão ser independentes da geração avaliada sempre que possível. LLM-as-a-judge não será a única evidência para critérios objetivamente verificáveis.

Toda métrica exigirá definição operacional, ground truth apropriado e limitações declaradas. A especificação normativa está em `docs/quality/evaluation-strategy.md`.

## 14. Observabilidade e evidências

Observabilidade será capacidade transversal do runtime, não um agente independente.

Cada execução produzirá eventos correlacionáveis, manifest versionado, artefatos, resultados, métricas e relatório. O manifest deverá registrar hashes de workflow, prompts e datasets, versão do modelo, parâmetros, adaptadores, dependências, ambiente e digest da sandbox.

Dados sensíveis e conteúdo integral de prompts não serão publicados automaticamente. A especificação normativa está em `docs/architecture/evidence-model.md`.

## 15. Estratégia de experimentação

Experimentos serão pequenos, comparáveis e documentados com pergunta, hipótese, contexto, opções, dataset, métricas, procedimento, resultado, limitações e decisão.

As primeiras comparações incluem máquina de estados versus LangGraph, chamada direta versus PydanticAI, structured output, avaliação própria versus framework e JSONL versus OpenTelemetry. Processo local poderá ser usado como baseline funcional, mas não será comparado a container como fronteira de segurança equivalente.

Não serão alteradas várias dimensões simultaneamente sem desenho experimental que permita interpretar o resultado. O catálogo e os relatórios ficarão em `docs/experiments/`.

## 16. Métricas da jornada de construção com IA

O projeto deverá medir não apenas o produto, mas o próprio processo de construção.

### 16.1 Esforço e velocidade

- horas humanas por sessão e milestone;
- tempo dedicado a concepção, implementação, teste, documentação e correção;
- lead time entre hipótese, experimento, decisão e release;
- estimativa inicial versus duração real;
- retrabalho por etapa.

### 16.2 Uso de IA

- ferramenta, provider e modelo usados;
- objetivo de cada interação relevante;
- quantidade aproximada de interações;
- custo estimado;
- artefatos propostos pela IA;
- artefatos aceitos, revisados e descartados;
- defeitos introduzidos por sugestões de IA;
- decisões alteradas após revisão humana;
- situações em que conhecimento profissional prevaleceu sobre a sugestão.

### 16.3 Qualidade do processo

- defeitos encontrados antes e depois de cada release;
- decisões revertidas;
- hipóteses confirmadas ou rejeitadas;
- documentação desatualizada detectada;
- cobertura de critérios do milestone;
- feedback de usuários externos.

Linhas de código geradas não serão usadas como indicador principal de produtividade.

## 17. Estratégia de documentação

### 17.1 Tipos de documento

| Tipo | Finalidade | Frequência |
|---|---|---|
| Visão e roadmap | Orientar o projeto | Revisão por milestone |
| ADR | Registrar decisão arquitetural relevante | Quando houver decisão |
| Experimento | Testar hipótese com evidência | Quando houver comparação |
| Journal | Registrar fatos e esforço | Por sessão relevante |
| Lição aprendida | Consolidar reflexão | Ao final de milestone |
| Tutorial | Ensinar uso e extensão | A partir da v0.1 |
| Referência | Explicar APIs, schemas e configuração | Junto da implementação |
| Release notes | Comunicar mudanças e resultados | Por release |

### 17.2 Autoridade documental

O Planejamento Mestre é autoridade para propósito, princípios, milestones e gates. ADRs aceitos prevalecem em decisões arquiteturais; especificações especializadas prevalecem nos detalhes de seu domínio. Revisões, experimentos, journals e documentos de concepção não alteram decisões automaticamente.

A hierarquia completa, a regra de precedência e o mapa de documentos estão em `docs/GOVERNANCA_DOCUMENTAL.md`.

## 18. Estratégia do livro

O livro emergirá da construção com journals factuais, reflexões contemporâneas, retrospectivas e capítulos vivos. Seu índice será provisório e não dirigirá artificialmente a arquitetura. Código e evidências terão prioridade quando houver conflito de capacidade.

A tese, o método, o ritmo e a linha editorial provisória estão em `book/README.md`.

## 19. Estratégia open source

O projeto terá instalação reproduzível nos ambientes oficialmente suportados, diagnóstico pela CLI, modo demo gravado, modo live, níveis de suporte explícitos, documentação de contribuição, segurança, CI e releases versionadas.

Uma developer preview com 3–5 engenheiros de qualidade ocorrerá antes do hardening final da v0.1. A estratégia detalhada está em `docs/project/open-source-strategy.md`.

## 20. Política de versões e maturidade

A `v0.1` não será definida como o menor artefato publicável. Ela será a primeira versão pública robusta que representa adequadamente a visão educacional e técnica. Antes dela, o projeto usará protótipos, spikes, milestones e alphas, que poderão ser versionados sem serem apresentados como produto pronto.

Concepção e especificação
        ↓
Spikes descartáveis
        ↓
Walking skeleton
        ↓
Alpha Python de referência
        ↓
Alpha multilíngue
        ↓
Avaliação avançada
        ↓
Developer preview
        ↓
Hardening
        ↓
v0.1 pública robusta
        ↓
Validação comunitária
        ↓
Evolução até v1.0

### 20.1 Critérios mínimos pretendidos para v0.1

| Capacidade | Obrigatoriedade | Evidência mínima |
|---|---|---|
| Contratos independentes da linguagem do SUT | Obrigatória | Conformance suite com mais de uma linguagem |
| Python end-to-end | Obrigatória | Perfil de referência e suite aprovada |
| TypeScript end-to-end | Obrigatória | Perfil suportado e suite aprovada |
| Terceira linguagem | Experimental obrigatória | Capability matrix e alpha executável |
| Extensão por adaptadores compostos | Obrigatória | Contratos e tutorial validados por terceiro |
| Workflow seguro e auditável | Obrigatória | Evidências, políticas e testes de transição |
| Datasets separados | Obrigatória | Smoke, Evaluation, Holdout, Security e Conformance catalogados |
| Sandbox Docker Desktop | Obrigatória | Testes adversariais no ambiente de referência |
| Budgets e critérios de parada | Obrigatória | Testes automatizados de limite e cancelamento |
| Modo demo e modo live | Obrigatória | Execuções documentadas e distinguíveis |
| Relatórios Markdown e estruturado | Obrigatória | Revisão de compreensão na developer preview |
| Instalação e diagnóstico | Obrigatória | Teste limpo no ambiente oficialmente suportado |
| Release reproduzível | Obrigatória | Artefatos, hashes, lockfiles e manifest completos |
| Coverage e mutation testing | Obrigatória nas linguagens suportadas | Relatório normalizado e limitações documentadas |
| Testes metamórficos | Condicional | Ao menos um caso válido ou decisão justificada de inaplicabilidade |
| OpenTelemetry | Opcional | Somente se o spike demonstrar benefício sobre JSONL |

Itens obrigatórios não admitem exceção no Gate da v0.1. Itens condicionais exigem evidência de aplicabilidade ou inaplicabilidade; itens experimentais e opcionais devem ter seu nível de suporte publicado.

## 21. Roadmap por etapas e gates

As datas serão estimadas após a baseline das primeiras sessões. Os gates são mais importantes do que prazos artificiais.

### Etapa 0 — Marco zero e preservação histórica

**Objetivo:** registrar corretamente a origem e preparar o sistema de acompanhamento.

**Aplicação**

- nenhuma implementação funcional nesta etapa;
- definir a terminologia inicial.

**Documentação**

- preservar os quatro esboços em `concepcao/`;
- criar este planejamento mestre;
- criar a linha do tempo do marco zero;
- registrar ferramentas e IAs já utilizadas;
- criar templates separados de journal, experimento, ADR e lição;
- definir a baseline inicial em dias e custos diretos;
- criar uma visão resumida de uma página.

**Livro**

- registrar a motivação pessoal;
- escrever notas factuais sobre o nascimento da ideia;
- registrar expectativas antes do primeiro código.

**Gate 0**

- [x] É possível explicar em uma página por que o projeto existe?
- [x] O público-alvo e o resultado educacional estão claros?
- [x] A história original foi preservada sem ser confundida com o plano vigente?
- [x] O método de medição da jornada está definido?

**Decisão:** Etapa 0 aprovada pelo responsável em 2026-07-11. Registro: `docs/project/gates/gate-00-marco-zero.md`.

### Etapa 1 — Visão, domínio e escopo

**Objetivo:** transformar a intenção em uma especificação compreensível por terceiros.

**Aplicação**

- mapear capacidades da fábrica;
- priorizar casos de uso;
- selecionar o primeiro workflow vertical;
- definir requisitos de independência de linguagem;
- priorizar os primeiros ecossistemas e seus adaptadores.

**Documentação**

- `product_vision.md`;
- glossário;
- personas leves;
- mapa de capacidades;
- escopo e não escopo;
- requisitos funcionais e atributos de qualidade dos alphas e da v0.1 robusta;
- matriz inicial de linguagens, test runners, build, cobertura e mutation engines;
- riscos e premissas.

**Livro**

- rascunhar a motivação;
- registrar a mudança de fábrica de software para fábrica de testes;
- documentar como a revisão humana alterou a proposta inicial da IA.

**Gate 1**

- [x] Um QE externo entenderia o projeto sem explicação verbal?
- [x] O primeiro workflow resolve um problema de qualidade concreto?
- [x] O primeiro incremento cabe em uma implementação vertical pequena sem reduzir a visão multilíngue?
- [x] Os contratos propostos evitam acoplamento a Python?
- [x] Os principais termos possuem definição única?

**Decisão:** Etapa 1 aprovada pelo responsável em 2026-07-11. Registro: `docs/project/gates/gate-01-visao-dominio-escopo.md`.

### Etapa 2 — Contratos, workflow e estratégia de avaliação

**Objetivo:** especificar o comportamento antes de escolher toda a implementação.

**Aplicação**

- desenhar estados, nós, transições e critérios de parada;
- definir schemas de entrada, saída, eventos e evidências;
- definir interfaces das primeiras skills;
- definir contratos de `LanguageProfile` e adaptadores compostos por capacidade;
- especificar sandbox em Docker Desktop, políticas e matriz de ambientes;
- criar Smoke Dataset, plano do Eval Dataset e Language Conformance Dataset inicial.

**Documentação**

- diagrama e especificação do workflow;
- ADR de separação entre runtime, workflow, agente e skill;
- threat model inicial;
- estratégia de testes e avaliação;
- catálogo do dataset;
- critérios de aceite dos alphas e da v0.1 robusta.

**Livro**

- registrar como conceitos tradicionais de QA foram adaptados;
- documentar dúvidas, alternativas e previsões antes dos experimentos.

**Gate 2**

- [x] Cada transição possui condição clara?
- [x] Retries e encerramento são limitados?
- [x] As evidências necessárias estão especificadas?
- [x] O dataset contém sucesso, falha, ambiguidade e abuso?
- [x] Há casos equivalentes planejados para validar mais de uma linguagem?
- [x] A fronteira de segurança está explícita?

**Decisão:** Etapa 2 aprovada pelo responsável em 2026-07-11. Registro: `docs/project/gates/gate-02-contratos-workflow-avaliacao.md`.

### Etapa 3 — Spikes arquiteturais

**Objetivo:** validar escolhas tecnológicas com implementações descartáveis ou mínimas.

**Aplicação**

- implementar uma máquina de estados Python explícita como baseline;
- comparar LangGraph com a baseline usando o mesmo workflow e dataset;
- comparar chamadas diretas ao provider com PydanticAI somente após a decisão sobre a engine;
- experimentar structured output;
- experimentar persistência e retomada;
- experimentar captura de evidências.
- experimentar isolamento sem tratar `subprocess` ou bloqueio de imports como sandbox.

**Documentação**

- relatório por experimento;
- ADR apenas para decisões efetivamente tomadas;
- matriz de decisão atualizada;
- riscos descobertos.

**Livro**

- registrar previsões versus resultados;
- capturar exemplos de sugestões úteis e incorretas da IA;
- medir esforço e retrabalho dos spikes.

**Gate 3**

- [x] A stack mínima foi escolhida com evidência?
- [x] O isolamento bloqueia comportamentos proibidos do dataset no ambiente experimental?
- [x] É possível persistir e explicar uma execução?
- [x] Tecnologias sem benefício demonstrado foram removidas ou adiadas?
- [x] LangGraph e PydanticAI foram avaliados separadamente?
- [x] Está claro quem controla o loop principal de execução?

**Status:** concluída e aprovada em 2026-07-12. ADR-004, ADR-005 e ADR-006 aceitas; Etapa 4 autorizada. Registro: `docs/project/gates/gate-03-spikes-arquiteturais.md`.

### Etapa 4 — Walking skeleton

**Objetivo:** executar o caminho completo com a menor funcionalidade possível.

**Plano executável:** `docs/project/stage-04-walking-skeleton-plan.md`.

**Aplicação**

- criar CLI mínima;
- validar input;
- executar um nó com LLM;
- gerar artefato em workspace temporário;
- executar uma validação determinística;
- emitir eventos;
- produzir relatório de sucesso ou falha.
- carregar e validar um `QualityContext` mínimo;
- selecionar ao menos uma skill compatível com o sistema;
- persistir snapshot sanitizado do contexto, skill, modelo e políticas usados.

**Documentação**

- guia de execução para desenvolvedor;
- arquitetura real do skeleton;
- primeira referência dos schemas;
- limitações conhecidas.
- tutorial do contexto mínimo de QA/equipe/sistema;

**Livro**

- registrar tempo entre concepção e primeiro fluxo completo;
- comparar expectativa e implementação real;
- escrever a retrospectiva do primeiro incremento.

**Gate 4**

- [ ] Uma execução completa pode ser reproduzida?
- [ ] É possível explicar por que ela passou ou falhou?
- [ ] Falhas de infraestrutura são distinguíveis das funcionais?
- [ ] Nenhuma etapa essencial depende apenas de logs informais?
- [ ] É possível explicar qual contexto, skill, MCP/model policy e aprovação orientaram a run?

**Status:** concluída e aprovada em 2026-07-13. 4.R1 a 4.R8 implementados; coverage, mutation pilot, observabilidade, material editorial, regressão local e CI pública aprovados. Os riscos residuais foram aceitos por Lucas. Registro: `docs/project/gates/gate-04-evidence-package.md`.

### Etapa 5 — Alpha Python de referência

**Objetivo:** completar o primeiro workflow em Python sem confundi-lo com o escopo final da plataforma.

**Plano executável:** `docs/project/stage-05-alpha-python-plan.md`

**Plano de aceite:** `docs/project/gates/gate-05-acceptance-plan.md`
**Status:** 5.1, 5.2 e 5.3 concluídos e publicados. A ADR-009 foi aceita. O 5.3 passou pela segunda revisão técnica após correção de sete findings e pelos três jobs da CI pública; permanece sem integração à CLI pública.

**Aplicação**

- implementar o workflow completo;
- suportar correção limitada;
- executar os datasets iniciais;
- incluir modo mock/demo;
- criar relatório Markdown e JSON;
- adicionar testes do runtime, skills, políticas e workflow;
- automatizar verificações em CI.

**Documentação**

- README público;
- quickstart;
- tutorial do primeiro workflow;
- explicação arquitetural;
- estratégia de avaliação;
- baseline experimental do alpha;
- política de segurança;
- contribuição e governança básicas.

**Livro**

- produzir retrospectiva do alpha Python;
- consolidar métricas da construção;
- transformar resultados relevantes em artigo quando houver evidência suficiente.

**Gate 5**

- [ ] Uma instalação limpa funciona no ambiente de referência?
- [ ] O modo demo funciona sem credenciais?
- [ ] O relatório é compreensível por um QE?
- [ ] Os resultados e limitações do alpha estão registrados?
- [ ] O core permaneceu desacoplado de pytest e Python?

### Etapa 6 — Alpha multilíngue e técnicas avançadas de QE

**Objetivo:** provar a arquitetura com ecossistemas distintos e aprofundar a avaliação de qualidade.

**Aplicação**

- implementar o perfil TypeScript e seus adaptadores de capacidade;
- implementar ou experimentar o perfil Java e seus adaptadores de capacidade;
- executar casos equivalentes entre linguagens;
- expandir coverage e mutation, iniciados no perfil Python, para os adapters TypeScript/Java e comparar a normalização entre ecossistemas;
- introduzir testes metamórficos onde houver relações válidas;
- ampliar testes adversariais da sandbox;
- evoluir o Eval Dataset de forma estratificada.

**Documentação**

- guia de criação de adaptadores;
- matriz comparativa dos ecossistemas;
- relatórios de conformidade entre linguagens;
- estratégia e resultados das técnicas avançadas;
- limitações específicas de cada tooling.

**Livro**

- registrar como a segunda linguagem confirmou ou refutou a arquitetura;
- documentar diferenças entre teoria e prática nas técnicas avançadas;
- produzir retrospectivas por milestone.

**Gate 6**

- [ ] O mesmo workflow funciona em Python e TypeScript?
- [ ] Adicionar a segunda linguagem exigiu mudanças indevidas no core?
- [ ] A terceira linguagem possui caminho comprovado ou alpha funcional?
- [ ] Mutation e demais técnicas produzem evidência útil, não apenas métricas decorativas?
- [ ] Datasets distinguem regressão rápida, benchmark e segurança?

### Etapa 7 — Developer preview

**Objetivo:** validar instalação, compreensão, utilidade e extensibilidade com 3–5 engenheiros de qualidade antes da v0.1.

**Aplicação**

- distribuir uma versão alpha identificada como experimental;
- acompanhar instalação e primeira execução em ambiente limpo;
- coletar falhas de usabilidade, segurança percebida e compreensão dos relatórios;
- observar a criação ou modificação de ao menos um adaptador ou exemplo;
- priorizar correções por severidade e recorrência.

**Documentação**

- roteiro da developer preview;
- consentimento e política de coleta de feedback;
- relatório anonimizado dos resultados;
- backlog rastreável de findings e decisões.

**Livro**

- registrar diferenças entre a intenção do autor e a experiência real;
- preservar críticas, surpresas e mudanças de direção.

**Gate 7**

- [ ] Entre 3 e 5 QEs tentaram instalar e executar o projeto?
- [ ] Os principais pontos de atrito foram registrados e classificados?
- [ ] Findings críticos e altos foram resolvidos ou bloquearam corretamente a continuidade?
- [ ] Os relatórios foram compreendidos sem explicação individual do autor?

### Etapa 8 — Hardening e v0.1 pública robusta

**Objetivo:** preparar uma versão pública que represente adequadamente a visão do projeto.

**Aplicação**

- corrigir lacunas encontradas nos alphas;
- endurecer sandbox, budgets e políticas;
- estabilizar contratos e adaptadores;
- implementar diagnóstico de ambiente;
- validar modo demo, live e benchmark;
- automatizar verificações e empacotamento.

**Documentação**

- README público;
- quickstart e troubleshooting;
- tutoriais multilíngues;
- arquitetura e extensão por adaptadores;
- benchmark v0.1;
- política de segurança, contribuição e governança;
- release notes e limitações explícitas.

**Livro**

- produzir retrospectiva da v0.1;
- consolidar métricas desde o marco zero;
- revisar capítulos vivos sem antecipar conclusões futuras.

**Gate 8 — v0.1**

- [ ] Todos os critérios obrigatórios da Seção 20.1 foram atendidos?
- [ ] Itens condicionais possuem evidência de aplicabilidade ou inaplicabilidade?
- [ ] Uma pessoa externa consegue instalar e executar sem assistência?
- [ ] O modo demo funciona sem credenciais e está diferenciado do modo live?
- [ ] Os resultados, limitações e riscos estão publicados?
- [ ] A release é reproduzível?

### Etapa 9 — Validação com a comunidade

**Objetivo:** substituir suposições internas por feedback de usuários reais.

**Aplicação**

- corrigir problemas de instalação e usabilidade;
- instrumentar feedback opcional e respeitoso à privacidade;
- melhorar extensibilidade a partir de casos reais.

**Documentação**

- roteiro de avaliação externa;
- issues de feedback;
- FAQ;
- registro de decisões motivadas pela comunidade.

**Livro**

- documentar diferenças entre intenção do autor e uso real;
- registrar críticas, contribuições e mudanças de direção.

**Gate 9**

- [ ] Pelo menos três pessoas externas tentaram executar o projeto?
- [ ] Os principais pontos de atrito foram registrados?
- [ ] Há evidência para escolher a próxima capacidade?

### Etapa 10 — Evolução incremental até v1.0

**Objetivo:** ampliar a fábrica por perguntas de engenharia, não por uma lista fixa de agentes.

Possíveis perguntas de versão:

- agentes especializados melhoram o design de testes?
- MCP aumenta a extensibilidade de integrações reais?
- memória entre execuções melhora resultados sem contaminação?
- múltiplos modelos reduzem custo mantendo qualidade?
- mutation testing detecta testes gerados superficialmente?
- o workflow consegue operar com segurança em repositório real?
- novos tipos de workflow podem ser adicionados como plugins?
- o sistema funciona de forma confiável em CI?

Cada nova versão deverá declarar hipótese, baseline, mudança, resultado, limitações e decisão.

**Gate para v1.0**

- [ ] A arquitetura suporta mais de um workflow sem duplicação estrutural?
- [ ] Um colaborador consegue criar uma extensão documentada?
- [ ] Segurança, avaliação e observabilidade possuem testes próprios?
- [ ] A instalação e os exemplos são estáveis?
- [ ] Existe histórico suficiente para explicar a evolução por evidências?

## 22. Backlog inicial priorizado

### Agora — Etapa 0

1. Pacote documental revisado e aprovado.
2. Quatro critérios do Gate 0 verificados e atendidos.
3. Etapa 0 formalmente encerrada em 2026-07-11.

### Em seguida — Etapa 1

1. Criar a visão de produto em uma página.
2. Definir personas e necessidades.
3. Refinar mapa de capacidades.
4. Priorizar casos de uso.
5. Especificar o primeiro workflow vertical.
6. Confirmar nome do projeto e terminologia pública.
7. Definir requisitos de independência de linguagem.
8. Selecionar os três primeiros ecossistemas por critérios explícitos.
9. Desenhar os contratos iniciais de `LanguageProfile` e adaptadores por capacidade.

### Não iniciar ainda

- scaffold completo da aplicação;
- instalação de todos os frameworks candidatos;
- interface web;
- extensão VS Code;
- memória de longo prazo;
- integrações MCP externas;
- suporte multi-provider;
- adoção definitiva de LangGraph ou PydanticAI antes dos spikes;
- capítulos apresentados como definitivos sobre acontecimentos ainda não ocorridos.

## 23. Governança de decisões

### 23.1 Responsabilidade

Lucas é o responsável final por visão, prioridades e decisões. A IA atua como parceira de análise, geração, revisão e implementação, sem substituir julgamento profissional.

### 23.2 Estados de uma decisão

- **Proposta:** levantada, ainda sem avaliação.
- **Em experimento:** possui hipótese e teste em andamento.
- **Aceita:** aprovada e registrada.
- **Rejeitada:** avaliada e descartada com justificativa.
- **Adiada:** válida, mas desnecessária no momento.
- **Superada:** anteriormente aceita, substituída por nova evidência.

### 23.3 Gate review

Ao final de cada etapa será feita uma revisão contendo:

- entregáveis concluídos e pendentes;
- métricas planejadas versus reais;
- riscos novos;
- decisões tomadas ou revertidas;
- lições aprendidas;
- recomendação de continuar, ajustar, repetir ou interromper;
- aprovação explícita do responsável antes da próxima etapa.

A autoridade e precedência entre ADRs, Planejamento Mestre, especificações, revisões, journals e documentos históricos são normatizadas por `docs/GOVERNANCA_DOCUMENTAL.md`.

## 24. Riscos principais

| Risco | Probabilidade | Impacto | Resposta inicial |
|---|---:|---:|---|
| Escopo crescer sem respeitar dependências | Alta | Alto | Milestones, adaptadores progressivos e gates |
| Stack escolhida por tendência | Alta | Médio | Spikes e regra de adoção |
| Documentação atrasar o código | Média | Alto | Walking skeleton cedo e docs proporcionais |
| Código gerar risco ao ambiente | Alta | Alto | Sandbox e políticas antes da autonomia |
| Livro competir com o produto | Média | Alto | Escrita proporcional, índice provisório e prioridade às evidências |
| Métricas sem definição válida | Média | Médio | Definição operacional e ground truth |
| Custo de modelos | Média | Médio | Dataset pequeno, cache/mock e medição |
| APIs e frameworks mudarem | Alta | Médio | Adaptadores, versões fixadas e ADRs |
| Resultados não reproduzíveis | Alta | Médio | Manifests, seeds quando possíveis e datasets |
| Falta de usuários externos | Média | Alto | Quickstart, demo e validação comunitária |
| Exposição acidental de dados | Média | Alto | Sanitização, política de publicação e revisão |
| Narrativa enviesada pelo sucesso | Média | Médio | Publicar falhas, limitações e decisões revertidas |
| Core acoplar-se à primeira linguagem | Alta | Alto | Contratos compostos e Language Conformance Dataset |
| Matriz multilíngue tornar-se insustentável | Média | Alto | Critérios de seleção, adaptadores e níveis explícitos de suporte |

## 25. Critérios globais de sucesso

### 25.1 Técnicos

- ao menos um workflow completo, seguro e auditável;
- execução reproduzível do dataset de referência;
- critérios de parada e aprovação explícitos;
- evidências estruturadas por execução;
- testes automatizados das fronteiras críticas;
- arquitetura extensível demonstrada por mais de uma linguagem e por um segundo workflow ou extensão.

### 25.2 Educacionais

- tutorial compreensível por engenheiros de qualidade;
- decisões arquiteturais justificadas por evidência;
- experimentos reproduzíveis;
- exemplos de quando não usar IA;
- lições negativas e limitações publicadas.

### 25.3 Portfólio e comunidade

- repositório público profissional e executável;
- releases com demonstrações e resultados;
- feedback real de usuários externos;
- ao menos um artigo ou apresentação baseado em evidências;
- contribuições ou discussões técnicas da comunidade.

Stars, seguidores e visualizações serão observados, mas não serão tratados como prova de qualidade técnica.

### 25.4 Livro e jornada

- journals consistentes e factuais;
- métricas de esforço e uso de IA desde o início;
- retrospectiva por milestone;
- decisões e mudanças rastreáveis;
- material suficiente para um manuscrito baseado em acontecimentos reais;
- reflexões narrativas contemporâneas às decisões, sem fabricação retrospectiva da história.

## 26. Questões abertas

Estas questões serão decididas nas etapas indicadas, não agora:

- Qual será o nome público definitivo do projeto?
- EngineOS será um componente interno ou o nome da plataforma?
- Qual tipo de aplicação Python será usado no primeiro alpha de referência?
- Quais serão as três primeiras linguagens e quais níveis de suporte cada uma terá na v0.1?
- Quais capacidades mínimas compõem um `LanguageProfile` suportado?
- Qual provider será usado no primeiro experimento real?
- Qual mecanismo de sandbox é viável para os ambientes suportados?
- LangGraph agrega valor suficiente ao primeiro workflow?
- PydanticAI reduz complexidade ou sobrepõe responsabilidades?
- Quais informações de prompts podem ser publicadas sem risco?
- O manuscrito ficará no mesmo repositório público ou em repositório separado?
- Qual licença melhor atende ao objetivo educacional e comunitário?

## 27. Próxima decisão

Implementar e revisar o incremento 5.4 — adapter live e budgets:

1. promover o transporte OpenAI experimental para as portas públicas de análise, geração e correção;
2. manter Structured Outputs e validação local sem delegar workflow ou retries ao provider;
3. persistir reservas e consumo de chamadas, tokens, latência e custo estimado;
4. separar falha transitória, permanente, recusa e output inválido;
5. preservar demo keyless/offline e tornar o smoke live manual e explicitamente orçado;
6. não considerar o Gate 5 aprovado nem iniciar a Etapa 6 automaticamente.
