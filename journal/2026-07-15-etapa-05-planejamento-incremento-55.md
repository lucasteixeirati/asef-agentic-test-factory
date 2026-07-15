# Relato — Planejamento do incremento 5.5

- **Data:** 2026-07-15
- **Estado:** plano aprovado; implementação iniciada pela fatia 5.5.1
- **Dependência:** `v0.1.0a3` publicada e evidências do Gate 5 sincronizadas

O planejamento do Smoke Dataset partiu dos quatro seeds materiais e dos componentes implementados até o 5.4. A auditoria mostrou que completar dez JSONs não seria suficiente: faltam uma fixture demo separada do contrato semântico, contexto para os SUTs Alpha, sequência gravada de correção, composição end-to-end do coordenador do 5.3 e comparação agregada expected/actual.

O finding mais importante foi o SMK-006. O catálogo previa erro de sintaxe seguido de correção, mas `UnitSkill` bloqueia corretamente sintaxe inválida antes do Docker. O plano preserva a policy e troca a fixture por erro de coleta/execução sintaticamente válido, permitindo que pytest produza `TEST_ERROR` e que a matriz determinística autorize uma correção.

O plano propõe que resultados negativos esperados — espera humana, budget, infraestrutura e policy — contem como conformidade quando coincidirem com expectations versionadas. O relatório não será chamado de benchmark. A CI executará a suíte duas vezes, sem chave ou rede de provider, e comparará fingerprints semânticos que excluem IDs, tempo e outros fatos operacionais variáveis.

A implementação foi dividida em seis fatias com critérios de parada. Lucas aprovou explicitamente o plano em 2026-07-15, autorizando o início do código pela fatia 5.5.1. Alterações de fixtures e CI permanecem ordenadas nas fatias seguintes do plano aprovado.

## Início da implementação

A fatia 5.5.1 começou com contratos separados para fixture demo, observação/resultados e relatório agregado. Também foi criado o loader fail-fast dos dez casos, incluindo validação de enums, versões, referências, limites de tamanho, isolamento do oracle, hash efetivo e ausência de side effects antes da validação completa. Os testes adversariais cobrem ausência/extra, divergência de versão, campo duplicado, referência inexistente, traversal e vazamento do oracle.

Na sequência, os dez casos foram materializados e conectados ao fluxo Alpha. O SMK-006 usa import inexistente sintaticamente válido para alcançar `TEST_ERROR` e só então consumir sua correção gravada. O runner agregado preserva resultados negativos como matches quando coincidem com o contrato, detecta fingerprint instável entre repetições e grava reports sem sobrescrita. O comando público e o job de CI foram adicionados; a execução Docker completa pertence à revisão final do incremento.

## Revisão local

O primeiro Smoke Docker terminou 5/10 porque os cinco casos executáveis encontraram o limite de comprimento de path do Windows na combinação de dois nomes temporários UUID. O diagnóstico veio das evidências persistidas, não de tentativa e erro sobre a lógica dos casos. Os nomes temporários internos foram encurtados; os nomes finais e as garantias de escrita atômica permaneceram iguais.

Depois da correção, a suíte passou 10/10 e, na repetição final, 20/20 com fingerprints estáveis. O hash efetivo final foi `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`. O loader também passou a incorporar todos os arquivos do `read_scope` no hash, fechando uma lacuna percebida durante a revisão. Regressão, coverage, integrações Docker, wheel isolado, secret scan e integridade do diff ficaram verdes.

O commit funcional `06cc892` foi publicado e a CI `29442732993` aprovou `core`, `framework-spikes`, `docker-security` e `alpha-smoke`. O job Smoke confirmou novamente 20/20, report válido, evidências sem secrets e artifact sanitizado. O incremento foi formalmente encerrado; o Gate 5 permanece aberto.
