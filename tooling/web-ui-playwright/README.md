# ASEF Web UI Playwright toolchain

Imagem de ferramenta da fatia 6.4.2. Ela contém somente o package Playwright e os
browsers/dependências fornecidos pela imagem oficial pinada. Não executa `npm
install`, download de browser ou resolução de versão durante uma run.

## Identidade pinada

- base: `mcr.microsoft.com/playwright:v1.61.0-noble`;
- digest da base: `sha256:57b65fdc9ceabe0ef613124c7bbe2babcf9362c4d85e382fe3b03604e84b428a`;
- Node: `24.16.0`;
- npm usado no build: `11.13.0`;
- Playwright: `1.61.0`;
- Chromium observado no digest: `149.0.7827.55`;
- tag local: `asef/web-ui-playwright:1.61.0`.

`package-lock.json` fixa integridade e árvore npm. O adapter resolve a tag local
para um image ID `sha256:` antes de cada execução e usa somente esse ID na run.

## Build e prova local

```powershell
docker build --build-arg SOURCE_DATE_EPOCH=0 --tag asef/web-ui-playwright:1.61.0 tooling/web-ui-playwright
$env:PYTHONPATH = "src"
$env:ASEF_RUN_WEB_UI_DOCKER_TESTS = "1"
python -m unittest discover -s tests/integration -p test_web_ui_toolchain_docker.py -v
```

O probe possui apenas `version` e `probe`; não aceita URL, JavaScript, shell ou
argv livre. `probe` inicia Chromium headless em conteúdo em memória e verifica
usuário não-root, rootfs/workspace read-only e ausência de egress. A compilação e
execução de `WebUiTestPlan` pertencem à 6.4.3.

`SOURCE_DATE_EPOCH=0` normaliza timestamps da imagem e das camadas pelo BuildKit.
O tar canônico da árvore npm foi idêntico em construções `--no-cache`
(`c984c2e0…72bb`), mas o exporter
do Docker Desktop 28.2.2 produziu image IDs diferentes ao copiar o mesmo blob entre
estágios. A garantia atual é de entradas, conteúdo npm, versões e comportamento
reproduzíveis, não de imagem byte-idêntica. Cada run resolve e registra seu image ID.
