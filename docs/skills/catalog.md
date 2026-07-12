# Catálogo inicial de skills ASEF

Skills ASEF são capacidades de Quality Engineering invocadas pelo runtime. Elas não são equivalentes às skills locais de uma ferramenta de desenvolvimento e não recebem autoridade automática sobre MCPs ou ambientes.

| Skill | Sistemas | Saídas principais | Ferramentas futuras | Aprovações típicas |
|---|---|---|---|---|
| `web-ui` | web, SPA, webview híbrida | cenários UI, page/screen models, automações | Playwright, browser MCP | acesso a ambiente, exportação |
| `backend-api` | REST, GraphQL, gRPC, eventos | contratos, cenários, automações de API | clients HTTP, schemas, service virtualization | dados e endpoints privados |
| `mobile` | Android, iOS, híbrido | fluxos, automações, matriz de devices | Appium, device farms | upload de app, device cloud |
| `unit` | funções, classes, módulos | testes isolados e oracles | pytest, JUnit, Vitest/Jest | exportação ao repositório |
| `mutation` | código com suíte existente | configuração, mutants e relatório | mutmut, PIT, Stryker | budget de duração |
| `performance` | APIs, UI, eventos, batch | workload, thresholds e relatórios | k6, JMeter, Gatling | ambiente e carga autorizados |

## Contrato mínimo futuro de uma skill

- identificador e versão;
- capability e sistemas aplicáveis;
- nível de suporte por linguagem;
- contexto obrigatório e opcional;
- inputs e outputs tipados;
- comandos e dependências permitidos;
- MCPs e operações permitidas;
- budgets padrão e máximos;
- decisões humanas obrigatórias;
- dataset de conformance;
- riscos e limitações;
- evidências produzidas.

## Composição

Um workflow pode compor várias skills, mas cada uma mantém contrato e evidências próprios. Mutation não gera automaticamente testes; performance não reutiliza credenciais de backend sem política; mobile não ganha acesso ao device farm apenas porque o sistema é classificado como aplicativo.

## Evolução planejada

1. detalhar `unit` e `backend-api` no alpha Python;
2. detalhar `web-ui` com TypeScript/Playwright;
3. experimentar `mobile` com Java/Android e adaptadores externos;
4. habilitar mutation somente quando houver suíte determinística executável;
5. habilitar performance apenas com ambiente e thresholds aprovados.
