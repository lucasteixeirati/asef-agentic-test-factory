# Relato — Incremento 5.7.2 Security Dataset

- **Data:** 2026-07-16
- **Estado:** implementação e revisão local concluídas

Lucas autorizou a 5.7.2 após o fechamento da primeira fatia. Foram criados os doze casos públicos, loader estrito, executores internos, runner, reports e `asef security`.

A primeira prova real não foi verde: SEC-004 terminou `UNSUPPORTED` porque o argv fixo de criação da junction estava incorreto. A suite reportou 11/12 e exit de infraestrutura, preservando a semântica fail-closed. O comando foi corrigido para uma chamada interna fixa de junction e o caso passou isoladamente.

A execução final `security-20260716T115701Z-322d5aef` passou 12/12 com hash `e386538869acc970a86d935b7068c794e5522b884caf327a953b3b4434b1818b`. Os resource attacks foram limitados, SEC-010 provou autoridade do host sem alegar robustez universal do modelo e não restaram containers `asef-*`.

A regressão final ficou em 287 descobertos, 258 aprovados e 29 skips opcionais, com branch coverage de 85,78%. O secret scan passou no source e na evidência da suite. Lifecycle hardening permanece fora desta fatia.

A revisão corrigiu ainda a fronteira application/adapter, validação UTF-8 do dataset, verificação obrigatória do target de junction e continuidade após control failure. Com os findings encerrados, a 5.7.2 foi aprovada localmente.
