# Plano detalhado da Etapa 6 — experiência multiskill

**Status:** aprovado para execução por Lucas em 2026-07-18.

## Objetivo

Transformar a fundação do Alpha Python em uma experiência cotidiana verificável: pedido em linguagem natural, skill especializada, perfil de linguagem, execução controlada, evidência normalizada e revisão humana. A prova multilíngue continua importante, mas passa a servir a jornadas reais de API, web e Java.

## Restrições herdadas do Gate 5

- uso experimental e não aprovado para produção;
- rede desligada por padrão e alvos somente com autorização explícita;
- nenhuma skill ou agente amplia sua própria autoridade;
- suporte só muda de `planned` após adapter, testes, conformance, documentação e limitações;
- avaliação humana isolada e avaliação externa continuam pendentes;
- findings críticos ou altos bloqueiam promoção quando não remediados ou aceitos explicitamente.

## Fatias

### 6.0 — reconciliação do produto e do roadmap

**Entrega:** este plano, Planejamento Mestre reconciliado e distinção explícita entre skill, perfil, adapter e agente.

**Aceite:** prioridades API → web/TypeScript → Java estão registradas sem apagar a comparação multilíngue e as técnicas avançadas.

### 6.1 — mapa do produto e jornada cotidiana

**Entrega:** `docs/PROJECT_MAP.md`, navegação pública e exemplos de jornadas por componente.

**Aceite:** uma pessoa identifica onde usar, estender, auditar e estudar o projeto sem percorrer a árvore inteira.

### 6.2 — contratos de skills e papéis agênticos

**Entrega:** template e contratos individuais de `unit`, `backend-api`, `web-ui`, `mutation` e `performance`; catálogo de papéis agênticos com autoridade limitada.

**Aceite:** cada contrato declara versão, estado, entradas, saídas, ferramentas, permissões, checkpoints, evidências, conformance e limitações. Documentação planejada não é confundida com implementação.

### 6.3 — primeira fatia cotidiana: backend API

**Progresso:** 6.3.1 concluída localmente: intenção natural por cassette, plano JSON revisável, política loopback/read-only, adapter HTTP no host, CLI, fixture, relatórios e testes. Permanecem integração ao contrato geral de run/budgets, sandbox Docker, provider live, OpenAPI e dataset de conformance dedicado.

**Escopo inicial:** HTTP/REST, contrato OpenAPI opcional, ambiente local/fictício e operações não destrutivas. GraphQL, gRPC, eventos e alvos públicos externos permanecem fora da primeira fatia.

**Entrega:** contrato tipado, política da skill, geração gravada e live, adapter HTTP controlado, caso fictício local, CLI explícita e relatório com rastreabilidade requisito → cenário → request → assertion → evidência.

**Aceite:** a mesma intenção em linguagem natural produz automação reproduzível; rede e métodos mutáveis exigem política; redirects, credenciais, hosts e payloads são limitados; conformance positiva, negativa e adversarial passa.

### 6.4 — TypeScript/Playwright e web UI

**Escopo inicial:** aplicação web fictícia local, fluxos de leitura e mutações delimitadas, Chromium no container e TypeScript.

**Entrega:** perfil `node-typescript`, adapter Playwright, política `web-ui`, page/component models quando justificados, fixtures e evidências visuais sanitizadas.

**Aceite:** execução end-to-end isolada, seletores resilientes, espera explícita por condição, ausência de secrets em artefatos e equivalência dos resultados normalizados com Python.

### 6.5 — Java/JUnit experimental

**Escopo inicial:** projeto Maven fictício e testes JUnit 5; Gradle, Spring completo e API Java ficam como expansão condicionada.

**Entrega:** detecção Maven, geração de teste unitário, build/test adapter, resultado normalizado e caminho documentado para JaCoCo/PIT.

**Aceite:** o workflow unitário equivalente executa em Python, TypeScript e Java sem lógica de ecossistema adicionada ao core.

### 6.6 — técnicas de qualidade, regressão e Gate 6

**Entrega:** coverage e mutation aplicáveis por perfil, relações metamórficas justificadas, datasets estratificados, regressão de segurança, matriz comparativa, retrospectiva, livro e pacote do Gate 6.

**Aceite:** métricas não alteram aceitação funcional silenciosamente; resultados nativos mantêm evidência; níveis de suporte são reconciliados com a implementação observada.

## Sequenciamento e checkpoints

Cada fatia segue: contrato → threat model → implementação mínima → testes → conformance → documentação → revisão. A conclusão de uma fatia não promove automaticamente a seguinte nem altera o nível público de suporte sem evidência.

## Gate 6 revisado

- [ ] A jornada em linguagem natural é compreensível e auditável?
- [ ] `backend-api` funciona ponta a ponta em alvo fictício autorizado?
- [ ] `web-ui` funciona ponta a ponta com TypeScript/Playwright?
- [ ] O workflow unitário equivalente funciona em Python, TypeScript e Java experimental?
- [ ] Adicionar perfis e skills não contaminou o core com lógica de tooling?
- [ ] Agentes permanecem limitados a saídas tipadas, sem autoridade operacional implícita?
- [ ] Coverage, mutation e relações metamórficas produzem evidência útil?
- [ ] Datasets distinguem regressão, conformance, benchmark e segurança?
- [ ] Condições herdadas do Gate 5 foram resolvidas ou permanecem explicitamente abertas?
