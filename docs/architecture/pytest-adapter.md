# Adapter pytest do Alpha Python

- **Incremento:** 5.2
- **Estado:** concluído; aprovado localmente e na CI pública em 2026-07-13
- **Código:** `src/asef/adapters/pytest_execution.py`
- **Toolchain:** `tooling/python-pytest/`

## Fronteira

O core conhece `TestExecutionOutcome` e o resultado normalizado, não importa `pytest` nem interpreta texto do terminal. O adapter executa a ferramenta e traduz JUnit XML para fatos neutros.

```text
workspace read-only ──┐
                     ├─ container pytest sem rede ── JUnit XML
output file isolado ──┘                                  │
                                                        ↓
                            PASSED / ASSERTION_FAILURE / TEST_ERROR
                            NO_TESTS / TOOL_ERROR / INFRASTRUCTURE_ERROR
```

## Resultado estruturado

O pytest é executado com seu suporte JUnit XML nativo, sem plugin de report adicional:

- cache provider desabilitado;
- bytecode desabilitado;
- `basetemp` no tmpfs;
- JUnit escrito em `/asef-output/pytest-junit.xml`;
- stdout e stderr continuam limitados pelo sandbox;
- XML limitado a 2 MiB, sem DTD ou entities;
- resultado bruto preservado por `EvidenceRef`.

`NormalizedExecutionResult` evoluiu para `1.1.0` com ferramenta/versão, outcome, errors, skipped e raw result opcional. Requests, snapshots e demais contratos permanecem `1.0.0`.

## Classificação factual

| Evidência | Outcome neutro | Classificação atual do workflow |
|---|---|---|
| exit 0, testes > 0, sem failure/error/skip | `PASSED` | `ACCEPTED` |
| exit 0 com testes ignorados | `PASSED` | `TEST_FAILURE`; suíte gerada incompleta |
| assertion failure | `ASSERTION_FAILURE` | `TEST_FAILURE` até o oracle do 5.3 |
| sintaxe, import ou collection error | `TEST_ERROR` | `TEST_ERROR` |
| zero testes / exit 5 | `NO_TESTS` | `TEST_ERROR` |
| uso inválido, XML ausente/malformado | `TOOL_ERROR` | `INFRASTRUCTURE_ERROR` |
| timeout, OOM ou falha Docker | `INFRASTRUCTURE_ERROR` | `INFRASTRUCTURE_ERROR` |

O 5.2 não atribui assertion failure ao teste ou ao SUT. Essa interpretação exige o oracle independente da ADR-009 e pertence ao 5.3.

## Sandbox e escrita

O mount `/workspace` continua read-only. Para permitir resultado estruturado sem abrir escrita sobre o SUT:

1. o host cria um diretório irmão dentro da raiz autorizada;
2. um único arquivo vazio é pré-criado e recebe permissão temporária de escrita;
3. o diretório é montado separadamente em `/asef-output`;
4. mounts iguais, ancestrais, descendentes ou fora da raiz são rejeitados;
5. o XML é lido, limitado e o capture temporário é removido.

## Imagem de ferramenta

A imagem deriva da imagem Python já fixada por digest. `pytest`, `iniconfig`, `packaging` e `pluggy` têm versões e SHA-256 de wheels pinados. A CI constrói `asef/python-pytest:8.3.3`; antes da execução, o adapter resolve o tag para um image ID `sha256:` e usa esse ID imutável no container e na evidência.

Ainda não existe imagem publicada em registry. Por isso:

- o perfil continua parcial;
- a CLI pública não muda silenciosamente de runner;
- ausência da imagem falha antes do container com diagnóstico explícito;
- distribuição/retention da imagem será decidida antes da experiência externa do Alpha.

## Evidência local

- adapter/parser: 7 testes unitários;
- integração Docker pytest: 3/3;
- Docker/security total: 14/14;
- adapter com 93% de branch coverage;
- core total com 88% de branch coverage.
