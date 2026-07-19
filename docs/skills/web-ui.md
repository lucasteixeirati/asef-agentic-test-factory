# Skill `web-ui`

- **Versão:** 0.1.0-draft
- **Estado:** contrato/política 6.4.1 e toolchain 6.4.2 implementados localmente; capability continua `planned` até existir execução de plano e conformance.
- **Propósito:** gerar e executar automações de fluxos web autorizados com evidência compreensível.
- **Escopo inicial:** aplicação fictícia local, Chromium, TypeScript e Playwright.
- **Fora do escopo inicial:** bypass de controles, scraping irrestrito, CAPTCHA, produção e dispositivos móveis reais.
- **Contexto obrigatório:** URL/servidor permitido, fluxos, dados de teste, efeitos proibidos, viewport e critérios de sucesso.
- **Saídas:** `WebUiTestPlan` declarativo e `WebUiExecutionResult` normalizado; automação Playwright e screenshots reais continuam planejadas.
- **Técnicas:** seletores por papel/label/test-id, espera por condição, isolamento de dados, teste por comportamento e abstração sem duplicação prematura.
- **Permissões:** origem HTTP em loopback literal e porta explicitamente allowlisted; downloads, uploads, clipboard, geolocalização, dialogs e pop-ups negados.
- **Checkpoints humanos:** login com segredo, operação destrutiva, pagamento, comunicação externa e publicação de imagem.
- **Conformance atual:** testes de parser/política/fixture e probe Docker real de Chromium não-root, sem rede e com filesystems delimitados; execução de cenário permanece planejada.
- **Threat model:** [`../architecture/web-ui-browser-threat-model.md`](../architecture/web-ui-browser-threat-model.md).
- **Toolchain:** [`../architecture/web-ui-toolchain.md`](../architecture/web-ui-toolchain.md).
- **Limitações:** uma execução aprovada não comprova acessibilidade completa, compatibilidade universal de browsers ou aptidão para produção.
