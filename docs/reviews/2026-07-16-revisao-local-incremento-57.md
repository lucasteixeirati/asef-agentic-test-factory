# Revisão local final — incremento 5.7

- **Data:** 2026-07-16
- **Candidata:** `0.1.0a5`
- **Estado:** concluída e publicada como pré-alpha `v0.1.0a5`

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
- wheel publicado SHA-256: `6b4d191705a9ddf4a513b3e33f4df021bae477e4a77b5149e713a42b055e937c`;
- sdist publicado SHA-256: `783c1c8a2beb6285f3cbef5a127a8c59cd778e3ae23c682c795e6a0bb76080fc`;
- instalação isolada confirmou metadata `0.1.0a5` e doctor `DEGRADED/READY`;
- zero containers ASEF residuais;
- workflow YAML: seis jobs, `alpha-security` com 13 passos.

## Evidência pública

- checkpoint funcional: `2de3c44`;
- GitHub Actions: [`29528937211`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29528937211);
- CI documental final: [`29530753021`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29530753021);
- seis jobs aprovados: `core`, `framework-spikes`, `docker-security`, `alpha-smoke`, `quality-capabilities` e `alpha-security`;
- o `alpha-security` aprovou Security 12/12, doctor instalado, prova Linux de symlink/cleanup recursivo, cleanup dry-run/apply controlado, ausência de containers gerenciados e secret scan das evidências;
- reports sanitizados foram publicados pelo job com retenção de sete dias.
- tag anotada e [pré-release `v0.1.0a5`](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a5) publicadas em 2026-07-16.

## Riscos residuais

- apply recursivo permanece bloqueado no Windows por capability, sem fallback;
- a política de descarte não promete secure erase;
- reports consolidados e experiência externa pertencem ao 5.8/5.9;
- o projeto permanece experimental e não oferece isolamento absoluto para código arbitrariamente hostil.

## Parecer

A candidata atende o desenho e os critérios técnicos da 5.7. Após aprovação humana, a tag anotada, o wheel, o sdist e a pré-release `v0.1.0a5` foram publicados e verificados. O incremento 5.7 está encerrado. Este parecer não fecha o Gate 5 e não inicia a Etapa 6; o próximo passo é planejar o 5.8 separadamente.
