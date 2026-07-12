# Personas e necessidades

## Objetivo

Representar os principais perfis que deverão compreender, executar, estudar ou ampliar a Fábrica de Testes Agêntica. As personas orientam decisões de produto; não pretendem descrever todos os usuários possíveis.

## P1 — Engenheira de qualidade que aprende IA

**Contexto:** possui experiência com testes manuais ou automação, mas pouca experiência construindo sistemas agênticos.

**Objetivos:**

- executar um workflow sem compreender toda a arquitetura;
- visualizar como requisitos se transformam em riscos, cenários e testes;
- entender onde a IA participou e onde houve validação determinística;
- estudar exemplos e adaptar um caso existente.

**Dificuldades:**

- terminologia de LLMs e agentes;
- configuração de providers e ambientes;
- interpretação de métricas probabilísticas;
- receio de executar código gerado.

**Necessidades:**

- modo demo sem credenciais;
- instalação diagnosticável;
- tutorial progressivo;
- relatório legível;
- explicação das decisões e limitações.

## P2 — SDET ou engenheiro de automação experiente

**Contexto:** domina código, frameworks de teste e CI, e deseja avaliar utilidade real da abordagem agêntica.

**Objetivos:**

- executar a plataforma sobre um SUT conhecido;
- comparar testes gerados com sua baseline;
- medir cobertura, mutação, falhas e custo;
- integrar ou criar adaptadores;
- reproduzir experimentos.

**Dificuldades:**

- desconfiança de demonstrações sem evidência;
- toolchains distintos entre linguagens;
- resultados instáveis entre modelos;
- frameworks que escondem o fluxo de controle.

**Necessidades:**

- schemas e contratos explícitos;
- eventos, manifests e artefatos auditáveis;
- datasets versionados;
- documentação de extensão;
- separação entre falha do teste, SUT, infraestrutura e modelo.

## P3 — Líder ou arquiteto de qualidade

**Contexto:** avalia riscos, governança e adoção de IA em processos de engenharia.

**Objetivos:**

- entender riscos e controles;
- analisar custo, benefício e intervenção humana;
- avaliar onde a autonomia é aceitável;
- usar o projeto como referência para decisões internas.

**Dificuldades:**

- alegações de produtividade sem baseline;
- ausência de rastreabilidade;
- exposição de dados e credenciais;
- falta de critérios de parada e responsabilidade.

**Necessidades:**

- visão executiva;
- threat model;
- políticas e budgets;
- métricas com definição operacional;
- histórico de decisões, falhas e retrabalho.

## P4 — Contribuidor open source

**Contexto:** deseja corrigir, ampliar ou portar uma capacidade para novo ecossistema.

**Objetivos:**

- compreender rapidamente a organização do repositório;
- executar testes locais;
- criar um adaptador ou experimento;
- propor mudanças sem romper contratos.

**Dificuldades:**

- documentação divergente;
- interfaces grandes;
- ausência de fixtures e modo offline;
- decisões arquiteturais implícitas.

**Necessidades:**

- governança documental;
- ADRs;
- conformance suite;
- exemplos pequenos;
- política de contribuição e níveis de suporte.

## P5 — Autor e mantenedor

**Contexto:** engenheiro de qualidade responsável pela visão, construção e narrativa do projeto.

**Objetivos:**

- demonstrar domínio técnico com decisões justificadas;
- medir a construção assistida por IA em dias e custos diretos;
- preservar a coerência entre aplicação, documentação e livro;
- incorporar feedback sem perder o propósito.

**Necessidades:**

- gates explícitos;
- backlog priorizado;
- registros simples e sustentáveis;
- separação entre decisão, experimento e sugestão;
- trilha factual para o livro.

## Priorização

As personas P1 e P2 orientam a experiência da v0.1. P3 orienta governança e evidências. P4 orienta extensibilidade. P5 orienta sustentabilidade e registro da jornada.

