# Relato — incremento 5.9.1 inventário e protocolo

- **Data:** 2026-07-17
- **Estado:** concluído localmente; revisão humana pendente
- **Autorização:** Lucas aprovou o plano 5.9 e autorizou somente a fatia 5.9.1

O inventário `1.0.0` congelou a pré-release `v0.1.0a6`, commits, assets, tamanhos, digests e três execuções públicas de sete jobs. Os vinte critérios G5 receberam quarenta referências primárias existentes. O estado inicial preserva G5-18 com risco residual de compreensão externa e G5-19 parcial; portanto, a recomendação técnica permanece `NOT_READY` e a decisão `PENDING_HUMAN`.

O protocolo `ASEF-EXT-ALPHA 1.0.0` e o template de observação foram escritos antes de qualquer sessão. Eles excluem PII, gravação e código real; definem participante elegível, consentimento, tarefas EXT-01 a EXT-08, intervenção, rubrica, validade e severidade. Nenhum participante foi contatado e nenhum resultado foi criado.

O checker mecânico valida inventário, release congelada, sete jobs, paths contidos, protocolo, template, estados G5 e ausência de decisão prematura. O contrato futuro de resultado rejeita PII aninhada, consentimento/privacidade ausentes, tarefas inválidas, intervenção central e finding crítico/alto aberto em sessão `VALID`. O job `public-experience` passou a executar essa checagem offline.

A inspeção do planejamento encontrou versões históricas no quickstart e em suporte/limitações. Ambas foram reconciliadas com `0.1.0a6`; o docs checker agora falha quando uma fonte canônica declara outra última release.

Validação local: 9 testes do Gate checker; 5 testes documentais; inventário 20 critérios/40 evidências sem findings; documentação 122 arquivos/107 links sem findings; secret scan verde; regressão de 355 testes com 33 skips opcionais e branch coverage de 85%. Não houve mudança no runtime/package nem justificativa para `0.1.0a7`.

Próxima decisão: revisar o protocolo e a fatia 5.9.1. A 5.9.2 não foi iniciada.
