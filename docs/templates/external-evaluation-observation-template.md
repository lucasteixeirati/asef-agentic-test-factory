# Observação de avaliação externa — Alpha Python

> Copie este template somente quando uma sessão real ocorrer. Remova instruções editoriais antes de publicar e nunca inclua PII, terminal bruto, gravação ou paths pessoais.

## Controle da sessão

- **Resultado ID:** use `ASEF-EXT-YYYYMMDD-PNN`
- **Data:** registrar em `YYYY-MM-DD`
- **Protocolo:** `ASEF-EXT-ALPHA` versão `1.0.0`
- **Participante:** ID anonimizado `PNN`
- **Release/tag:** registrar tag congelada
- **Commit:** registrar SHA completo
- **Ambiente:** descrição ampla e não identificável
- **Estado:** `VALID`, `INFORMATIVE`, `ENVIRONMENT_BLOCKED`, `WITHDRAWN` ou `INVALID`

## Elegibilidade e consentimento

- **Experiência prática em QE/automação:** `true` ou `false`
- **Externo ao ciclo de autoria:** `true` ou `false`
- **Sem briefing funcional individual:** `true` ou `false`
- **Familiaridade prévia com o ASEF:** descrição limitada
- **Consentimento obtido:** `true` ou `false`
- **Revisão/retirada combinada:** descrição do processo, sem contato pessoal

Se consentimento não for `true`, o resultado não pode ser publicado.

## Integridade da release

| Asset | Tamanho | SHA-256 observado | Confere |
|---|---:|---|---|
| wheel | preencher na sessão | preencher na sessão | `true` ou `false` |
| sdist | preencher na sessão | preencher na sessão | `true` ou `false` |

## Tarefas

| ID | Estado | Duração aproximada | Fonte consultada | Observação anonimizada | Intervenção |
|---|---|---:|---|---|---|
| EXT-01 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-02 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-03 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-04 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-05 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-06 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-07 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |
| EXT-08 | preencher na sessão | preencher na sessão | preencher na sessão | preencher na sessão | nenhuma ou ID |

Estados permitidos: `COMPLETED_INDEPENDENTLY`, `COMPLETED_WITH_RECOVERY`, `COMPLETED_WITH_INTERVENTION`, `FAILED`, `ENVIRONMENT_BLOCKED` e `NOT_ATTEMPTED`.

## Intervenções

| ID | Tarefa | Motivo de segurança/logística | Conteúdo limitado da intervenção | Alterou o resultado |
|---|---|---|---|---|
| usar somente se ocorrer | registrar | registrar | registrar sem dado pessoal | `true` ou `false` |

## Compreensão do report

Resuma semanticamente, sem transcrição longa:

1. estado terminal e evidência;
2. classificação funcional e alcance;
3. o que `ACCEPTED` não prova;
4. integridade das referências;
5. diferença entre fatos e inferências;
6. recomendação e autoridade sobre o SUT;
7. limitações para outro projeto;
8. próxima ação segura.

## Findings

| ID | Tarefa | Severidade | Observação | Impacto | Critério G5 | Estado | Decisão |
|---|---|---|---|---|---|---|---|
| usar `EXT-F-NNN` se ocorrer | EXT-NN | `CRITICAL`, `HIGH`, `MEDIUM` ou `LOW` | registrar | registrar | G5-NN | `OPEN`, `FIXED`, `ACCEPTED_RISK` ou `OUT_OF_SCOPE` | registrar |

## Resultado da sessão

- **Tarefas centrais independentes/recuperadas:** registrar IDs
- **Interpretação central correta:** `true` ou `false`
- **Finding crítico/alto aberto:** `true` ou `false`
- **Sessão atende ao protocolo:** `true` ou `false`
- **Justificativa limitada:** registrar fatos, sem avaliar a pessoa

## Privacidade e publicação

- **PII removida:** `true` ou `false`
- **Secret scan:** `PASS` ou `FAIL`
- **Participante revisou ou exerceu retirada conforme combinado:** `true` ou `false`
- **Material bruto não versionado:** `true` ou `false`

## Limitações

- uma sessão não representa a população de QEs;
- ambiente, release e tarefas são delimitados;
- resultado não é certificação de segurança nem aprovação automática do Gate 5;
- registrar limitações adicionais observadas.
