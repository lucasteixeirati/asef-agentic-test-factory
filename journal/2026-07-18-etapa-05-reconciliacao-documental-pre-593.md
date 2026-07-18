# Relato — reconciliação documental anterior à 5.9.3

- **Data:** 2026-07-18
- **Estado:** reconciliação concluída; sessão externa aguardando participante elegível

Após a publicação e o postflight de `v0.1.0a7`, Lucas solicitou uma reconciliação transversal antes da avaliação externa e autorizou acelerar as quatro fatias restantes da Etapa 5 sem adicionar features.

Foram reconciliados o Planejamento Mestre, cabeçalhos de progresso das Etapas 4/5, plano 5.9, critérios e inventário do Gate 5, checker mecânico, mapa de fontes do livro, proveniência editorial, EXP-001 e mapa de governança. O EXP-001 agora aponta para a decisão já aceita na ADR-008; o livro não mantém o bloqueio a6 como vigente; e G5-01, G5-17 e G5-20 referenciam release e CIs atuais.

O inventário G5 foi promovido à revisão `1.1.0` sobre `v0.1.0a7`, preservando o histórico do preflight a6 e mantendo `results` vazio. O checker congela release, assets, revisão e matriz pública, rejeita resultado prematuro e passa a carregar/validar o resultado anonimizado em uma sessão concluída ou bloqueada.

O fluxo acelerado preserva quatro decisões humanas: autoridade/consentimento da sessão, remediação material ou nova release, publicação do resultado anonimizado e decisão final do Gate 5. A 5.9.3 não será simulada: depende de QE externo humano, elegível, consentido e usando somente material público.

A validação local aprovou 13 testes específicos do Gate, 360 testes na regressão completa com 33 skips opcionais, 20 critérios/40 evidências no inventário e 130 arquivos/117 links documentais, sem findings funcionais ou documentais.

## Decisão posterior sobre participante

Lucas confirmou que não haverá QE externo neste fechamento, consentiu com a avaliação e com a publicação somente do resultado anonimizado, e definiu o chat como canal. A avaliação externa foi marcada `DEFERRED`, sem resultado fabricado. A 5.9.3 foi iniciada como sessão interna acompanhada com `I01`, cujo papel de autor/mantenedor e viés de conhecimento são obrigatórios no resultado.

Ao preparar o cartão EXT-01, a leitura integral do instrumento revelou que o kit já apontava para a7, mas o corpo do protocolo externo ainda congelava a6. O protocolo foi corrigido para `ASEF-EXT-ALPHA 1.0.1` e para os commits/hashes a7; o checker passou a exigir esses valores. Um protocolo interno separado impede que a sessão informativa seja confundida com independência externa.
