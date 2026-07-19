# ASEF — Fábrica de Testes Agêntica

> Projeto open source experimental para construir automações de Quality Engineering assistidas por IA, com contexto validado, decisões controladas, execução isolada e evidências auditáveis.

O ASEF investiga como LLMs podem propor análises e testes sem receber autoridade sobre estados, budgets, políticas, execução ou classificação. O runtime continua determinístico nessas fronteiras; decisões humanas e limitações permanecem visíveis.

## Estado atual

**Experimental — pré-alpha. Não use em produção nem contra código arbitrariamente hostil.**

A última pré-release publicada é [`v0.1.0a7`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a7), com os incrementos 5.1 a 5.8 e a correção documental identificada no preflight 5.9.2. Ela permanece experimental, pré-alpha e inadequada para produção ou código arbitrariamente hostil.

A versão atual do package é `0.1.0a7`. Use sempre código, documentação, wheel, sdist e imagem da mesma tag para preservar a identidade da evidência.

Comprovado até aqui:

- fluxo demo por cassette, sem chave e sem chamada de provider;
- geração e static validation de um teste unitário Python;
- execução Docker com rede, filesystem, memória, PIDs, timeout e paths controlados;
- estados, budgets, retries, evidências e exit codes tipados;
- reports JSON/Markdown com facts, inferences, recommendations e limitations separados;
- evidence integrity por containment e SHA-256, com hashes dos reports no manifest;
- checkpoints humanos opcionais com LangGraph;
- coverage/mutation experimentais e datasets Smoke/Security offline;
- doctor, logs estruturados, retention e cleanup conservador.
- primeira subfatia `backend-api`: intenção natural por cassette, plano revisável, REST loopback read-only e relatório próprio.

Ainda não comprovado:

- segurança para produção ou isolamento absoluto;
- qualidade de um modelo/provider em cenário real contínuo;
- validação por participante externo;
- suporte completo a TypeScript, Java, macOS ou Linux;
- que coverage/mutation ou `ACCEPTED` provem correção universal do SUT.

## Quickstart de cinco minutos

Requisitos: Python 3.13 e Docker Desktop iniciado. Git é necessário apenas para a instalação por checkout. Consulte a fonte canônica de [suporte e limitações](docs/project/support-and-limitations.md) antes de usar outro host, perfil ou modo live.

```powershell
git clone https://github.com/lucasteixeirati/asef-agentic-test-factory.git
cd asef-agentic-test-factory
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\asef.exe doctor --mode demo --output .asef/doctor
.\.venv\Scripts\asef.exe run
```

O caminho feliz retorna um único JSON em stdout com:

```json
{
  "status": "SUCCEEDED",
  "classification": "ACCEPTED",
  "report_json": ".asef/runs/RUN_ID/report.json",
  "report_markdown": ".asef/runs/RUN_ID/report.md",
  "report_schema_version": "1.0.0"
}
```

Use os paths reais retornados pelo CLI. A demo materializa somente assets fictícios sob `.asef/demo/v1`, não lê `OPENAI_API_KEY` e não usa rede no container.

Para instalação por wheel, validação do report e cleanup dry-run, siga o [quickstart completo](docs/getting-started/quickstart.md).

## O que acontece na demo

```text
request + QualityContext
  -> snapshot e policies
  -> análise gravada: behaviors, risks e scenarios
  -> artifact tipado + static validation
  -> workspace efêmero
  -> execução Docker normalizada
  -> avaliação funcional determinística
  -> AlphaRunReport JSON + Markdown + hashes no manifest
```

O fluxo público linear não usa o oracle curado combinado do incremento 5.3. `ACCEPTED` significa apenas que a execução registrada satisfez a regra funcional desta run e deste perfil experimental.

## Mapa da documentação

Comece pelo [mapa do produto](docs/PROJECT_MAP.md), que separa uso cotidiano, extensão, auditoria e pesquisa.

Para usar o Alpha atual:

- [quickstart instalado](docs/getting-started/quickstart.md) — instalação, doctor, run, validação e cleanup;
- [tutorial WF-001 demo](docs/tutorials/wf-001-demo.md) — requisito, análise, artifact, execução e report;
- [interpretação do report](docs/guides/report-interpretation.md) — classificações, quality e evidence integrity;
- [troubleshooting](docs/guides/troubleshooting.md) — exits e ações seguras;
- [tutorial live](docs/tutorials/wf-001-live.md) — provider opt-in, secret no host e budget explícito.
- [tutorial backend API local](docs/tutorials/backend-api-local.md) — intenção natural gravada, revisão por run, execução loopback e evidências da Etapa 6.

