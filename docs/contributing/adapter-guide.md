# Guia para capabilities, adapters e perfis

## Princípio

Uma extensão traduz tecnologia externa para contratos ASEF sem transferir autoridade ao provider, dataset ou ferramenta. Core e application services não devem importar Docker, OpenAI, pytest, coverage, mutmut, LangGraph ou um SDK específico de linguagem.

Antes de implementar, descreva problema, capability, nível pretendido, contrato de resultado, riscos, tooling, budgets, evidência de conformance e limitações públicas. Um spike ou container que inicia não constitui suporte.

## Fronteiras de import

- tipos, enums e invariantes neutros ficam nos módulos de contratos/core;
- orchestration, policies, retries e decisão funcional ficam em `application/`;
- interfaces de efeitos ficam como `Protocol` em `application/ports.py` ou módulo neutro equivalente;
- SDKs, subprocess, Docker e filesystem concreto ficam em `adapters/`;
- imagens e drivers de ferramenta ficam em `tooling/`;
- CLI apenas compõe dependências e apresenta resultados;
- datasets selecionam IDs e fixtures; nunca shell, argv, imagem, mount ou policy arbitrários.

Valide a fronteira com testes de imports. Não adicione `if language == ...` ao core quando uma declaração de perfil, capability ou adapter resolve a variação.

## Adicionando uma capability

1. Defina request, output normalizado, status e códigos de diagnóstico em contrato neutro.
2. Declare a capability no perfil com `available`, `partial`, `planned` ou `unsupported`; `available`/`partial` exigem adapter.
3. Adicione ou reutilize um port pequeno, sem tipos do SDK externo.
4. Implemente o adapter com argv, imagem, limites e parsing fechados.
5. Persista resultado nativo sanitizado, resultado normalizado e hashes quando aplicável.
6. Cubra sucesso, falha funcional, output malformed, timeout, indisponibilidade e truncamento.
7. Adicione fixture/conformance independente e atualize documentação de suporte.

Uma capability opcional não pode mudar silenciosamente a aceitação funcional. Status ausente, não solicitado, unsupported e failed são estados distintos.

## Adicionando um perfil de linguagem

Proponha o perfil primeiro em `languages.py` com imagem por digest, version command, markers, capabilities e limitações. Comece como `planned`; promova somente após evidência end-to-end.

O perfil precisa demonstrar, no recorte anunciado:

- detecção sem escolha ambígua silenciosa;
- staging contido e SUT original preservado;
- build/test runner não interativo em container;
- resultado normalizado para sucesso, falha e erro de tooling;
- timeout, limites de output e ausência de rede/secret;
- imagem/toolchain reproduzíveis;
- conformance, tutorial e limitações atualizados.

Tooling específico pertence ao adapter/container. Não altere contratos centrais apenas para espelhar o formato nativo de uma ferramenta.

## Contratos, fixtures e conformance

- parsers devem rejeitar campos extras, duplicados, paths não canônicos, oversize e formatos ambíguos;
- fixtures usam somente projetos fictícios, pequenos e licenciáveis;
- golden files cobrem estruturas estáveis; invariantes devem ter testes contratuais próprios;
- integrações Docker são opt-in e não substituem testes unitários com executores falsos;
- cassettes não contêm prompt integral, headers, secrets ou conteúdo proprietário;
- resultados esperados negativos não viram pass quando a primitive está ausente: use `UNSUPPORTED`/erro conforme o contrato.

Use o catálogo de Language Conformance em [`../quality/datasets/catalog.md`](../quality/datasets/catalog.md) e a arquitetura vigente em [`../architecture/alpha-python-architecture.md`](../architecture/alpha-python-architecture.md).

## Checklist de revisão

- contrato e schema/versionamento foram avaliados;
- core/application permanecem independentes do tooling;
- imagem, argv, mounts, rede e budgets pertencem ao host revisado;
- unitários, failure paths e conformance foram executados;
- evidências e reports continuam sanitizados;
- secret scan e `git diff --check` passam;
- [`../project/language-matrix.md`](../project/language-matrix.md) e [`../project/support-and-limitations.md`](../project/support-and-limitations.md) refletem somente o comprovado;
- README/tutorial/troubleshooting mudam apenas se a jornada pública mudou;
- riscos, uso de IA e decisões humanas estão registrados no PR.

