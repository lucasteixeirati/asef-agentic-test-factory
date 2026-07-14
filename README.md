# ASEF — Fábrica de Testes Agêntica

> Um projeto open source para estudar e construir automações de Quality Engineering assistidas por IA, com contexto validado, workflows controlados, execução isolada e evidências auditáveis.

## Por que este projeto existe

O ASEF nasceu como uma ideia ampla de automação agêntica do SDLC e foi redirecionado para Quality Engineering a partir da experiência prática do autor. O objetivo é demonstrar como construir uma fábrica de testes moderna sem entregar decisões críticas a um modelo de linguagem.

Este repositório também registra a jornada de desenvolvimento assistido por IA: hipóteses, velocidade, custos, falhas, retrabalho, decisões humanas e lições que poderão formar um futuro livro.

## Estado atual

**Experimental — pré-alpha.** Os incrementos 5.1, 5.2 e 5.3 foram concluídos. A versão `0.1.0a2` incorporou o oracle independente e a correção limitada, mas esse fluxo ainda não integra a CLI pública. O projeto não deve ser usado para executar código arbitrariamente hostil ou em produção.

Já demonstrado:

- máquina de estados explícita e budgets compartilhados;
- structured output com validação e recuperação limitada;
- modo demo por cassette e chamada OpenAI live controlada;
- LangGraph com checkpoint, interrupção e retomada SQLite;
- comparação separada com PydanticAI;
- Docker Desktop com rede, filesystem, memória, PIDs, timeout e paths controlados;
- baselines em Python, Node/TypeScript e Java por imagens fixadas em digest;
- contexto validável de QA, equipes, sistemas, repositórios, skills, MCPs e LLMs;
- journals, experimentos, ADRs e lições aprendidas.

## Visão arquitetural

```text
QualityContext + decisão humana
              |
      runtime e políticas ASEF
       /        |         \
 workflow     skills     MCP/LLM adapters
       \        |         /
       sandbox + evidências
```

O runtime mantém autoridade sobre estados, budgets, retries, permissões e evidências. LLMs propõem análises e artefatos tipados. Skills oferecem capacidades delimitadas. MCPs somente executam operações autorizadas pelo contexto e pela política.

## Skills planejadas

- web UI e WebView;
- backend/API;
- mobile;
- testes unitários;
- mutation testing;
- performance.

O catálogo está em [`docs/skills/catalog.md`](docs/skills/catalog.md). Uma skill aparecer no catálogo não significa que esteja implementada ou suportada.

## Contexto de Quality Engineering

Cada organização poderá descrever, sem armazenar secrets:

- perfil e fronteiras de aprovação do QA;
- objetivos e riscos da equipe;
- sistemas e fluxos críticos;
- repositórios e escopos de leitura/escrita;
- capabilities e skills permitidas;
- MCPs e operações autorizadas;
- política de modelos, dados e budgets.

Veja [`docs/context/README.md`](docs/context/README.md) e o [exemplo fictício](examples/context/quality-context.example.json).

## Quickstart — demo sem chave de API

Requisitos: Git, Python 3.13 e Docker Desktop iniciado. Em um PowerShell:

```powershell
git clone https://github.com/lucasteixeirati/asef-agentic-test-factory.git
cd asef-agentic-test-factory
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\asef.exe run
```

O resultado esperado é um JSON com `"status": "SUCCEEDED"` e `"classification": "ACCEPTED"`. O relatório fica no caminho indicado por `report_path`. A demo cria contexto, SUT fictício e cassettes públicos sob `.asef/demo/v1`; ela não lê `OPENAI_API_KEY`, não chama um modelo e não exige checkout para funcionar depois da instalação.

O comando executa o WS-001 completo no Docker Desktop, sem rede no container e sem escrever no SUT original. Estado, snapshot de contexto, manifest, eventos, artifact, resultado e relatórios permanecem sob `.asef/runs`. Por policy, `--output` também deve permanecer dentro de `.asef`.

O audit trail de cada run é append-only. Logs operacionais JSONL ficam em `.asef/logs/asef.jsonl`, com rotação e redaction básica. Use `--log-level DEBUG|INFO|WARNING|ERROR` sem alterar o JSON público do stdout. Veja [`docs/architecture/observability.md`](docs/architecture/observability.md).

Para observar fronteiras intermediárias sem executar o container:

```powershell
.\.venv\Scripts\asef.exe prepare
.\.venv\Scripts\asef.exe generate
```

Limitações atuais: apenas a skill `unit` e o perfil Python do calculator percorrem o fluxo completo; o modo live ainda não é público; o isolamento depende do daemon local do Docker; e a demo gravada prova o workflow, não a qualidade de um modelo em produção.

Checkpoint e decisão humana usam um extra opcional:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[workflow-langgraph]"
.\.venv\Scripts\asef.exe wait
.\.venv\Scripts\asef.exe resume --run-id <RUN_ID> --answer "Only signed integers"
.\.venv\Scripts\asef.exe cancel --run-id <RUN_ID> --reason "No longer required"
```

`wait` retorna 3, `resume` reutiliza a mesma run e `cancel` retorna 130. O modo linear continua funcionando sem instalar o extra.

Exit codes públicos: 0 sucesso, 2 input/contexto, 3 espera humana, 4 falha funcional, 5 policy, 6 budget, 7 provider/infraestrutura e 130 cancelamento. A matriz é exercitada automaticamente nos testes.

Para desenvolver e executar toda a suíte localmente, use o checkout:

```powershell
$env:PYTHONPATH='src'
$env:ASEF_RUN_DOCKER_TESTS='1'
python -m unittest discover -s tests\integration -v
```

Nunca coloque uma chave real em arquivos do repositório. O modo live exige `OPENAI_API_KEY` no host e budget explícito.

## Estrutura

- `src/asef/` — contratos, application services, runtime, adapters e baseline legada temporária;
- `spikes/` — comparações descartáveis ou isoladas;
- `tests/` — testes unitários e integrações Docker;
- `docs/` — arquitetura, projeto, qualidade, contexto e experimentos;
- `journal/` — fatos contemporâneos da jornada;
- `book/` — estratégia e notas do futuro livro;
- `concepcao/` — documentos históricos preservados.

## Roadmap resumido

1. Marco Zero e planejamento — concluído.
2. Contratos, workflow e avaliação — concluído.
3. Spikes arquiteturais — revisão técnica concluída.
4. Walking skeleton e hardening — concluídos; Gate 4 aprovado.
5. Alpha Python — incrementos 5.1, 5.2 e 5.3 concluídos; integração pública do novo fluxo à CLI permanece futura.
6. Perfis TypeScript e Java.
7. Developer preview e hardening da v0.1.

Veja o [`PLANEJAMENTO_MESTRE.md`](PLANEJAMENTO_MESTRE.md).

## Contribuição e segurança

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) e [`SECURITY.md`](SECURITY.md). Resultados experimentais, limitações e decisões revertidas são contribuições válidas; o projeto não busca uma narrativa artificial de sucesso contínuo.

## Licença

Código e documentação são disponibilizados sob a licença MIT. Consulte [`LICENSE`](LICENSE).

---

### English summary

ASEF is an experimental open-source Agentic Test Factory for learning how to build context-aware, policy-controlled and evidence-driven Quality Engineering automation with LLMs, skills, MCP integrations and isolated execution.