Referências técnicas atuais:

- [QualityContext](docs/context/README.md);
- [skills ASEF](docs/skills/README.md) e [papéis agênticos](docs/agents/README.md);
- [contratos do Alpha](docs/architecture/contracts/alpha-python-contracts.md);
- [threat model de publicação](docs/architecture/report-publication-threat-model.md);
- [observabilidade](docs/architecture/observability.md);
- [doctor](docs/architecture/doctor.md);
- [cleanup](docs/architecture/cleanup.md);
- [provider live](docs/architecture/live-provider.md).

A [arquitetura real do Alpha](docs/architecture/alpha-python-architecture.md), o [guia de adapters](docs/contributing/adapter-guide.md) e o [guia de contribuição](CONTRIBUTING.md) documentam as fronteiras vigentes.

## Comandos públicos

```text
asef prepare    fronteira anterior à análise
asef generate   análise, geração e static validation
asef run        demo linear completa no Docker
asef wait       pausa opcional para esclarecimento humano
asef resume     retoma a mesma run aguardando decisão
asef cancel     cancela a mesma run aguardando decisão
asef doctor     diagnóstico read-only do ambiente
asef smoke      dataset funcional offline
asef security   dataset de controles offline
asef cleanup    planejamento/aplicação conservadora sob .asef
asef api-generate intenção natural para plano REST revisável por cassette (6.3 em desenvolvimento)
asef api        plano REST declarativo contra fixture loopback autorizada (6.3 em desenvolvimento)
asef web-generate intenção natural gravada para plano Web UI revisável (6.4 em desenvolvimento)
asef web        retoma por run-id e executa a fixture Web UI isolada após revisão
```

Exit codes: `0` sucesso, `2` input/contexto, `3` espera humana, `4` falha funcional, `5` policy, `6` budget, `7` provider/infraestrutura e `130` cancelamento.

Checkpoint humano requer o extra opcional:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[workflow-langgraph]"
```

## Suporte e limitações

O único workflow completo continua sendo `unit` no perfil experimental `python-pytest`, com o SUT fictício calculator e Docker Desktop local. `backend-api` é parcial: cassette, plano revisável, retomada por run, budgets/evidências e REST read-only contra loopback no host; Docker cobre somente conformance autocontida. Node/TypeScript e Java continuam planejados. A [matriz canônica](docs/project/support-and-limitations.md) distingue capability comprovada de alvo futuro.

O modo live exige provider/modelo disponível, tarifas atuais informadas pelo operador e budget positivo. Disponibilidade, preço e câmbio não são congelados no repositório. Nunca coloque chave real em arquivo, argumento, contexto, cassette, report ou issue.

Quality capabilities enriquecem evidência, mas não mudam a classificação funcional e não aplicam threshold universal.

## Estrutura do repositório

O [mapa do produto](docs/PROJECT_MAP.md) explica a árvore completa e indica quais pastas um usuário cotidiano pode ignorar.

- `src/asef/` — contratos, application services, runtime e adapters;
- `tests/` — testes unitários, adversariais e integrações opcionais;
- `datasets/` — fixtures Smoke/Security públicas e fictícias;
- `docs/` — arquitetura, guias, projeto, qualidade e experimentos;
- `journal/` — fatos contemporâneos do desenvolvimento;
- `book/` — estratégia e notas do futuro livro;
- `concepcao/` — documentos históricos preservados.

## Roadmap

1. visão, domínio, contratos e spikes — concluídos;
2. walking skeleton e hardening — concluídos;
3. Alpha Python 5.1 a 5.7 — concluído;
4. relatórios e experiência pública 5.8 — publicado em `v0.1.0a6`;
5. avaliação interna/fechamento 5.9 e Gate 5 — concluídos com condições registradas;
6. experiência multiskill — jornada cotidiana, API, TypeScript/Playwright, Java/JUnit e técnicas avançadas, conforme o [plano da Etapa 6](docs/project/stage-06-plan.md).

Veja o [planejamento mestre](PLANEJAMENTO_MESTRE.md) para gates, dependências e critérios completos.

## Contribuição, segurança e licença

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de propor mudanças. Para vulnerabilidades ou possível exposição, siga [`SECURITY.md`](SECURITY.md) e não abra issue pública com dados sensíveis.

Código e documentação usam a licença [MIT](LICENSE). Resultados negativos, limitações e decisões revertidas são parte válida da evidência do projeto.

---

### English summary

ASEF is an experimental open-source Agentic Test Factory for context-aware, policy-controlled and evidence-driven Quality Engineering automation. The current complete path is a keyless Python demo; production safety, broad language support and external validation are not claimed.
