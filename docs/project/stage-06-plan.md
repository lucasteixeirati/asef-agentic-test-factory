# Plano detalhado da Etapa 6 — experiência multiskill

**Status:** concluído; Gate 6 aprovado por Lucas em 2026-07-20.

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

**Progresso:** 6.3.1, 6.3.2 e 6.3.3 concluídas localmente. Além do envelope e da execução loopback, `api-generate` possui provider live opt-in com tarifas fornecidas pelo operador, budget, tokens, custo estimado e retry contabilizados; OpenAPI 3.0/3.1 JSON opcional restringe operações e gera evidência resumida; o dataset `BACKEND-API-CONFORMANCE-001` cobre oito controles. A rede cotidiana continua fail-closed em loopback: serviço externo real depende de adapter com resolução/pinning e isolamento ainda não implementado.

**Escopo inicial:** HTTP/REST, contrato OpenAPI opcional, ambiente local/fictício e operações não destrutivas. GraphQL, gRPC, eventos e alvos públicos externos permanecem fora da primeira fatia.

**Entrega:** contrato tipado, política da skill, geração gravada e live, adapter HTTP controlado, caso fictício local, CLI explícita e relatório com rastreabilidade requisito → cenário → request → assertion → evidência.

**Aceite:** a mesma intenção em linguagem natural produz automação reproduzível; rede e métodos mutáveis exigem política; redirects, credenciais, hosts e payloads são limitados; conformance positiva, negativa e adversarial passa.

### 6.4 — TypeScript/Playwright e web UI

**Progresso:** 6.4.1–6.4.6 concluídas localmente. O caminho cassette, capability run/revisão por hash, execução Chromium, live opt-in sem chamada real, dataset adversarial repetido e experiência instalada fora do checkout estão comprovados. O Gate 6 promoveu somente `unit` e `web-ui` a partial no perfil experimental `node-typescript`.

**Escopo inicial:** aplicação web fictícia local, fluxos de leitura e mutações delimitadas, Chromium no container e TypeScript.

**Entrega:** perfil `node-typescript`, adapter Playwright, política `web-ui`, page/component models quando justificados, fixtures e evidências visuais sanitizadas.

**Aceite:** execução end-to-end isolada, seletores resilientes, espera explícita por condição, ausência de secrets em artefatos e equivalência dos resultados normalizados com Python.

### 6.5 — Java/JUnit experimental

**Progresso:** 6.5.1–6.5.6 concluídas localmente. Contratos,
fixture empacotada, toolchain Maven offline, compilação JUnit determinística, run
revisável, Surefire normalizado, conformance repetida e experiência instalada estão
comprovados. O Gate 6 promoveu somente `unit` a partial no perfil experimental
`java-junit`.

**Escopo inicial:** projeto Maven fictício e testes JUnit 5; Gradle, Spring completo e API Java ficam como expansão condicionada.

**Entrega:** detecção Maven, geração de teste unitário, build/test adapter, resultado normalizado e caminho documentado para JaCoCo/PIT.

**Aceite:** o workflow unitário equivalente executa em Python, TypeScript e Java sem lógica de ecossistema adicionada ao core.

### 6.6 — técnicas de qualidade, regressão e Gate 6

**Progresso:** consolidação local concluída. O caminho unitário TypeScript foi
materializado sobre a mesma intenção aritmética revisada do Java, com compilação
determinística, Node test/TAP nativo e sandbox comum. Coverage/mutation foram
reconciliados por aplicabilidade (disponíveis em Python; indisponibilidade explícita
nos demais), relações metamórficas válidas foram versionadas e o pacote Gate 6 foi
preparado e aprovado pela validação humana final.

**Entrega:** coverage e mutation aplicáveis por perfil, relações metamórficas justificadas, datasets estratificados, regressão de segurança, matriz comparativa, retrospectiva, livro e pacote do Gate 6.

**Aceite:** métricas não alteram aceitação funcional silenciosamente; resultados nativos mantêm evidência; níveis de suporte são reconciliados com a implementação observada.

## Sequenciamento e checkpoints

Cada fatia segue: contrato → threat model → implementação mínima → testes → conformance → documentação → revisão. A conclusão de uma fatia não promove automaticamente a seguinte nem altera o nível público de suporte sem evidência.

## Gate 6 revisado

- [x] A jornada em linguagem natural é compreensível e auditável tecnicamente?
- [x] `backend-api` funciona ponta a ponta em alvo fictício autorizado?
- [x] `web-ui` funciona ponta a ponta com TypeScript/Playwright?
- [x] O workflow unitário equivalente funciona em Python, TypeScript e Java experimental no recorte aritmético?
- [x] O core permaneceu livre de lógica específica de tooling ao adicionar perfis e skills?
- [x] Agentes permanecem limitados a saídas tipadas, sem autoridade operacional implícita?
- [x] Coverage, mutation e relações metamórficas produzem evidência útil ou ausência explícita?
- [x] Datasets distinguem regressão, conformance, benchmark e segurança?
- [x] Condições herdadas do Gate 5 permanecem explicitamente abertas onde não resolvidas?

O checklist técnico foi seguido pela decisão humana registrada em
`gates/gate-06-acceptance-plan.md`: Gate 6 aprovado em 20/07/2026.
