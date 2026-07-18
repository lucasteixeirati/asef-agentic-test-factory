# Planejamento do incremento 6.4 — TypeScript, Playwright e Web UI

**Data:** 2026-07-18

Após a aprovação da 6.3, o repositório foi auditado antes de abrir a próxima implementação. O perfil `node-typescript` possui apenas a prova histórica de inicialização da imagem Node; `web-ui` continua documental e planned. Não há Playwright, Chromium empacotado, fixture, adapter, resultado normalizado ou dataset.

O plano divide a entrega em seis fatias. A arquitetura mantém a mesma separação observada em API: linguagem natural propõe um contrato declarativo, revisão humana autoriza a execução e o runtime controla origem, browser, artifact, container e evidências. A IA não recebe JavaScript arbitrário nem autoridade de rede.

A primeira prova será inteiramente local, com fixture e Chromium no mesmo container e rede externa desligada. Screenshots serão evidência privada e não sanitizada por padrão; traces e vídeos ficam fora do recorte inicial. Sites públicos, autenticação real e comunicação externa não são atalhos aceitos para demonstrar a capability.

Este planejamento foi estruturado pela IA a partir do roadmap, dos contratos existentes e da auditoria do repositório. Implementação, chamada live, push, tag e release permanecem pendentes de checkpoints explícitos.
