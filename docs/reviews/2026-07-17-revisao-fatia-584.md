# Revisão técnica — fatia 5.8.4

- **Data:** 2026-07-17
- **Estado:** aprovada localmente
- **Escopo:** arquitetura real, evidência/avaliação/segurança, suporte e contribuição

## Findings corrigidos

1. A arquitetura pública vigente ainda era o documento prospectivo do walking skeleton. Foi criada uma visão consolidada do fluxo e das autoridades realmente implementadas.
2. A árvore de evidências omitia snapshot, state, attempts, oracle, quality e os dois reports. O modelo agora distingue cada papel, hashes no manifest e limites de integridade.
3. Avaliação não separava a demo linear do oracle combinado nem explicava o alcance das baselines. A interpretação de acceptance, quality, Smoke/Security e validade ficou explícita.
4. Segurança não descrevia a superfície do `AlphaRunReport`. Conteúdo proibido, verifier, integridade e transação recuperável foram ligados ao threat model.
5. A matriz de linguagens apresentava intenções como decisão proposta. Ela agora deriva de `languages.py`: Python experimental; Node/Java planned e apenas startup histórico.
6. Hosts, sandbox, live, cleanup e datasets estavam repetidos em documentos diferentes. `support-and-limitations.md` passou a ser a fonte canônica.
7. CONTRIBUTING não cobria extras, matriz de testes, fronteiras de import, conformance ou extensão. O guia geral e o adapter guide cobrem esses fluxos.
8. Faltava código de conduta. A política pública foi adicionada; os templates existentes foram auditados e preservados, com um check adicional no PR.

## Evidências

- arquitetura, suporte, adapter guide e código de conduta presentes;
- 115 arquivos Markdown verificados, sem link local quebrado;
- claims confrontados com `application/ports.py`, `languages.py`, stores, contratos e workflow de CI;
- 337 testes aprovados, com 33 skips opcionais;
- branch coverage geral: 85,34%;
- secret scan dos documentos públicos aprovado;
- `git diff --check` aprovado;
- nenhuma chamada live, Docker, alteração de código do produto, package audit ou CI desta fatia.

## Limitações da revisão

O checker offline permanente e sua auditoria de anchors/claims pertencem à 5.8.5; nesta fatia a verificação de links foi uma inspeção local ad hoc. Smoke 20/20, Security 12/12 e quality mantêm as evidências já publicadas pela 5.7, mas não foram reexecutados porque a 5.8.4 altera somente documentação/comunidade. Wheel/sdist e experiência instalada também permanecem para a 5.8.5.

## Parecer

A 5.8.4 atende os critérios 25 a 28 de seu plano e está aprovada localmente. O Alpha agora possui uma descrição arquitetural coerente com o código, suporte sem promoção indevida e um caminho de contribuição que preserva as fronteiras do core. A conclusão não autoriza 5.8.5, commit, push, CI, candidata, release ou Gate 5.

