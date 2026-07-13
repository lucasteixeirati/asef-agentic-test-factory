# Governança e autoridade documental

## Objetivo

Definir onde cada tipo de informação deve ser mantido e qual documento prevalece quando houver divergência.

## Hierarquia de autoridade

1. **ADRs aceitos:** decisões arquiteturais vigentes e suas consequências.
2. **Planejamento Mestre:** propósito, princípios, política de versões, milestones, gates e decisões de produto.
3. **Especificações especializadas:** segurança, avaliação, evidências, adaptadores e demais domínios técnicos.
4. **Roadmap operacional:** acompanhamento de execução, dependências e status.
5. **Experimentos e revisões:** evidências e recomendações que ainda precisam ser convertidas em decisões.
6. **Journal:** registro factual e cronológico; não estabelece decisão por si só.
7. **Documentos de concepção:** fontes históricas; não são normativos.

## Regra de precedência

- Um ADR aceito prevalece sobre hipótese ou formulação anterior do Planejamento Mestre.
- O Planejamento Mestre prevalece em propósito, escopo, princípios e gates.
- Uma especificação especializada prevalece nos detalhes de seu domínio, desde que não contrarie ADRs ou princípios do Planejamento Mestre.
- Revisões e experimentos não alteram a arquitetura automaticamente; devem produzir uma decisão registrada.
- Quando uma decisão superar conteúdo anterior, o documento antigo deve apontar para a decisão vigente ou ser marcado como superado.

## Responsabilidade de atualização

Toda mudança relevante deve verificar impactos em:

1. ADRs relacionados;
2. Planejamento Mestre;
3. especificação especializada;
4. roadmap e gates;
5. documentação de uso;
6. histórico e lições aprendidas.

## Mapa documental

| Documento | Autoridade principal |
|---|---|
| `PLANEJAMENTO_MESTRE.md` | Propósito, princípios, milestones e gates |
| `docs/project/product-vision.md` | Visão resumida e proposta de valor |
| `docs/project/measurement-baseline.md` | Método vigente de medição de tempo e custo |
| `docs/project/marco-zero.md` | Índice e situação documental do Marco Zero |
| `docs/project/stage-01-vision-domain-scope.md` | Índice e prontidão documental da Etapa 1 |
| `docs/project/stage-02-contracts-workflow-evaluation.md` | Índice e prontidão documental da Etapa 2 |
| `docs/project/stage-03-spikes-progress.md` | Progresso e pendências experimentais da Etapa 3 |
| `docs/project/pre-stage-04-readiness.md` | Preparação pública e contextual antes da Etapa 4 |
| `docs/project/stage-04-walking-skeleton-plan.md` | Plano executável aprovado/pendente da Etapa 4 |
| `docs/project/stage-04-progress.md` | Progresso e checkpoints da implementação do skeleton |
| `docs/project/gates/gate-04-acceptance-plan.md` | Critérios objetivos previstos para o Gate 4 |
| `docs/project/stage-05-alpha-python-plan.md` | Escopo, incrementos, dependências e Definition of Done da Etapa 5 |
| `docs/project/stage-05-progress.md` | Progresso e checkpoints da implementação do Alpha Python |
| `docs/project/gates/gate-05-acceptance-plan.md` | Critérios objetivos previstos para o Gate 5 |
| `docs/project/requirements-v01.md` | Requisitos e atributos de qualidade pretendidos para v0.1 |
| `docs/project/language-matrix.md` | Níveis de suporte e toolchains candidatos |
| `docs/project/first-workflow.md` | Seleção conceitual do primeiro workflow |
| `docs/project/gates/` | Decisões formais de aprovação ou bloqueio dos gates |
| `docs/architecture/adr/` | Decisões arquiteturais vigentes |
| `docs/architecture/language-adapters.md` | Contratos e extensibilidade multilíngue |
| `docs/architecture/pytest-adapter.md` | Implementação, segurança e limitações do adapter pytest do 5.2 |
| `docs/architecture/workflows/` | Topologia e estado dos workflows |
| `docs/architecture/contracts/` | Schemas e contratos conceituais do core |
| `docs/architecture/contracts/alpha-python-contracts.md` | Contratos concretos de datasets e métricas iniciados no 5.1 |
| `docs/architecture/adr/` | Decisões arquiteturais aceitas |
| `docs/architecture/evidence-model.md` | Eventos, manifests e rastreabilidade |
| `docs/architecture/observability.md` | Separação vigente entre audit trail e logs operacionais |
| `docs/quality/security-strategy.md` | Threat model, sandbox e controles |
| `docs/quality/evaluation-strategy.md` | Datasets, oracles, métricas e validade |
| `docs/quality/sandbox-policy-baseline.md` | Baseline quantitativa de isolamento e budgets |
| `docs/quality/datasets/` | Catálogos e futuros casos versionados |
| `datasets/` | Casos executáveis versionados e separação entre geração e avaliação |
| `tooling/python-pytest/` | Build reproduzível da imagem de ferramenta pytest |
| `docs/quality/stage-04r8-test-hardening.md` | Baselines de coverage e mutation do hardening pré-Gate 4 |
| `docs/project/open-source-strategy.md` | Publicação, experiência externa e comunidade |
| `docs/reviews/` | Revisões independentes e respostas |
| `docs/templates/` | Modelos operacionais para novos registros |
| `book/README.md` | Estratégia editorial e estrutura provisória |
| `book/PROVENANCE.md` | Classes de origem, autoria e estados editoriais |
| `book/source-map.md` | Relação provisória entre capítulos, evidências e lacunas |
| `journal/` | Registro factual da jornada |
| `docs/context/` | Contratos e governança do contexto operacional |
| `docs/skills/` | Catálogo e contratos planejados das skills ASEF |
| `docs/architecture/walking-skeleton-architecture.md` | Arquitetura planejada, substituída pela arquitetura real após implementação |
| `docs/architecture/contracts/walking-skeleton-schemas.md` | Contratos concretos e versionamento do skeleton |
| `examples/context/` | Exemplos fictícios e sanitizados de contexto |
| `README.md` | Entrada pública do projeto; não substitui o Planejamento Mestre |
| `concepcao/` | História da origem do projeto |
