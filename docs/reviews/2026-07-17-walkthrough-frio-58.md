# Walkthrough frio roteirizado — incremento 5.8

- **Data:** 2026-07-17
- **Executor:** automação conduzida pelo mantenedor
- **Ambiente:** diretório temporário vazio, Windows, Python 3.13 e Docker Desktop/WSL2
- **Artifact:** wheel preliminar local `0.1.0a6`, instalado com `--no-deps`
- **Escopo:** consistência operacional da documentação; não é teste externo de usabilidade

## Regra da sessão

A sequência seguiu somente o quickstart e seus links canônicos. Conhecimento interno do código não foi usado para escolher comandos, reconstruir paths ou interpretar o resultado. Paths vieram do stdout do CLI.

## Roteiro e resultado

| Passo | Ação documental | Resultado |
|---|---|---|
| 1 | localizar requisitos | Python 3.13, Docker, imagem pytest e wheel da mesma revisão identificados |
| 2 | instalar o wheel | `asef-agentic-test-factory 0.1.0a6` instalado sem dependências do runtime |
| 3 | executar doctor | `DEGRADED/READY`; checks opcionais não bloquearam a demo |
| 4 | executar demo | `SUCCEEDED/ACCEPTED`, keyless e sem rede de provider |
| 5 | localizar/validar report | path lido do stdout; parser público aprovou `AlphaRunReport 1.0.0` |
| 6 | responder checklist factual | status/classification/terminal, integridade, limitações, recomendação e próxima ação identificados |
| 7 | executar cleanup dry-run | `DRY_RUN_COMPLETE`, zero deleções e run recente preservada |
| 8 | localizar contribuição/segurança | README levou a `CONTRIBUTING.md` e `SECURITY.md` |

## Checklist factual

- status: `SUCCEEDED`;
- classification: `ACCEPTED`;
- terminal: `true`;
- evidence integrity observada: somente `VERIFIED`;
- limitações: `REFERENCE_PROFILE_ONLY`, `NOT_SAFE_FOR_PRODUCTION`, `QUALITY_NOT_REQUESTED`;
- recomendação: `DO_NOT_USE_IN_PRODUCTION`;
- próxima ação: ler recomendações/limitações; nenhuma ação é automática.

O auditor adicional aprovou nove de nove checks, incluindo validação real pelo JSON Schema Draft 2020-12 empacotado, contrato Python, state/manifest, hashes e paridade Markdown. Report JSON e Markdown tiveram SHA-256 `637ac5790b9228d5a6b107878babfff0a6a9b4d85cef5ef4c6d613175757bcff` e `564ab317d4f983ec138e33df849d24cbd014ed7e4373f41195d8184f50593695` nessa run.

## Findings

Nenhum finding bloqueante ou editorial novo surgiu no roteiro. O requisito de construir a imagem pytest e a opcionalidade da imagem quality já haviam sido corrigidos na 5.8.5. A instalação do validator `jsonschema` ocorreu somente depois da validação pelo parser runtime e foi usada exclusivamente pelo auditor de qualidade.

## Limites

- executor não foi um QE externo;
- não houve provider live, custo ou secret;
- a imagem pytest já estava disponível no host após build explícito da mesma revisão;
- o roteiro não valida discoverability em PyPI/registry, pois a candidata não está publicada;
- compreensão real da comunidade continua para Developer Preview.

