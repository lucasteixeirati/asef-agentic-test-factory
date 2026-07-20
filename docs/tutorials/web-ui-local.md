# Web UI local com plano revisável

Este tutorial usa somente a fixture fictícia empacotada, cassette público e Chromium
local. Não acesse sites externos, não use credenciais e não forneça dados privados.
O Gate 6 promoveu `web-ui` a partial no perfil experimental `node-typescript`,
somente neste recorte local.

## Pré-requisitos

- Windows 11 x86-64, Python 3.13 e Docker Desktop com containers Linux;
- wheel ASEF e checkout público da mesma revisão;
- imagem local `asef/web-ui-playwright:1.61.0`, construída explicitamente:

```powershell
docker build --build-arg SOURCE_DATE_EPOCH=0 --tag asef/web-ui-playwright:1.61.0 tooling/web-ui-playwright
```

Instale o wheel em uma virtualenv. A fixture HTML/JS/CSS e o cassette entram no
package; a execução não depende de `examples/` do checkout.

## 1. Gerar sem provider

Em um diretório de trabalho vazio fora do checkout:

```powershell
$generated = asef web-generate `
  --requirement "Review requirements and preserve evidence" `
  --mode demo | ConvertFrom-Json

$generated | ConvertTo-Json
```

O estado esperado é `WAITING_FOR_HUMAN_REVIEW`. O comando não abre browser e não
executa o plano.

## 2. Revisar

```powershell
Get-Content -Raw $generated.plan_path
Get-Content -Raw (Join-Path $generated.run_dir "manifest.json")
```

Confirme origem `http://127.0.0.1:4173`, ações fechadas, ausência de secrets e
cenários coerentes. Não edite o artifact persistido: seu hash será reconciliado.

## 3. Executar a run revisada

```powershell
$completed = asef web --run-id $generated.run_id | ConvertFrom-Json
$completed | ConvertTo-Json
```

O resultado esperado da cassette pública é `SUCCEEDED` / `ACCEPTED`, com um teste
aprovado. O container usa rede desabilitada; servidor e Chromium compartilham apenas
o loopback interno. O diretório indicado por `run_dir` contém state, manifest, plano,
resultado e hashes.

## Interpretação e limites

Esse resultado comprova somente a intenção gravada contra a fixture local da mesma
revisão. Não comprova suporte geral a TypeScript, compatibilidade entre browsers,
sites públicos, autenticação, upload/download, acessibilidade completa, visual
regression, performance ou produção. Screenshots de falha são privados por padrão.

O modo `--mode live` muda apenas a geração do plano e exige autorização separada,
modelo, chave no processo host, budget e tarifas positivas. Ele não amplia a origem
permitida nem autoriza execução externa.
