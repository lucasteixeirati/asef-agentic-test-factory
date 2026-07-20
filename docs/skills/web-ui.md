# Skill `web-ui`

- **Versão:** 0.1.0-draft
- **Estado:** partial no perfil experimental `node-typescript`, somente no recorte local comprovado.
- **Propósito:** gerar e executar automações de fluxos web autorizados com evidência compreensível.
- **Escopo inicial:** aplicação fictícia local, Chromium, TypeScript e Playwright.
- **Fora do escopo inicial:** bypass de controles, scraping irrestrito, CAPTCHA, produção e dispositivos móveis reais.
- **Contexto obrigatório:** URL/servidor permitido, fluxos, dados de teste, efeitos proibidos, viewport e critérios de sucesso.
- **Saídas:** `WebUiTestPlan` declarativo, artifact TypeScript data-only, `WebUiExecutionResult` normalizado e screenshot PNG privado somente em falha.
- **Técnicas:** seletores por papel/label/test-id, espera por condição, isolamento de dados, teste por comportamento e abstração sem duplicação prematura.
- **Permissões:** origem HTTP em loopback literal e porta explicitamente allowlisted; downloads, uploads, clipboard, geolocalização, dialogs e pop-ups negados.
- **Checkpoints humanos:** login com segredo, operação destrutiva, pagamento, comunicação externa e publicação de imagem.
- **Conformance atual:** 14 controles versionados; nove casos de browser executados duas vezes em Chromium real não-root com `--network none` e fingerprint funcional estável.
- **Threat model:** [`../architecture/web-ui-browser-threat-model.md`](../architecture/web-ui-browser-threat-model.md).
- **Toolchain:** [`../architecture/web-ui-toolchain.md`](../architecture/web-ui-toolchain.md).
- **Limitações:** uma execução aprovada não comprova acessibilidade completa, compatibilidade universal de browsers ou aptidão para produção.
