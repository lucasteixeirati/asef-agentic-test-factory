# Journal — planejamento do Alpha Python

- **Data:** 2026-07-13
- **Etapa:** planejamento da Etapa 5
- **Participantes:** Lucas e GPT-5.6 Sol
- **Estado:** plano aprovado por Lucas; incremento 5.1 autorizado

## Intenção

Transformar a descrição ampla da Etapa 5 em um plano executável antes de alterar o runtime, preservando a ambição técnica do projeto e deixando claro o que pertence ao Alpha Python e o que deve ser validado somente na etapa multilíngue.

## O que foi analisado

Foram cruzados Planejamento Mestre, requisitos v0.1, WF-001, critérios de aceite, datasets, segurança, capability contracts, ADRs aceitos e implementação do walking skeleton. A comparação mostrou que a base já possui budgets, demo gravada, Docker, evidências e checkpoint humano, mas ainda não possui na aplicação pública:

- modo live integrado à porta agêntica atual;
- loop real de correção após falha `pytest`;
- classificações `TEST_ERROR` e `SUT_DEFECT_SUSPECTED` implementadas;
- datasets executáveis;
- coverage e mutation aplicadas ao SUT;
- diagnóstico público do ambiente.

## Decisões propostas

1. Substituir a dependência conceitual de um único calculator por uma suíte pequena de funções Python, com versões corretas e defeitos semeados.
2. Isolar os oracles do prompt e materializá-los somente na avaliação. Como o projeto é público, isolamento significa não exposição ao gerador, não segredo para o leitor.
3. Combinar resultado do teste gerado com oracle independente antes de sugerir defeito no SUT.
4. Permitir no máximo duas correções, sempre restritas ao artifact de teste e preservando cada tentativa.
5. Ligar o modo live à mesma porta, policies e budgets do demo; apenas o adapter de provider muda.
6. Implementar coverage e mutation no perfil Python como prova dos contratos. A Etapa 6 verificará a generalização em TypeScript e Java.
7. Executar os dez casos Smoke e os doze casos Security no Alpha, sem transformar o Smoke Dataset em alegação estatística.
8. Registrar material para o livro durante a construção, deixando retrospectiva e possível artigo condicionados às evidências finais.

## Decomposição

O plano foi dividido em nove incrementos: contratos/SUT, pytest, oracle/correção, live, Smoke Dataset, coverage/mutation, segurança/doctor, documentação pública e auditoria/Gate 5. Vinte critérios objetivos foram propostos para o gate.

## Avaliação crítica

O risco principal não é apenas implementar muitas capacidades. É produzir uma classificação convincente, porém falsa. Sem oracle independente, uma falha pode ser atribuída ao SUT quando o teste gerado está errado; sem isolamento, o mesmo modelo pode reproduzir a resposta do oracle. Por isso, a independência da evidência foi colocada antes do modo live e das métricas mais vistosas.

Também foi evitada uma falsa separação entre Python e multilíngue: coverage e mutation entram agora como adapters Python, pois são necessárias para provar o Alpha; a comparação entre ecossistemas continua pertencendo à Etapa 6.

## Material para o livro

Este planejamento oferece um episódio sobre a diferença entre “automatizar a execução de testes” e “construir evidência para interpretar um resultado”. A contribuição de QA aparece na exigência de um oracle independente, em classificações baseadas em causa e na recusa de usar dez casos como benchmark estatístico.

Outro ponto editorial relevante é a evolução do calculator: ele foi adequado para provar o walking skeleton, mas insuficiente para demonstrar correção, ambiguidade, defeito suspeito e técnicas de avaliação. Evoluir o SUT de referência não invalida o skeleton; mostra como critérios de uma etapa posterior exigem uma fixture mais rica.

## Métricas deste registro

- planejamento realizado no mesmo dia corrido da aprovação do Gate 4;
- nenhum custo adicional de API informado para esta atividade documental;
- nenhuma implementação do runtime alterada;
- dois novos documentos normativos propostos: plano da Etapa 5 e matriz do Gate 5.

## Decisão humana

Lucas aprovou os conteúdos editoriais apresentados e autorizou seguir adiante em 2026-07-13. A decisão foi registrada como aprovação do plano e das quatro escolhas centrais já destacadas: suíte de SUTs pequenos, oracle isolado do prompt, live sob budget explícito e coverage/mutation Python como adapters. A aprovação autoriza apenas o incremento 5.1 e não aprova antecipadamente novos ADRs, o Gate 5 ou a Etapa 6.
