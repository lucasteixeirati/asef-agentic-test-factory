# Mapa de domínio e capacidades

## Domínios principais

Fábrica de Testes Agêntica
├── Intake e contexto
├── Análise de requisitos e risco
├── Design de testes
├── Geração de automação
├── Execução controlada
├── Avaliação de qualidade
├── Análise de falhas
├── Evidências e relatórios
└── Extensibilidade e governança

## 1. Intake e contexto

### Capacidades

- receber especificação e SUT;
- validar formato e completude mínima;
- descobrir estrutura do projeto;
- aplicar limites ao contexto;
- identificar informação sensível;
- solicitar esclarecimento quando necessário.

## 2. Análise de requisitos e risco

### Capacidades

- extrair comportamentos e restrições;
- identificar ambiguidades e contradições;
- mapear riscos por probabilidade e impacto;
- priorizar áreas de teste;
- relacionar requisitos, riscos e cenários.

## 3. Design de testes

### Capacidades

- criar cenários positivos, negativos e de fronteira;
- aplicar técnicas de particionamento e valores-limite;
- propor BDD quando apropriado;
- reduzir redundância;
- avaliar cobertura dos requisitos;
- definir oracles e dados necessários.

## 4. Geração de automação

### Capacidades

- selecionar perfil de linguagem e toolchain;
- gerar testes compatíveis com padrões permitidos;
- validar schema, sintaxe e estrutura;
- limitar arquivos e dependências;
- corrigir testes dentro do budget;
- preservar rastreabilidade com cenários e requisitos.

## 5. Execução controlada

### Capacidades

- preparar workspace efêmero;
- executar por Docker Desktop;
- aplicar rede, filesystem, processos e budgets;
- capturar stdout, stderr, status e artefatos;
- cancelar e descartar recursos;
- classificar falhas de infraestrutura.

## 6. Avaliação de qualidade

### Capacidades

- executar testes visíveis e ocultos;
- coletar cobertura;
- executar mutation testing;
- aplicar relações metamórficas;
- comparar resultados com oracles;
- avaliar regressão entre versões;
- registrar intervenção humana e violações.

## 7. Análise de falhas

### Capacidades

- separar falha de teste, SUT, geração, política e infraestrutura;
- resumir evidências sem ocultar incerteza;
- propor hipótese e próxima ação;
- encaminhar possível defeito para revisão humana;
- controlar ciclos de correção.

## 8. Evidências e relatórios

### Capacidades

- emitir eventos correlacionáveis;
- criar manifest reproduzível;
- armazenar artefatos por hash;
- gerar relatório estruturado e Markdown;
- sanitizar conteúdo sensível;
- comparar runs e milestones.

## 9. Extensibilidade e governança

### Capacidades

- compor `LanguageProfile`;
- registrar provider e skills;
- validar conformance suite;
- aplicar níveis de suporte;
- registrar ADRs e experimentos;
- executar gates e publicar limitações.

## Capacidade agêntica versus determinística

| Área | Predominantemente agêntica | Predominantemente determinística |
|---|---|---|
| Requisitos | interpretação e ambiguidades | validação de schema |
| Risco | levantamento contextual | cálculo e ordenação configurada |
| Design | proposição de cenários | verificação de formato e duplicidade simples |
| Geração | produção e correção de testes | syntax check e políticas |
| Execução | análise posterior | sandbox, comandos, timeout e captura |
| Avaliação | julgamento sem oracle completo | testes, coverage, mutação e contratos |
| Relatório | síntese explicativa | eventos, métricas e manifest |

## Prioridade por versão

- **Walking skeleton:** intake, geração simples, execução, eventos e relatório.
- **Alpha Python:** análise, design, geração, execução, correção limitada e avaliação básica.
- **Alpha multilíngue:** perfis compostos, conformance, coverage, mutação e avaliação avançada.
- **v0.1:** experiência externa, hardening, documentação e evidências completas.

