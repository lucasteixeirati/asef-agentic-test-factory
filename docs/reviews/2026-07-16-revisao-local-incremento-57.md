# Revisão local final — incremento 5.7

- **Data:** 2026-07-16
- **Candidata:** `0.1.0a5`
- **Estado:** aprovada tecnicamente após CI pública; decisão de publicação pendente

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

## Evidência pública

- checkpoint funcional: `2de3c44`;
- GitHub Actions: [`29528937211`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29528937211);
- seis jobs aprovados: `core`, `framework-spikes`, `docker-security`, `alpha-smoke`, `quality-capabilities` e `alpha-security`;
- o `alpha-security` aprovou Security 12/12, doctor instalado, prova Linux de symlink/cleanup recursivo, cleanup dry-run/apply controlado, ausência de containers gerenciados e secret scan das evidências;
- reports sanitizados foram publicados pelo job com retenção de sete dias.

## Riscos residuais

- apply recursivo permanece bloqueado no Windows por capability, sem fallback;
- a política de descarte não promete secure erase;
- reports consolidados e experiência externa pertencem ao 5.8/5.9;
- a candidata ainda não possui tag ou pré-release pública.

## Parecer

A candidata atende o desenho e os critérios técnicos da 5.7. O checkpoint foi publicado e os seis jobs passaram; portanto, o incremento está tecnicamente aprovado e pode ser recomendado para publicação como `v0.1.0a5`. Este parecer não cria nem aprova release/tag, não fecha o Gate 5 e não inicia a Etapa 6. Essas decisões permanecem explícitas e humanas.
