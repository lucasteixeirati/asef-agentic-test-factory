# Troubleshooting seguro

Comece pelo JSON de stdout, depois execute doctor. Preserve a run original quando houver suspeita de integridade; não “corrija” state, manifest ou report manualmente.

Ambientes, profiles e garantias não oferecidas estão em [suporte e limitações](../project/support-and-limitations.md).

## Por exit code

| Exit | Categoria | Primeira ação segura |
|---:|---|---|
| `0` | sucesso público | conferir classification, report e limitations |
| `2` | input/contexto | revisar argumento/path e validar o contexto |
| `3` | espera humana | usar `resume` ou `cancel` na mesma output root |
| `4` | falha funcional | inspecionar classification, attempts e execution evidence |
| `5` | policy | ler o finding; não desabilitar o controle |
| `6` | budget | comparar usage/budgets antes de decidir novo teto |
| `7` | provider/infraestrutura | executar doctor e separar dependência local de externa |
| `130` | cancelamento | conferir decision code e audit trail |

## Doctor primeiro

```powershell
asef doctor --mode demo --output .asef/doctor
```

Para live, acrescente contexto e `--mode live`. `BLOCKED` indica requisito obrigatório ausente ou inválido. O doctor não instala ou corrige automaticamente.

## Docker CLI, daemon e imagem

Sintomas comuns: comando `docker` ausente, daemon indisponível, imagem fixada não encontrada ou timeout.

Ações seguras:

1. confirme que Docker Desktop está iniciado;
2. execute `docker version` localmente;
3. rode `asef doctor --mode demo`;
4. confira se a imagem exigida pelo snapshot existe;
5. preserve o report/diagnóstico antes de alterar o ambiente.

Não recomende nem execute `docker system prune`, não remova containers alheios e não retire `--network none`, limites de recurso ou filesystem read-only para fazer a demo passar.

## Contexto e input

Para exit `2`, verifique:

- path existente e dentro do escopo esperado;
- JSON válido e campos conhecidos;
- system, repository, skill e language profile referenciados;
- imagem por digest;
- ausência de secret inline;
- modo do request compatível com o snapshot.

Falha anterior à criação da run não produz report. Isso evita fabricar audit trail sem evidência persistida.

## Provider, chave e budget live

Para `PROVIDER_ERROR`, `BUDGET_ERROR` ou exit `7` em live:

- confirme apenas a presença da variável de ambiente, sem imprimir seu valor;
- confirme modelo disponível e tarifas atuais;
- revise timeout, token limit e budget em BRL;
- diferencie retry já consumido de nova execução paga;
- use dados fictícios ao reproduzir.

Não coloque secret em arquivo, argumento, issue ou cassette. Não aumente budget automaticamente; um novo teto exige decisão consciente do operador.

## Policy do artifact

`POLICY_VIOLATION` pode indicar traversal, extensão/path incorreto, tamanho, shape inválido ou scenario IDs divergentes.

Leia o erro tipado e corrija a fonte autorizada. Não mova o artifact para fora de `tests_generated`, não execute o arquivo diretamente no host e não relaxe a skill para aceitar output arbitrário.

## Falha funcional e possível defeito

Para `TEST_FAILURE` ou `TEST_ERROR`, compare contagens, outcome e evidence refs. `SUT_DEFECT_SUSPECTED` exige checkpoint/revisão humana; não abra bug como “confirmado” apenas com a classificação automática.

Preserve separação entre teste gerado, SUT e oracle. Corrigir o teste não deve modificar o SUT original.

## Filesystem e cleanup

Use sempre dry-run primeiro:

```powershell
asef cleanup --kind all --older-than-days 7
```

Targets fora de `.asef`, links/junctions, identidade alterada ou perfil recursivo não comprovado falham fechados. No Windows atual, remoção recursiva de diretórios não é prometida. Não delete evidência manualmente durante uma investigação.

## Report ou evidence integrity

Se houver `MISSING`, `MISMATCH`, `EVIDENCE_INTEGRITY_FAILURE` ou hash divergente no manifest:

1. pare a reemissão/publicação;
2. preserve `state.json`, `events.jsonl`, `manifest.json`, reports e evidências;
3. compare SHA-256 sem editar arquivos;
4. verifique link/junction e path externo;
5. reproduza em nova run, não sobrescreva a original.

Tamper existente bloqueia reemissão. O ASEF não repara silenciosamente a trilha.

## Logs

Logs operacionais ficam em `.asef/logs/asef.jsonl`. Use `--log-level DEBUG` apenas quando necessário e revise o arquivo antes de compartilhar. Redaction básica reduz risco, mas não substitui inspeção humana.

## Onde reportar

- bug reproduzível e sanitizado: issue do repositório;
- vulnerabilidade ou possível exposição: siga [`SECURITY.md`](../../SECURITY.md), sem issue pública;
- dúvida de contribuição: consulte [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

Inclua versão, comando sem secrets, status/classification, exit code e diagnóstico sanitizado. Não anexe source privado, raw environment, prompt/resposta integral ou credencial.
