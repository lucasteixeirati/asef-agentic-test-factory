# Toolchain Web UI da fatia 6.4.2

## Escopo

A 6.4.2 comprovou que Node, Playwright e Chromium pinados iniciam sob a política
Docker comum. A 6.4.3 adiciona compilação e execução de `WebUiTestPlan` somente
contra a fixture local. O probe continua carregando apenas HTML constante em
`about:blank` e não é confundido com a execução funcional.

## Componentes

| Componente | Identidade |
|---|---|
| imagem oficial | Playwright 1.61.0 Noble por digest `sha256:57b65f…428a` |
| Node | 24.16.0 |
| Playwright npm | 1.61.0, instalado por `npm ci` e lockfile |
| Chromium | 149.0.7827.55 observado no digest |
| imagem ASEF | tag local `asef/web-ui-playwright:1.61.0`, resolvida para image ID antes da run |
| driver | `asef_web_ui_driver.mjs`, comandos fechados `version`, `probe` e `run` |
| adapter | `DockerWebUiToolchainProbe` |

## Execução funcional 6.4.3

`WebUiPlanCompiler` traduz o contrato validado para um módulo TypeScript data-only
determinístico. O adapter compara bytes e SHA-256 desse artifact com uma nova
compilação do plano persistido antes de iniciar Docker. O driver importa o módulo,
reconcilia seu conteúdo com `plan.json`, serve os três assets allowlisted da fixture
em `127.0.0.1:4173` e interpreta somente ações, locators e assertions fechados.

Cada cenário usa contexto novo com service workers bloqueados. Routing aborta
origens diferentes; popup, dialog e download tornam o cenário `POLICY_BLOCKED`.
Assertion divergente é `FAILED`, espera excedida é `TIMEOUT` e falha de browser ou
resultado inválido é `ERROR`. Screenshot PNG existe somente em cenário não aprovado,
fica sob output contido e permanece privada e não publicável.

A imagem oficial inclui browsers e dependências do sistema, mas não o package npm.
O build instala o package de versão idêntica com scripts e download de browser
desabilitados. Dependências nunca são instaladas durante a run.

## Política observada

```text
--network none
--read-only
--cap-drop ALL
--security-opt no-new-privileges:true
--user 65534:65534
--pids-limit 128
--memory 512m --memory-swap 512m
--cpus 1
workspace read-only
output separado e gravável
/tmp tmpfs noexec,nosuid,64 MiB
```

O resultado JSON estrito registra versões, UID/GID e observações de rootfs,
workspace e egress. Resultado ausente, grande, adulterado, com versão divergente ou
incompatível com o exit do container vira `SANDBOX_EXECUTION_ERROR`.

## Limites e decisões de segurança

- a imagem oficial é indicada apenas para teste/desenvolvimento e não para sites
  não confiáveis; a prova ASEF usa somente conteúdo fictício local;
- o processo Chromium é não-root, mas esta fatia não alega que o sandbox interno
  do browser seja uma fronteira suficiente; o container continua sendo o controle
  externo principal;
- não se usa `--ipc=host`; o probe usa `/tmp` limitado no lugar de compartilhar IPC
  com o host;
- o teste de egress usa `192.0.2.1`, endereço reservado para documentação, e exige
  falha sob `--network none`;
- o image ID local detecta troca da tag dentro da run, mas distribuição por registry
  e assinatura da imagem ainda não foram decididas;
- duas construções sem cache produziram o mesmo tar canônico npm
  (`c984c2e0…72bb`) e o mesmo probe, mas image IDs diferentes no exporter do Docker
  Desktop 28.2.2; a alegação é reprodutibilidade de entradas/conteúdo/comportamento,
  não byte-identidade da imagem;
- no Windows, diretórios criados por `tempfile` podem ter ACL incompatível com bind
  mounts do Docker Desktop; a integração usa raiz controlada sob `.asef`.

O threat model geral permanece em
[`web-ui-browser-threat-model.md`](web-ui-browser-threat-model.md).
