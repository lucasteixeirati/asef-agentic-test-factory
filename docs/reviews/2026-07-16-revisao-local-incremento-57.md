# Revisão local final — incremento 5.7

- **Data:** 2026-07-16
- **Candidata:** `0.1.0a5`
- **Estado:** recomendada localmente; CI pública e decisão de publicação pendentes

## Escopo entregue

- contratos, threat model e policy;
- Security Dataset `SEC-001..012` e CLI;
- lifecycle Docker com labels, interruption cleanup e orphan detection;
- `asef doctor`;
- `asef cleanup`, tombstones, retention/debug e scanner endurecido;
- job `alpha-security`;
- provas Windows e Linux.

## Evidências locais

- Security Windows: 12/12;
- Smoke: 20/20;
- Linux cleanup/symlink em imagem pinada: 2/2;
- package audit fora do checkout: doctor, demo, cleanup e scanner aprovados;
- matriz Docker/quality: 17 passes e três skips de host em 20;
- regressão: 318 descobertos, 285 passes e 33 skips opcionais;
- branch coverage: 85,16%;
- wheel e sdist `0.1.0a5` inspecionáveis pelo scanner;
- wheel SHA-256: `882b1133c19953c7ef7dda7e3a4ad9065b21e408efceb1029ea3a5e5246e85c4`;
- sdist SHA-256: `082423ef54c8af83c8d8080b72db8c3b83761295a4d83cd598ca1a80215146e3`;
- instalação isolada confirmou metadata `0.1.0a5` e doctor `DEGRADED/READY`;
- zero containers ASEF residuais;
- workflow YAML: seis jobs, `alpha-security` com 13 passos.

## Riscos residuais

- apply recursivo permanece bloqueado no Windows por capability, sem fallback;
- a prova Linux local ocorreu em container; a evidência pública depende do novo job;
- reports consolidados e experiência externa pertencem ao 5.8/5.9;
- a working tree ainda precisa de checkpoint controlado antes da CI.

## Parecer

A candidata local atende o desenho da 5.7 e pode seguir para checkpoint e CI pública. Este parecer não aprova Gate 5, release, tag ou Etapa 6. A aprovação do incremento depende de seis jobs verdes e decisão explícita posterior de Lucas.
