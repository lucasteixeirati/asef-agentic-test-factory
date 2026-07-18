# Relato — preparação da candidata corretiva `0.1.0a7`

- **Data:** 2026-07-17
- **Autorização:** preparar candidata corretiva após o bloqueio da 5.9.2
- **Estado:** candidata local pronta para checkpoint de publicação; Gate e sessão continuam bloqueados

O defeito de processo que originou `PREFLIGHT-F-001` foi tratado com um contrato explícito: a versão do package representa desenvolvimento, enquanto `release-state.json` registra separadamente a última versão e tag publicadas. Isso evita que uma candidata local seja apresentada como release e evita que documentos congelados preservem uma alegação obsoleta após publicação.

Metadata e fallbacks foram promovidos para `0.1.0a7`. README, quickstart e suporte reconhecem `v0.1.0a6` como última release e `0.1.0a7` como candidata não publicada. O checker e seus testes protegem as duas identidades.

Wheel e sdist locais foram construídos e escaneados. Em diretório temporário fora do checkout, o sdist passou no docs checker; o wheel instalou sem dependências; doctor, demo, auditor 9/9 e cleanup dry-run passaram; a evidência foi escaneada e nenhum container gerenciado permaneceu. A regressão final aprovou 357 testes, 33 skips e coverage de 85%.

Após autorização explícita, o commit `58ea802` foi enviado à `main` e a CI pública `29620941881` aprovou os sete jobs. Nenhuma tag, release ou contato externo foi realizado. A candidata validada em CI ainda não fecha o finding da release imutável e não autoriza a 5.9.3.
