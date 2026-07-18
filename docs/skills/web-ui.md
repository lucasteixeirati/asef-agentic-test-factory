# Skill `web-ui`

- **Versão:** 0.1.0-planned
- **Estado:** planned em `node-typescript`; implementação prevista na fatia 6.4.
- **Propósito:** gerar e executar automações de fluxos web autorizados com evidência compreensível.
- **Escopo inicial:** aplicação fictícia local, Chromium, TypeScript e Playwright.
- **Fora do escopo inicial:** bypass de controles, scraping irrestrito, CAPTCHA, produção e dispositivos móveis reais.
- **Contexto obrigatório:** URL/servidor permitido, fluxos, dados de teste, efeitos proibidos, viewport e critérios de sucesso.
- **Saídas planejadas:** cenários, fixtures, automações, abstrações de página/componente justificadas, screenshots sanitizadas e resultado normalizado.
- **Técnicas:** seletores por papel/label/test-id, espera por condição, isolamento de dados, teste por comportamento e abstração sem duplicação prematura.
- **Permissões:** navegador e rede somente na allowlist; downloads, uploads, clipboard, geolocalização e pop-ups negados salvo política explícita.
- **Checkpoints humanos:** login com segredo, operação destrutiva, pagamento, comunicação externa e publicação de imagem.
- **Conformance planejada:** seletores frágeis, timeout, navegação externa, popup, secret em trace/screenshot, efeito destrutivo e flakiness controlada.
- **Limitações:** uma execução aprovada não comprova acessibilidade completa, compatibilidade universal de browsers ou aptidão para produção.

