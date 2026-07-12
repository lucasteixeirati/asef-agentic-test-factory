# Primeiro workflow vertical — Test Generation & Evaluation

## Identificação

- **ID:** WF-001
- **Nome de trabalho:** Test Generation & Evaluation
- **Caso de uso principal:** UC-001
- **Status:** selecionado para implementação vertical na Etapa 4
- **Primeiro perfil:** Python

## Problema

Engenheiros de qualidade precisam transformar requisitos e código existente em testes relevantes sem aceitar cegamente a saída de uma LLM. O workflow deve combinar interpretação agêntica com execução, oracles e evidências determinísticas.

## Objetivo

Receber requisito estruturado e função existente, identificar riscos, desenhar cenários, gerar testes, executá-los em isolamento, avaliar sua efetividade, corrigir testes quando permitido e produzir relatório auditável.

## Entradas conceituais

- requisito ou critérios de aceite;
- SUT existente e autorizado;
- perfil de linguagem;
- políticas e budgets;
- configuração de provider ou modo demo;
- testes/oracles de referência quando disponíveis.

## Saídas conceituais

- análise de ambiguidades e riscos;
- cenários rastreáveis;
- testes gerados;
- resultados de análise estática e execução;
- coverage e, quando habilitado, mutation score;
- classificação das falhas;
- eventos, manifest e artefatos;
- relatório Markdown e estruturado;
- decisões humanas registradas.

## Fluxo conceitual

Intake e validação
        ↓
Análise do requisito e do SUT
        ↓
Ambiguidade bloqueadora?
    ├── sim → solicitar decisão humana
    └── não
        ↓
Análise de riscos
        ↓
Design de cenários e oracles
        ↓
Geração de testes
        ↓
Validação estática e de políticas
        ↓
Execução em Docker Desktop
        ↓
Avaliação das evidências
    ├── teste inválido e budget disponível → corrigir teste
    ├── possível defeito do SUT → revisão humana
    ├── violação de política → falha segura
    ├── falha de infraestrutura → classificar e encerrar/repetir por política
    └── sucesso → relatório

## Limites do primeiro alpha

- função Python pura e pequena;
- projeto temporário controlado;
- pytest;
- dependências previamente permitidas;
- sem rede na sandbox;
- sem alteração automática do SUT original;
- no máximo duas tentativas de correção de teste;
- um provider no modo live;
- modo demo por respostas gravadas.

## Recorte anterior ao alpha — Walking Skeleton

O walking skeleton implementará somente um SUT controlado, skill `unit`, `unittest`, dois outputs gravados, execução Docker e evidências mínimas completas. Pytest, coverage, mutation, correção completa e múltiplos perfis continuam pertencendo ao alpha ou a etapas posteriores. Plano: `docs/project/stage-04-walking-skeleton-plan.md`.

## Independência da avaliação

- o SUT existente não será gerado pelo mesmo passo que cria os testes;
- testes ocultos não serão fornecidos ao gerador;
- oracles de referência serão curados ou derivados deterministicamente quando possível;
- geração de SUT sintético será identificada como laboratório e não como prova principal;
- uma LLM julgadora não substituirá evidência executável.

## Critérios de sucesso do alpha Python

- fluxo completo executável;
- estados e tentativas rastreáveis;
- sandbox aplicada;
- ao menos um caso de sucesso, um teste inválido, um possível defeito e uma violação de política;
- relatório que diferencia falha de teste, SUT e infraestrutura;
- core sem dependência direta de pytest fora dos adaptadores.

## Razões da seleção

- cobre as capacidades centrais do produto;
- produz evidências objetivas;
- demonstra o papel específico de Quality Engineering;
- permite progressão para TypeScript e Java;
- limita o SUT sem limitar a arquitetura;
- expõe riscos reais de circularidade, sandbox e avaliação.

## Adiado para a Etapa 2

- schemas exatos;
- nomes e granularidade dos estados;
- política detalhada de retry;
- budgets quantitativos;
- contrato dos adaptadores;
- formato definitivo do relatório;
- topologia de persistência e retomada.
