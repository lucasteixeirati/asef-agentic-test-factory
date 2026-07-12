# Master Plan: EngineOS (ASEF) & The Agentic Journey

## 1. Visão Geral e Estratégia de Duplo Impacto

O **EngineOS** (anteriormente AI Software Engineering Factory - ASEF) é uma plataforma de engenharia de software baseada em um **Runtime Agentic**. Em vez de acoplar agentes a scripts estáticos, o EngineOS separa rigidamente a infraestrutura de execução, as habilidades operacionais (*Skills/MCP*) e as regras de negócio do SDLC (*Workflows*).

Este projeto é executado sob uma estratégia de **Duplo Impacto**:
1. **O Produto (EngineOS):** Uma plataforma open-source, resiliente e testável, construída sob a ótica de Engenharia de Qualidade (QA para IA).
2. **O Livro (Building in Public):** Uma obra viva documentando a jornada de um Engenheiro de Qualidade sênior construindo sistemas complexos de IA em público.

---

## 2. Mudança de Paradigma Arquitetural

O design do sistema foi refatorado para eliminar o acúmulo de monólitos de agentes. A estrutura macro do repositório segue a seguinte árvore conceitual:

```text
EngineOS/
├── journal/               # Diário de bordo diário (Métricas, tokens, aprendizados)
├── brainstorms/           # Comparações e testes de hipóteses entre LLMs
├── core/
│   ├── workflow_engine/   # Orquestração de grafos e estados (LangGraph)
│   ├── agent_runtime/     # Ciclo de vida dos agentes e auto-correção (PydanticAI)
│   ├── skills/            # Ferramentas puras e contratos de dados (Pydantic)
│   ├── mcp_layer/         # Conectores isolados de protocolos de contexto (GitHub, Jira)
│   ├── memory/            # Estrutura tripartite (Mem0 + ChromaDB + Redis)
│   └── evaluation/        # Pipelines de testes de prompts e assertividade (DeepEval)
└── applications/          # CLI (Typer) e Web UI (Next.js)

3. Stack Tecnológica e Alocação de IAs (Mês 1)
Para o Mês 1 (Fase No-Code / Arquitetura e Especificação), a eficiência operacional está distribuída da seguinte forma:

IA de Concepção Principal (Assinada): ChatGPT Plus (Interface para debates arquiteturais, geração de PRD/ADRs e escrita dos capítulos iniciais do livro através de blocos de texto/Canvas).

IAs de Apoio e Benchmarking: Gemini (Varredura de contexto longo e ideias de resiliência de dados) e Amazon Q (Validação de infraestrutura e padrões de nuvem).

Stack de Código Futura (Mês 2+): Claude Code + VS Code + GitHub MCP (Reservado para quando o planejamento estiver blindado).

4. O Livro: "Construindo uma Plataforma de Engenharia de Software com IA em Público"
O livro não será um manual de ferramentas, mas uma crônica de engenharia, processos e tomadas de decisão.

Estrutura de Capítulos Definida:
Capítulo 1: Por que comecei esse projeto?

Capítulo 2: Minha experiência como QA (A busca pelo determinismo no caos).

Capítulo 3: Como a IA mudou completamente minha forma de trabalhar.

Capítulo 4: Os primeiros brainstorms (ChatGPT, Gemini, Amazon Q e os primeiros erros).

Capítulo 5: Quando percebi que estava pensando pequeno (O dia em que parei de criar agentes e decidi criar um Runtime).

Capítulo 6: Criando a visão do produto.

Capítulo 7: Arquitetura (A separação entre Workflows, Runtime e Skills).

Capítulo 8: Primeiro agente (Aterrissando com PydanticAI).

Capítulo 9: Primeiro Workflow (Desenhando estados com LangGraph).

Capítulo 10: Primeiro MCP (Conectando o mundo externo).

Capítulo 11: Primeira integração.

Capítulo 12: Primeira falha grande (O capítulo inevitável).

Capítulo 13: Refatoração.

Capítulo 14: A v0.1 (O nascimento do MVP funcional).

Capítulo 15: Open Source (Governança, CI/CD e comunidade).

Capítulo 16: O que eu faria diferente.

5. Roadmap de Engenharia (Evolução Incremental)

v0.1: Core Runtime      v0.3: Conectividade Real    v1.0: Enterprise Ready
  ┌────────────────┐       ┌────────────────┐         ┌────────────────┐
  │  PydanticAI    │──────►│  Camada MCP    │────────►│  Next.js App   │
  │  LangGraph     │       │  LongMemory    │         │  VS Code Ext.  │
  │  Planner+Dev+QA│       │  Security/Perf │         │  Multi-Cloud   │
  └────────────────┘       └────────────────┘         └────────────────┘

v0.1 (Foco Atual de Design): CLI Local. Módulo Planner + Developer (escrita de funções simples) + QA Agent (reaproveitando o QA Assistant AI legado para rodar pytest em sandbox).

v0.2: Integração do Requirement Agent (gerador de BDD) e Reviewer Agent (revisão estática de SOLID).

v0.3: Camada MCP estável (GitHub/FileSystem) + Memória de Longo Prazo (Mem0).

v0.4: Automação de testes de prompt com DeepEval e monitoramento via LangSmith.

v1.0: Interface Web em Next.js e Extensão do VS Code.

6. Plano de Ação Tático: Próximas 4 Semanas (Fase Sem Código)
Com os templates criados e o ChatGPT Plus ativo, este é o cronograma de entregáveis da fase conceitual:

Semana 1: Refinamento da Visão e Posicionamento do Produto
Ação: Utilizar o ChatGPT Plus para detalhar o escopo funcional do MVP (v0.1). O que exatamente o agente Developer precisa gerar para o agente QA validar com sucesso?

Entregável: Escrever o rascunho do Capítulo 1 e Capítulo 5 do livro. Criar o arquivo docs/product_vision.md.

Registro: Alimentar o journal/ a cada sessão de escrita.

Semana 2: Arquitetura de Estados (LangGraph Core)
Ação: Desenhar a topologia do grafo para o workflow "Greenfield". Quais são os nós? Onde ocorrem os loops de erro se o código do desenvolvedor falhar nos testes do QA?

Entregável: docs/ADR-002_Workflow_Topology.md. Mapeamento de transição de estados em pseudocódigo Markdown.

Semana 3: Contratos de Tipos e Habilidades (Skills Schema)
Ação: Definir as interfaces de entrada e saída das primeiras ferramentas usando modelos Pydantic puros. Como o agente lê um arquivo? Como ele solicita um patch de alteração?

Entregável: Criação dos arquivos de definição de schemas em formato Markdown para servirem de contexto imediato no mês 2.

Semana 4: Plano de Testes do Sistema Não-Determinístico (QA para IA)
Ação: Criar a estratégia de validação das saídas da LLM. Como usaremos o DeepEval para garantir que o código gerado atende aos requisitos sem alucinar?

Entregável: docs/evaluation_strategy.md. Definição do gold dataset inicial de 20 prompts de teste.

7. Critérios de Sucesso para Saída da Fase No-Code
[ ] Todos os diretórios base criados no repositório local.

[ ] Visão do Produto e 3 primeiros ADRs (Framework, Interface, Separação de Camadas) revisados e consolidados.

[ ] Pelo menos 5 registros reais estruturados na pasta journal/.

[ ] Primeiros 5 capítulos do livro rascunhados e estruturados.

