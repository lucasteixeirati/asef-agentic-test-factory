# Relato — incremento 5.8.1 contrato do Alpha report

- **Data:** 2026-07-16
- **Estado:** concluída e aprovada localmente
- **Dependência:** plano do 5.8 aprovado

Lucas aprovou o plano detalhado do 5.8, autorizando o início exclusivo da fatia 5.8.1. Foi criado o contrato neutro `AlphaRunReport 1.0.0`, com parser estrito e JSON Schema Draft 2020-12 empacotado.

A revisão durante a implementação endureceu paths canônicos, ordem dos budgets no parser, reconciliação do oracle por attempt, links scenario→artifact→execution, IDs contíguos, uniqueness de attempts/capabilities, acceptance funcional e publicação somente de evidence sanitizada e verificada. Dois testes adversariais inicialmente falharam porque seus próprios fixtures atingiam invariantes anteriores ao alvo; os fixtures foram corrigidos sem afrouxar o contrato.

O threat model separa conteúdo permitido/proibido e reserva builder, filesystem verifier, renderer Markdown, store, manifest e CLI para a 5.8.2. Nenhum report real foi migrado nesta fatia.

Na auditoria final, a cobertura arredondada inicialmente ocultou 84,97%, abaixo do piso exato. Foram adicionados casos adversariais reais para fields aninhados, sem alterar o limiar ou omitir módulo. O resultado final foi 13 testes específicos aprovados; regressão de 331 testes com 33 skips opcionais; branch coverage geral de 85,10%; JSON Schema validado; e wheel/sdist contendo contrato e schema. Não houve commit, push, CI, versão ou release.
