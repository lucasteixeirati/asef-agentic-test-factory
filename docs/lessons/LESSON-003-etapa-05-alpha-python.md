# Lição aprendida — Etapa 5: evidência forte não elimina o limite da autovalidação

- **Data:** 2026-07-18
- **Etapa:** Alpha Python
- **Período analisado:** 2026-07-13 a 2026-07-18
- **Estado:** concluída tecnicamente; estruturação por IA a partir de evidências e relatos explícitos de Lucas

## O que esperávamos

Entregar um Alpha Python instalável, seguro dentro de limites declarados, capaz de gerar e avaliar testes com rastreabilidade, métricas, reports públicos e evidência suficiente para o Gate 5.

## O que aconteceu

O Alpha evoluiu por contratos, adapter pytest em Docker, oracle independente, correção limitada, adapter live com budget, Smoke 20/20, coverage/mutation, Security 12/12, doctor, cleanup e reports tipados. Sete jobs públicos e as releases até `v0.1.0a7` sustentam o recorte técnico.

A preparação externa encontrou uma divergência documental imutável na a6 e forçou a a7. Na avaliação final, a ausência de QE externo levou a uma sessão interna explicitamente assistida. Ela encontrou sobreafirmação inicial de maturidade e segurança, além de uma resposta incompleta para cleanup inseguro. Ambas foram corrigidas; a instalação humana isolada foi adiada e permaneceu risco aceito.

## Evidências

- `docs/evaluations/2026-07-18-alpha-python-release-a7-postflight.json`;
- `docs/evaluations/2026-07-18-alpha-python-internal-evaluation-I01.json`;
- `docs/reviews/2026-07-18-revisao-fatia-593-594.md`;
- `docs/project/measurement-baseline.md`;
- `journal/` e revisões 5.1 a 5.9.

## O que funcionou

- fatias pequenas, gates e releases imutáveis tornaram regressões e correções atribuíveis;
- testes negativos, oracles independentes e execução fora do checkout revelaram premissas invisíveis no caminho feliz;
- separação entre fato, inferência, recomendação e limitação reduziu sobreafirmação;
- a revisão periódica de Lucas sobre testes, logs, objetivo, planejamento e documentação redirecionou o trabalho sem exigir escrita manual de todo o código;
- declarar assistência da IA e ausência de independência preservou a honestidade da evidência.

## O que não funcionou

- a primeira versão do protocolo externo continuou citando a6 mesmo depois de kit e postflight migrarem para a7;
- o checker inicial verificava headings, mas não congelava a identidade interna do protocolo;
- a sessão interna começou com instalação no checkout apesar da instrução de usar material público e ambiente vazio;
- a resposta inicial confundiu progresso técnico com estabilidade e segurança gerais;
- não houve participante externo disponível para observar compreensão independente.

## Papel da IA

- **Sugestões úteis:** implementação, contratos, testes adversariais, documentação, checkers, triagem e síntese editorial;
- **Sugestões corrigidas:** premissas de empacotamento, consistência de release/protocolo, interpretação excessiva de segurança e resposta a cleanup inseguro;
- **Sugestões rejeitadas ou limitadas:** arquitetura de dois centros da ADR-007, expansão silenciosa de escopo e qualquer simulação de participante externo;
- **Decisões humanas:** escopo, checkpoints, releases, aceitação de risco, adiamento externo e futura decisão do Gate.

## Impacto

- **Aplicação:** Alpha Python funcional no recorte experimental publicado;
- **Arquitetura:** core neutro, adapters limitados e evidência tipada permaneceram autoridades separadas;
- **Documentação:** identidade de release e protocolo passou a ser verificada mecanicamente;
- **Livro/jornada:** a autovalidação tornou-se parte da história, não uma evidência escondida ou promovida indevidamente.

## O que faremos diferente

- validar protocolo, kit e release como um único conjunto congelado;
- executar a jornada humana fora do checkout antes de interpretar usabilidade;
- pedir primeiro que o participante declare limitações, evitando que “funcionou” vire “é seguro”;
- coletar feedback real de usuários assim que houver adoção;
- avaliar futuramente um sistema público controlado, desde que o experimento respeite autorização, escopo e a capability real do ASEF.

## Ações

| Ação | Responsável | Etapa alvo | Status |
|---|---|---|---|
| Preservar feedback externo como condição/risco do Gate 5 | Lucas | pós-Alpha | aberto |
| Planejar experimento com SUT público autorizado, sem presumir automação web | Lucas + IA | etapa futura | backlog |
| Manter checker de protocolo/release no Gate | IA sob revisão humana | 5.9.6+ | implementado |
