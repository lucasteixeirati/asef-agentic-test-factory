# Contribuindo com o ASEF

Obrigado por contribuir. O ASEF é experimental e prioriza evidência reproduzível, segurança, contratos estáveis e honestidade sobre limitações. Participar implica seguir o [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Antes de começar

- leia o [`README.md`](README.md), o [`PLANEJAMENTO_MESTRE.md`](PLANEJAMENTO_MESTRE.md) e os [limites atuais](docs/project/support-and-limitations.md);
- procure issue, experimento ou ADR relacionado;
- descreva problema e evidência antes de uma mudança arquitetural;
- não apresente spike, alvo ou capability planejada como suporte entregue;
- use somente sistemas, organizações, dados e credenciais fictícios/sanitizados.

## Setup mínimo

Requer Python 3.13. Crie e ative uma virtualenv, então instale o package e dependências de teste:

```powershell
python -m pip install -e ".[test]"
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python -m coverage run -m unittest discover -s tests -v
python -m coverage report
python tools/secret_scan.py
```

Extras são opt-in:

- `.[mutation]` para a baseline local de mutmut;
- `.[workflow-langgraph]` para checkpoint humano opcional;
- requirements em `spikes/` somente para os spikes isolados.

Não adicione uma dependência opcional ao caminho core por conveniência.

## Matriz local de testes

| Mudança | Validação mínima |
|---|---|
| Core, contrato, adapter falso ou docs acopladas | regressão `unittest`, coverage >=85%, secret scan e `git diff --check` |
| Workflow LangGraph | testes de checkpoint/workflow com o extra instalado |
| Adapter pytest/Docker | build de `tooling/python-pytest` e integrações com `ASEF_RUN_DOCKER_TESTS=1` |
| Coverage/mutation container | build de `tooling/python-quality` e `ASEF_RUN_QUALITY_DOCKER_TESTS=1` |
| Live provider | somente smoke manual autorizado; nunca obrigatório em PR |
| Dataset/segurança | runner correspondente, fingerprints/reports e ausência de containers gerenciados |

Integrações Docker são opt-in porque constroem imagens e executam containers. Não relaxe sandbox para fazê-las passar e não use `docker system prune`. Registre testes não executados e o motivo.

## Arquitetura e extensões

Core e application services dependem de contratos/ports, não de Docker, OpenAI, pytest, coverage, mutmut ou LangGraph. Efeitos concretos pertencem aos adapters; imagens e drivers, a `tooling/`; datasets não controlam argv, imagem, mount ou policy.

Para adicionar capability, adapter ou perfil, siga o [`docs/contributing/adapter-guide.md`](docs/contributing/adapter-guide.md). Um perfil começa `planned` e só é promovido com contrato, fixtures, conformance, failure paths, isolamento, documentação e evidência end-to-end.

## Pull requests

Explique problema/escopo, evidências/testes, riscos/limitações, impacto em contratos/segurança/documentação e uso relevante de IA. Atualize a fonte documental que tem autoridade; mudanças de suporte devem reconciliar a [matriz de linguagens](docs/project/language-matrix.md) e a [fonte de suporte](docs/project/support-and-limitations.md).

O template existente contém o checklist mínimo. Issues de bug, experimento e skill/contexto já separam reprodução, hipótese, permissões e conformance; proponha novo template apenas se houver um fluxo realmente distinto.

## Dados, cassettes e IA

- não inclua secrets, dados internos, prompts privados, headers ou contexto real de equipes;
- autenticação é apenas referência gerenciada pelo host;
- sanitize outputs e execute `python tools/secret_scan.py` antes do commit;
- cassettes live são opt-in e não são publicáveis sem revisão humana;
- revise código e texto gerados por IA, declare sugestões aceitas/rejeitadas e preserve a decisão humana;
- IA não pode aprovar sua própria evidência, licença, segurança ou mudança arquitetural.

Mantenedores preservam autoridade sobre visão, arquitetura, segurança e releases. Experimentos informam decisões, mas não alteram ADRs automaticamente.
