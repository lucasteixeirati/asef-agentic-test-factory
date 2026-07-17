# Arquitetura real do Alpha Python

## Escopo e estado

Este documento descreve o caminho implementado do Alpha Python. Ele substitui a visão prospectiva de [`walking-skeleton-architecture.md`](walking-skeleton-architecture.md) como referência do runtime atual, sem apagar o histórico da Etapa 4.

O único perfil funcional é `python-pytest`, ainda **experimental**. A arquitetura separa decisões de domínio de provider, Docker, filesystem, ferramentas de qualidade e apresentação do relatório.

## Fluxo implementado

```text
CLI / SkeletonRunRequest
  -> QualityContext validado + policies + budgets
  -> adapter agêntico recorded ou live
  -> skill unit + validação estática
  -> workspace efêmero com cópias allowlisted
  -> pytest em container Docker sem rede
  -> oracle curado + loop de correção, quando o fluxo combinado é usado
  -> coverage/mutation opcionais em tooling separado
  -> AlphaRunReport tipado + evidências + hashes no manifest
```

`asef run` usa por padrão a jornada linear da demo. O fluxo combinado com oracle independente existe no runtime e nos datasets, mas não deve ser inferido de toda execução pública. LangGraph participa somente do checkpoint humano opcional; não é o loop de controle principal.

## Camadas e autoridades

| Área | Implementação atual | Autoridade |
|---|---|---|
| Contratos/core | `contracts.py`, `report_contracts.py`, `evaluation_contracts.py`, policies e outcomes | estados, invariantes, classificações e formas de dados |
| Aplicação | serviços em `application/` e protocols em `application/ports.py` | sequência, budgets, retries, aceitação e transições |
| Adapters | contexto, provider recorded/live, workspace, Docker, stores e checkpoint | traduzir efeitos externos para contratos ASEF |
| Skills | validação da capability `unit` | aceitar ou rejeitar artifact antes do workspace |
| Tooling | imagens `python-pytest` e `python-quality` | executar argv e ferramentas pinados dentro de containers |
| Datasets | Smoke e Security versionados | casos, oracles e resultados esperados; nunca comandos arbitrários |
| Evidências | `JsonRunStore`, eventos, manifest e refs com SHA-256 | persistir fatos observados e identidades |
| Relatórios | builder, verifier, renderer e store do Alpha report | projetar fatos persistidos em JSON normativo e Markdown derivado |
| Logs | `.asef/logs/asef.jsonl` | diagnóstico operacional sanitizado, sem autoridade funcional |
| Humano | resposta sanitizada em checkpoint | esclarecer, confirmar suspeita ou cancelar; não reescrever evidência |

## Fronteiras de dependência

O core e os serviços de aplicação trabalham com tipos neutros e `Protocol`. Eles não importam OpenAI, Docker, pytest, coverage, mutmut ou LangGraph para decidir o domínio. Adapters podem depender da tecnologia que traduzem, mas devolvem somente contratos ASEF. A CLI compõe essas dependências e mapeia o resultado para exit code; ela não decide aceitação por conta própria.

```text
CLI
  -> application services
       -> AgenticTestPort ........ recorded / OpenAI adapter
       -> WorkspacePort .......... filesystem efêmero
       -> TestExecutionPort ...... Docker pytest adapter
       -> QualityExecutionPort ... Docker coverage/mutation adapter
       -> RunStorePort ........... JSON, JSONL, artifacts e manifest
       -> HumanCheckpointPort .... LangGraph/SQLite opcional
```

Uma capability nova entra por contrato/port e adapter; não por condicionais de linguagem espalhadas pelo core. O guia de extensão está em [`../contributing/adapter-guide.md`](../contributing/adapter-guide.md).

## Contexto, provider e geração

O `QualityContext` limita arquivos, operações, provider, modelo e budgets antes de qualquer efeito. O resolver produz um snapshot primitivo persistível. O adapter `recorded` torna a demo determinística e keyless. O adapter live usa a Responses API somente quando contexto, operação, modelo, tarifas, budget e secret no host foram autorizados; sua saída continua sujeita aos contratos e validadores locais.

Requisito, source, comentários e resposta do provider são dados não confiáveis. O provider propõe análise e artifact; não escolhe paths, imagem, argv, mount, política, retry ou transição.

## Workspace, execução e oracle

Somente arquivos autorizados são copiados para uma árvore efêmera sob `.asef`. O SUT original não é modificado. O artifact passa por contrato, path, AST/imports e rastreabilidade antes do staging.

O adapter pytest executa uma imagem pinada, como usuário não privilegiado, sem rede, com workspace read-only, output separado e budgets. JUnit é normalizado em `NormalizedExecutionResult`; falha de teste, erro de coleta, timeout e infraestrutura permanecem categorias distintas.

No fluxo combinado, o oracle curado é persistido por hash e nunca entra no prompt. Cada tentativa tem artifact, execução e avaliação próprios. Uma correção pode alterar apenas o teste gerado dentro do budget; suspeita de defeito no SUT requer decisão humana e não autoriza correção automática do produto.

## Quality capabilities

Coverage e mutation são observações opcionais executadas pela imagem `python-quality`. Elas possuem contratos, evidências e status próprios (`AVAILABLE`, `FAILED`, `UNSUPPORTED` ou não solicitada) e enriquecem o report sem mudar retroativamente a decisão funcional. Os resultados valem para o perfil de referência delimitado, não para projetos Python arbitrários.

## Persistência e publicação

A árvore real e as garantias de integridade estão em [`evidence-model.md`](evidence-model.md). Em resumo:

- `state.json` é o estado funcional persistido;
- `events.jsonl` é a trilha da run;
- `manifest.json` reúne identidade, uso, refs e hashes dos reports;
- artifacts, attempts, oracle, resultados e quality preservam evidências delimitadas;
- `report.json` é a representação normativa de `AlphaRunReport 1.0.0`;
- `report.md` é uma renderização determinística do JSON validado.

O verifier confina refs à run e publica somente itens allowlisted e sanitizados. Ausência ou divergência de hash vira `MISSING`/`MISMATCH`; não é convertida em fato verificado. O store reconcilia tamper anterior e escreve JSON, Markdown e manifest por uma transação recuperável.

## Limites arquiteturais atuais

- CLI local e persistência em filesystem assumem um único operador; não há coordenação distribuída.
- Docker é uma sandbox experimental, não garantia para código arbitrariamente hostil ou produção.
- O host e as combinações realmente validadas estão na fonte canônica [`../project/support-and-limitations.md`](../project/support-and-limitations.md).
- Logs e eventos não são assinados nem armazenamento imutável.
- PydanticAI permanece spike; não integra o caminho live.
- Node, Java, Go e .NET não possuem adapter end-to-end suportado.

