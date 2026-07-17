# Relato — incremento 5.8.5 experiência instalada e CI

- **Data:** 2026-07-17
- **Estado:** concluída e aprovada localmente
- **Dependência:** 5.8.4 concluída e 5.8.5 aprovada por Lucas

Lucas autorizou exclusivamente a 5.8.5. Foram implementados checker documental offline, auditor da instalação e o sétimo job `public-experience`, sem alterar a independência dos seis jobs anteriores.

O checker final aprovou 117 documentos e 103 links. O auditor instalou o wheel sem dependências fora do checkout, exigiu doctor pronto, demo keyless aceita, contrato/schema empacotado, state/manifest/report reconciliados, hashes válidos e Markdown completo antes de copiar somente quatro arquivos publicáveis.

A prova encontrou uma inconsistência de produto: a imagem quality era marcada obrigatória no doctor, embora coverage/mutation sejam opcionais e o job de experiência construa somente pytest. A semântica foi corrigida para warning/degraded, com teste e documentação. Uma captura PowerShell com BOM também foi recusada corretamente pelo JSON estrito e normalizada sem repetir a run.

A regressão aprovou 344 testes com 33 skips e coverage de 85,34%. Dist, scripts, workflow e evidência instalada passaram no scanner; nenhum container gerenciado permaneceu. Nenhum commit, push, CI pública, mudança de versão, candidata ou release foi realizado. A 5.8.6 depende de nova aprovação explícita.
