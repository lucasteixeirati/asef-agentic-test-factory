# Escopo e não escopo

## Escopo da iniciativa

- fábrica de testes agêntica open source e educacional;
- workflows controlados para atividades de Quality Engineering;
- runtime com estado, budgets, políticas e evidências;
- análise de requisito, risco e design de testes;
- geração e correção limitada de automação;
- execução isolada por Docker Desktop;
- suporte multilíngue progressivo;
- avaliação determinística e probabilística;
- documentação da construção assistida por IA;
- material factual para livro e comunidade.

## Escopo dos primeiros alphas

### Walking skeleton

- CLI mínima;
- structured input;
- um provider ou modo gravado;
- workspace efêmero;
- execução simples;
- eventos JSONL;
- relatório de sucesso ou falha.

### Alpha Python

- função Python pura existente como SUT;
- requisito estruturado;
- análise de risco e cenários;
- geração de pytest;
- execução em Docker Desktop;
- correção limitada do teste;
- classificação de falhas;
- datasets iniciais;
- relatório e manifest.

### Alpha multilíngue

- Python e TypeScript end-to-end;
- Java experimental;
- perfis compostos por capacidade;
- conformance suite;
- coverage e mutation testing;
- técnicas avançadas aplicáveis.

## Escopo pretendido da v0.1

- critérios obrigatórios da matriz do Planejamento Mestre;
- developer preview concluída;
- instalação validada no ambiente de referência;
- modo demo e live;
- documentação para uso e extensão;
- limitações e níveis de suporte publicados.

## Não escopo até a v0.1

- produto comercial ou SaaS;
- interface web e extensão VS Code;
- automação de todo o SDLC;
- deploy e release autônomos;
- Jira, Slack e Confluence;
- RAG e memória de longo prazo sem experimento aprovado;
- suporte enterprise ou multiusuário;
- garantia de segurança para código hostil fora do threat model publicado;
- compatibilidade com qualquer linguagem ou toolchain;
- conclusão editorial do livro.

## Restrições

- desenvolvimento inicial no ambiente Windows com Docker Desktop/WSL2;
- custo inicial limitado à licença informada de ChatGPT Plus;
- medição de esforço em dias corridos;
- suporte linguístico condicionado a adaptadores e conformance suite;
- credenciais fornecidas pelo usuário não entram na sandbox;
- resultados de IA exigem validação proporcional ao risco.

## Premissas

- Docker Desktop estará disponível no ambiente de referência;
- pelo menos um provider será acessível para modo live;
- o modo demo permitirá desenvolvimento e aprendizado sem provider;
- datasets poderão ser publicados respeitando origem, licença e privacidade;
- ferramentas open source selecionadas terão execução automatizável.

