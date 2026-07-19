# Da skill ao envelope de run

**Estado editorial:** revisado e aprovado pelo autor em 2026-07-19.

A primeira API revelou uma diferença entre demonstrar uma função e construir um produto. Gerar um plano e fazer um request local era suficiente para provar o mecanismo, mas não para responder perguntas operacionais: qual execução consumiu o modelo, quem revisou o plano, quantos requests eram permitidos, qual arquivo foi realmente executado e que evidência sustentou a conclusão?

O estado do primeiro workflow já respondia perguntas semelhantes, porém havia nascido para teste unitário. Reutilizá-lo por conveniência levaria nomes e transições de pytest para API e, depois, para browser e Java. A alternativa foi extrair um envelope de capability run: identidade, política, budget, usage, fatos e evidências comuns; plano e resultado continuam específicos da skill.

A fronteira Docker trouxe outra correção de expectativa. “Executar API no container” parece simples até lembrar que `--network none` impede alcançar o loopback do host. A prova honesta colocou fixture e cliente dentro do mesmo container. Ela comprova o isolamento e o contrato de resultado, não o acesso seguro a um serviço real. A próxima arquitetura de rede terá de ser projetada explicitamente, não obtida removendo uma proteção.

Esta passagem sugere uma tese para a evolução do ASEF: generalizar somente o que duas capacidades realmente compartilham, e preservar como limitação tudo o que ainda foi provado apenas em fixture.
