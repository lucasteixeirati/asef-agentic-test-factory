# Revisão técnica — fatia 5.9.1

- **Data:** 2026-07-17
- **Estado:** aprovada por Lucas; protocolo liberado somente após preflight `READY`
- **Escopo:** inventário congelado, contrato de sessão, checkers, CI e reconciliação documental

## Resultado

**Recomendação: aprovar a 5.9.1 sem iniciar automaticamente a 5.9.2.**

O inventário é mecânico e não finge ser o pacote decisório final. Ele mantém G5-19 `PARTIAL`, G5-18 com risco residual e a decisão `PENDING_HUMAN`/`NOT_READY`. Release, assets e CIs estão congelados; o checker compara valores conhecidos, não apenas formatos.

## Controles revisados

- G5-01 a G5-20 aparecem exatamente uma vez e em ordem;
- 40 referências primárias permanecem contidas e existentes;
- wheel/sdist, tamanhos e SHA-256 conferem com a release pública;
- cada CI contém exatamente os sete jobs canônicos;
- protocolo/template possuem seções mínimas obrigatórias;
- `external_evaluation.status` é `NOT_STARTED` e `results` é vazio;
- decisão de aprovação contraditória com item parcial é rejeitada;
- paths absolutos, traversal e evidência ausente são rejeitados;
- PII conhecida é rejeitada inclusive quando aninhada;
- sessão `VALID` exige consentimento, privacidade, elegibilidade, tarefas centrais sem intervenção e ausência de crítico/alto aberto;
- docs checker compara a última release declarada à metadata em README, quickstart e suporte;
- `public-experience` executa o novo checker sem novo job, rede, secret ou participante.

## Findings da revisão

1. A primeira execução apontou `datasets/smoke/manifest.json`, que não existe porque o Smoke usa dez diretórios por caso. A evidência foi substituída pelo catálogo real; checker final 20/20 e 40 referências.
2. A invocação inicial de testes tentou importar `tests.*`, mas `tests` não é package. A validação foi repetida por discovery e passou.
3. A revisão exigiu comparação contra digests congelados e validação semântica de sessão `VALID`; ambos foram adicionados com testes adversariais.
4. Quickstart e suporte ainda continham estado histórico da `v0.1.0a5`; as duas fontes foram corrigidas e ganharam proteção automática.

Todos os findings foram encerrados antes deste parecer.

## Validação

- Gate checker: 9/9;
- docs checker: 5/5;
- inventário: 20 critérios, 40 evidências, zero findings;
- documentação: 122 arquivos, 107 links, zero findings;
- regressão core: 355 testes, 33 skips opcionais;
- branch coverage: 85%, threshold atendido;
- secret scan focal: aprovado;
- `git diff --check`: aprovado.

## Limites preservados

- nenhum participante foi contatado;
- nenhuma sessão, preflight ou chamada live ocorreu;
- nenhum resultado externo foi materializado;
- nenhuma mudança foi feita no runtime/package;
- nenhuma tag, release ou decisão do Gate 5 foi criada;
- 5.9.2 a 5.9.6 permanecem não autorizadas.

## Próximo checkpoint

Lucas deve revisar o protocolo, o template e este parecer. Aprovar a 5.9.1 encerra somente esta fatia; o ensaio da release da 5.9.2 depende de autorização posterior e separada.
