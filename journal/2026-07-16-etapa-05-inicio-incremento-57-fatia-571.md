# Relato — Início do incremento 5.7 e fatia 5.7.1

- **Data:** 2026-07-16
- **Estado:** planejamento aprovado; implementação limitada à 5.7.1
- **Dependência:** pré-alpha `v0.1.0a4`

Lucas aprovou explicitamente o planejamento do incremento 5.7 e autorizou somente a primeira fatia. Nenhuma autorização foi inferida para dataset materializado, runner, hardening Docker, CLI doctor, cleanup mutável, CI ou release.

A implementação começou pelos contratos neutros. A matriz Security associa cada ID `SEC-001` a `SEC-012` a um executor interno e outcome fixos, impedindo que manifests forneçam comando, imagem ou mount. Resultados distinguem pass, failure, erro de infraestrutura e primitive unsupported. O report agregado só é aceito com doze passes.

Os contratos do doctor limitam facts e texto público, usam códigos estáveis e aceitam apenas recomendações enumeradas. Retenção foi formalizada com efêmeros imediatos, evidência final explícita, logs rotativos, CI em sete dias, debug sanitizado e tombstones preservados. Cleanup nasce em dry-run, raiz fixa `.asef` e sem executor de remoção.

A caracterização local confirmou uma limitação importante do Windows/Python atual: junctions podem ser detectadas, porém `rmtree` não anuncia resistência a ataques de symlink e remoção por `dir_fd` não existe. O runtime de contratos publica `RECURSIVE_APPLY_DRY_RUN_ONLY`. O teste de criação real de symlink foi ignorado por privilégio do host e não foi transformado em pass.

Os 17 testes direcionados iniciais terminaram com 16 aprovações e um skip explícito da fixture de symlink. A regressão completa, coverage e secret scan ainda serão executados antes do fechamento da fatia.

## Fechamento local da fatia

Os testes adversariais foram ampliados antes da regressão final porque a primeira medição deixou a cobertura geral em apenas 85,09%, próxima demais do gate. A suíte direcionada passou a conter 24 testes, cobrindo schemas, enums, reconciliação, sanitização, policy, dry-run, tombstones e overclaim de filesystem.

Na regressão final:

- 277 testes foram descobertos;
- 249 executaram e passaram;
- 28 foram ignorados por dependências opcionais/Docker, incluindo a fixture real de symlink sem privilégio;
- branch coverage geral ficou em 86,80%;
- `security_contracts.py` ficou em 94,90%;
- compilação, `git diff --check` e secret scan passaram.

A fatia 5.7.1 está implementada localmente e pronta para revisão. Não foram criados manifests `SEC`, loader, runner, comandos de CLI, labels Docker, executor de doctor, deleção de filesystem, novo job de CI, versão ou release.

## Revisão técnica

A revisão não aprovou automaticamente a primeira implementação. Quatro findings exigiram correção:

1. o doctor ainda não materializava `HEALTHY`, `DEGRADED` e `BLOCKED`, nem duração/timeout por check;
2. fingerprints de Security e o hash do plano de cleanup eram apenas digests bem formados, sem reconciliação com os fatos;
3. o parser poderia converter uma string JSON em sequência de caracteres onde uma lista era exigida;
4. a inspeção não rejeitava explicitamente uma própria raiz `.asef` materializada como symlink/junction.

As correções adicionaram matriz de facts por check, versões/perfil no report do doctor, fingerprints derivados, plan hash verificável, arrays estritos e rejeição da raiz linkada. Retenção também passou a exigir exatamente 1 MiB + dois backups para logs, sete dias sanitizados para CI, cassette live não publicável e debug explícito/sanitizado.

Uma prova exploratória real criou uma junction temporária sob `.asef`. A inspeção retornou `JUNCTION`, o target permaneceu intacto e a fixture foi removida por paths literais. A prova não habilita apply recursivo nem encerra SEC-004.

Após as correções, a regressão final descobriu 278 testes: 249 passaram e 29 integrações opcionais foram ignoradas. A cobertura geral ficou em 86,90% e o novo módulo em 94,78%. Compilação, diff check, import público e secret scan passaram. A revisão aprovou localmente a 5.7.1; a 5.7.2 permanece dependente de nova decisão.
