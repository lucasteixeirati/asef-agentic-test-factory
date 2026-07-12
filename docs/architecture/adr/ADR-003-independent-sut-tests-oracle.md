# ADR-003 — Independência entre SUT, testes gerados e oracle

- **Status:** aceita
- **Data:** 2026-07-11
- **Responsável:** Lucas

## Contexto

Gerar SUT e testes a partir da mesma interpretação pode produzir testes verdes para um comportamento incorreto. Uma LLM julgadora usando o mesmo contexto também pode reforçar a circularidade.

## Drivers

- validade da avaliação;
- detecção real de defeitos;
- independência do oracle;
- confiança educacional;
- prevenção de vazamento de holdout.

## Opções consideradas

1. Gerar implementação e testes no mesmo workflow e aceitar a execução.
2. Usar outra LLM como único juiz.
3. Usar SUT existente no fluxo principal e oracles/testes de referência independentes.

## Decisão

Adotar a opção 3:

- WF-001 recebe SUT existente;
- testes ocultos não entram no prompt de geração;
- oracles são determinísticos ou curados quando possível;
- LLM-as-a-judge é evidência complementar;
- SUT gerado é permitido apenas em laboratório explicitamente identificado;
- possível defeito no SUT exige revisão humana.

## Consequências

### Positivas

- menor circularidade;
- evidência de qualidade mais defensável;
- separação entre erro do teste e defeito suspeito.

### Negativas

- maior custo de curadoria dos datasets;
- nem todo requisito terá oracle completo;
- holdouts exigem governança.

## Revisitar quando

Novas técnicas fornecerem independência equivalente e mensurável para geração conjunta, sem expor o oracle ao componente avaliado.

