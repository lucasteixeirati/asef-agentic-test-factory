# Revisão final do incremento 5.3

- **Data:** 2026-07-14
- **Escopo:** oracle independente, correção limitada, evidências por tentativa e revisão humana
- **Decisão técnica local:** aprovada
- **Publicação:** pendente de commit e CI pública

## Histórico da decisão

A primeira revisão rejeitou provisoriamente o incremento com três bloqueadores e quatro findings médios. A aprovação local somente ocorreu após correção e prova automatizada de todos eles.

## Findings encerrados

1. Cada artifact inicial ou corrigido é preservado com bytes, SHA-256 e metadata da tentativa.
2. Reserva de chamada/correção é persistida antes do provider; falhas recebem estado e classificação tipados.
3. Workspaces de oracle e tentativas são removidos em `finally`; evidências permanecem.
4. O estado evoluiu para `1.2.0` e lê documentos `1.1.0` sem os novos campos.
5. Falhas de staging, execução e persistência são normalizadas como infraestrutura.
6. Fonte, ref e SHA-256 do oracle são persistidos fora do workspace executável.
7. O interrupt humano publica o tipo real do checkpoint.

Durante o hardening, escrita textual no Windows revelou conversão LF/CRLF capaz de invalidar hashes. Artifacts e oracle passaram a usar escrita binária UTF-8 e possuem regressão dedicada.

## Evidência

- core: 178 descobertos, 155 aprovados e 23 opt-in; branch coverage 88%;
- frameworks/workflow opcional: 18/18;
- Docker: 15 descobertos, 14 aprovados e um skip por privilégio local de symlink no Windows;
- integração 5.3 real: teste gerado e oracle executados em containers, workspaces separados/read-only, evidências distintas e cleanup confirmado;
- `git diff --check`: sem erros;
- secret scan e auditoria do pacote devem ser repetidos imediatamente antes do commit.

## Limites preservados

- o fluxo 5.3 ainda não é o default da CLI;
- não há alegação de execução segura de código hostil ou uso em produção;
- `SUT_DEFECT_SUSPECTED` continua exigindo decisão humana;
- aprovação local não substitui CI pública nem decisão humana de publicação.

## Parecer

Os critérios técnicos do incremento 5.3 estão atendidos localmente. Recomenda-se publicar como pré-alpha `0.1.0a2` somente após secret scan, package audit, commit e três jobs verdes na CI pública.
