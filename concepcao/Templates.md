1. Template para o journal/
Cada dia de trabalho deve gerar um arquivo curto, focado em métricas e aprendizados. Isso alimentará diretamente os capítulos finais do livro.

# Journal: 2026-07-11 | O Marco Zero e a Mudança de Mentalidade

## 📊 Métricas do Dia
- **Tempo Investido:** 3 horas
- **Custo Estimado (APIs/Tokens):** $0.00 (Fase de Concepção)
- **IAs Utilizadas:** Gemini (Architectural Review), ChatGPT (PRD/ADR Design)

## 💡 Principais Aprendizados & Insights
- Percebi que estava pensando pequeno ao focar em "agentes isolados". O produto real é o *Runtime* resiliente; os agentes são apenas instâncias parametrizadas dentro dele.
- Decisão de separar estritamente a capacidade (Skills via MCP) do fluxo de controle (Workflows via LangGraph).

## 🛠️ Prompts que Funcionaram
- *Prompt X (Link ou colado aqui):* Excelente para extrair contradições no planejamento inicial.

## 🚧 Desafios & Bloqueios
- O dilema entre assinar Claude Code ou GPT Plus para a fase de no-code. Decidido pelo GPT Plus devido ao foco em documentação de alto nível.

## 🎯 Próximos Passos
- Desenhar o fluxo do primeiro workflow (Greenfield Project) em nível de pseudocódigo/estados.

2. Template para o brainstorms/
Para criar o estudo comparativo de IAs que você planejou, cada rodada de perguntas para os modelos deve ser documentada de forma padronizada.

# Brainstorm 002: Arquitetura do Estado Compartilhado (Gemini)

- **Data:** 2026-07-11
- **Modelo Avaliado:** Gemini 1.5 Pro
- **Contexto Fornecido:** PRD v1.0 do EngineOS

### 📥 O Prompt de Teste
"Dada a necessidade de persistência de estado entre falhas de rede no LangGraph, qual a melhor estratégia de checkpoint para um ambiente corporativo com múltiplos usuários?"

### 📤 Resposta Resumida da IA
- Sugeriu o uso de PostgreSQL com replicação assíncrona para os Checkpointers do LangGraph em vez do SQLite padrão.
- Propôs uma abordagem interessante de expurgar estados inativos após 48h para economizar armazenamento.

### ⚖️ Avaliação Técnica (Nota: 9.0/10)
- **Criatividade:** Alta. A ideia de expurgo de estado foi muito madura.
- **Precisão do Código:** Média. Forneceu um trecho de código com algumas assinaturas antigas do LangGraph que precisariam de refatoração.
- **Alinhamento com o Perfil de QA:** Excelente, focou bastante em cenários de degradação e falha de banco.

Plano de Ação para as Próximas Semanas (Fase Sem Código)
Nosso foco agora será consolidar a base teórica e documental do EngineOS. Vamos dividir o trabalho em sprints semanais de design:

Semana 1: Refinamento do Escopo e Visão do Produto

Detalhar o comportamento esperado do MVP (v0.1: Planner + Developer + QA).

Redigir o Capítulo 1 e Capítulo 5 do livro, registrando o exato momento em que o escopo mudou de ferramentas para plataforma.

Semana 2: Engenharia de Workflows e Contratos de Skills

Mapear a topologia de estados do LangGraph para o primeiro cenário.

Definir os schemas do Pydantic para as entradas e saídas das primeiras ferramentas de sistema (leitura/escrita de arquivos).

Semana 3: Matriz de Prompt Engineering e Estratégia de QA para IA

Desenhar o plano de avaliação inicial usando DeepEval (quais métricas exatas usaremos para julgar se o código gerado pelo Developer Agent é aceitável).

Estruturar o repositório de prompts para evitar o acoplamento de código.