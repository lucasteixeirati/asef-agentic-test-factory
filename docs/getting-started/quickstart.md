# Quickstart instalado — demo sem chave

Este caminho executa a demo pública do ASEF sem provider, sem chave de API e sem rede dentro do container. Ao final, você terá state, manifest, evidências e um `AlphaRunReport 1.0.0` em JSON e Markdown.

O ambiente abaixo é o recorte comprovado. Consulte [suporte e limitações](../project/support-and-limitations.md) antes de adaptar host, linguagem ou sandbox.

## Antes de começar

Você precisa de:

- Windows com PowerShell;
- Python 3.13;
- Docker Desktop instalado, iniciado e acessível pelo comando `docker`;
- imagem local `asef/python-pytest:8.3.3` construída a partir do tooling da mesma revisão;
- um wheel construído da mesma revisão deste documento ou um checkout do repositório.

A última pré-release publicada é `v0.1.0a6`. Use wheel, source archive, documentação e imagem construídos da mesma tag para manter a evidência atribuível à release.

A versão em desenvolvimento é a candidata corretiva local `0.1.0a7`, ainda não publicada. Não misture seus artefatos com os da `v0.1.0a6`; use sempre pacote, documentação e imagem da mesma revisão.

## 1. Criar um diretório vazio

```powershell
New-Item -ItemType Directory asef-demo
Set-Location asef-demo
py -3.13 -m venv .venv
```

## 2. Instalar

Com um wheel da mesma revisão deste guia:

```powershell
.\.venv\Scripts\python.exe -m pip install C:\downloads\asef_agentic_test_factory-VERSION-py3-none-any.whl
```

Para trabalhar a partir do checkout, execute na raiz clonada:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
```

O extra `workflow-langgraph` não é necessário para o caminho linear deste quickstart.

O wheel não incorpora uma imagem Docker. A partir do checkout ou do source archive da mesma revisão, construa somente a imagem pytest:

```powershell
docker build --tag asef/python-pytest:8.3.3 tooling/python-pytest
```

A imagem `python-quality` é opcional para esta demo. Se ela não existir, o doctor retorna `DEGRADED` com warning; coverage e mutation permanecem indisponíveis até seu build explícito.

## 3. Diagnosticar o ambiente

```powershell
.\.venv\Scripts\asef.exe doctor --mode demo --output .asef/doctor
```

Prossiga quando o JSON de stdout indicar `HEALTHY` ou `DEGRADED`. `BLOCKED` retorna exit `7`; veja [troubleshooting](../guides/troubleshooting.md) antes de tentar a run.

O doctor não instala dependências, não faz pull/build de imagem, não altera Docker e não chama provider.

## 4. Executar a demo

```powershell
.\.venv\Scripts\asef.exe run
```

O stdout contém um único objeto JSON. No caminho feliz, confira:

```json
{
  "status": "SUCCEEDED",
  "classification": "ACCEPTED",
  "report_json": ".asef/runs/RUN_ID/report.json",
  "report_markdown": ".asef/runs/RUN_ID/report.md",
  "report_schema_version": "1.0.0"
}
```

O objeto real também contém `run_id`, `run_dir` e o campo compatível `report_path`. Paths podem ser absolutos ou relativos conforme o diretório informado ao CLI; use os valores retornados, sem reconstruí-los a partir do exemplo.

Exit `0` e `ACCEPTED` significam que os testes gerados passaram na regra determinística e no runtime isolado desta demo. Não significam certificação, correção universal do SUT ou aprovação para produção.

## 5. Validar o report pelo contrato Python

No mesmo diretório:

```powershell
$report = Get-ChildItem .asef\runs -Recurse -Filter report.json | Select-Object -First 1
.\.venv\Scripts\python.exe -c "import json,sys; from asef import alpha_run_report_from_dict; alpha_run_report_from_dict(json.load(open(sys.argv[1], encoding='utf-8'))); print('report=valid')" $report.FullName
```

Isso usa o parser runtime, sem dependência de JSON Schema. O schema público também é distribuído em `asef/schemas/alpha-run-report.schema.json` para validadores externos.

## 6. Ler o resultado

Comece nesta ordem:

1. `status`, `classification` e `terminal`;
2. `functional_result`;
3. `evidence` e seus estados de integridade;
4. `facts` e `inferences`;
5. `recommendations` e `limitations`.

Veja o [guia de interpretação](../guides/report-interpretation.md) para classificações negativas, quality e integridade.

## 7. Planejar cleanup

O cleanup é dry-run por padrão:

```powershell
.\.venv\Scripts\asef.exe cleanup --kind runs --older-than-days 7
```

Leia o plano antes de considerar `--apply`. No Windows atualmente caracterizado, remoção recursiva de diretórios permanece bloqueada de forma segura. Não use `docker system prune` como substituto.

## O que a demo criou

Sob `.asef`:

- `demo/v1` — assets fictícios materializados pelo pacote;
- `runs/RUN_ID` — snapshot, state, events, manifest, artifact, execution evidence e reports;
- `logs/asef.jsonl` — logs operacionais com rotação e redaction básica;
- `maintenance/cleanup` — reports de cleanup, quando executado.

Próximos passos: [tutorial WF-001](../tutorials/wf-001-demo.md), [interpretação do report](../guides/report-interpretation.md) e [modo live](../tutorials/wf-001-live.md).
