# Revisão final do incremento 5.3

- **Data:** 2026-07-14
- **Escopo:** oracle independente, correção limitada, evidências por tentativa e revisão humana
- **Decisão técnica:** aprovada
- **Publicação:** aprovada como pré-alpha `0.1.0a2`

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
- secret scan do código e dos artefatos de distribuição: aprovado;
- wheel e sdist: construídos e inspecionados;
- instalação limpa do wheel e demo keyless: `SUCCEEDED/ACCEPTED`;
- commit funcional: `1cf687f`;
- CI pública `29360824309`: jobs `core`, `framework-spikes` e `docker-security` aprovados.

## Limites preservados

- o fluxo 5.3 ainda não é o default da CLI;
- não há alegação de execução segura de código hostil ou uso em produção;
- `SUT_DEFECT_SUSPECTED` continua exigindo decisão humana;
- o incremento publicado permanece pré-alpha e experimental.

## Parecer

Os critérios técnicos e de publicação do incremento 5.3 estão atendidos. Os sete findings estão encerrados, os artefatos foram auditados e os três jobs da CI pública passaram. A revisão recomenda e aprova o fechamento como pré-alpha `0.1.0a2`.
