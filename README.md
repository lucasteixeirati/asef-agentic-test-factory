# ASEF — Fábrica de Testes Agêntica

> Um projeto open source para estudar e construir automações de Quality Engineering assistidas por IA, com contexto validado, workflows controlados, execução isolada e evidências auditáveis.

## Por que este projeto existe

O ASEF nasceu como uma ideia ampla de automação agêntica do SDLC e foi redirecionado para Quality Engineering a partir da experiência prática do autor. O objetivo é demonstrar como construir uma fábrica de testes moderna sem entregar decisões críticas a um modelo de linguagem.

Este repositório também registra a jornada de desenvolvimento assistido por IA: hipóteses, velocidade, custos, falhas, retrabalho, decisões humanas e lições que poderão formar um futuro livro.

## Estado atual

**Experimental — pré-alpha.** O projeto concluiu tecnicamente os spikes arquiteturais e prepara o walking skeleton. Não deve ser usado para executar código arbitrariamente hostil ou em produção.

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

## Executar a baseline local

Requisitos atuais: Python 3.13 e, para integrações, Docker Desktop.

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python -m asef.cli prepare --output .asef\runs
```

O comando `prepare` valida request, QualityContext, scopes e o SUT controlado. Ele persiste estado, snapshot, manifest e eventos, encerrando em `ANALYZING_REQUIREMENT`, pronto para o próximo adapter. O alias `asef-spike` mantém a demo legada temporariamente.

Testes Docker são opt-in:

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
4. Walking skeleton — próximo.
5. Alpha Python.
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
