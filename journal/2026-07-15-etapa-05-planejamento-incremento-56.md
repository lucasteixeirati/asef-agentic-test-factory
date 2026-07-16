# Relato — Planejamento do incremento 5.6

- **Data:** 2026-07-15
- **Estado:** plano aprovado; implementação iniciada pela fatia 5.6.1
- **Dependência:** incremento 5.5 encerrado com Smoke Dataset 20/20 e CI pública verde

O planejamento do 5.6 começou pela distinção entre ferramentas usadas para testar o próprio ASEF e capabilities que avaliam um SUT. O repositório já possui contratos neutros para coverage e mutation, branch coverage do core e um mutation pilot periódico, mas ainda não possui adapters que apliquem essas medições ao artifact aceito do fluxo Alpha.

A principal decisão foi separar a avaliação funcional da avaliação de qualidade. Coverage e mutation serão evidências tipadas anexadas à run. Uma capability ausente, parcial ou com budget esgotado permanecerá visível, mas não será convertida em zero, sucesso ou suspeita de defeito do SUT.

A baseline também mostrou que a imagem pytest validada não deve receber mutmut e suas dependências. O plano propõe uma imagem de qualidade separada, com versões e hashes pinados, mantendo fonte e testes originais read-only. Coverage grava dados em área temporária; mutation trabalha sobre uma cópia descartável dentro do container Linux, porque mutmut 3 requer `fork` e não deve depender do host Windows.

Há uma incerteza técnica deliberadamente preservada: coverage.py oferece JSON público estruturado, mas mutmut não documenta contrato equivalente nem um limite universal de quantidade de mutantes. A primeira fatia caracterizará a versão `3.6.0` e deverá provar admission control real. Se o limite só puder ser verificado depois de executar todos os mutantes, a implementação será interrompida para rever a ferramenta; o budget não será simulado por truncamento do report.

O plano foi dividido em seis fatias: caracterização/contratos, imagem, coverage, mutation, integração/report e CI/revisão. G5-12 e G5-13 permanecem parciais até que outputs nativos, normalização, budgets, imutabilidade e CI sejam comprovados.

## Início da 5.6.1

Lucas aprovou explicitamente o plano em 2026-07-15. A implementação começou pela caracterização do wheel oficial `mutmut 3.6.0`, cujo SHA-256 observado foi `a9f5b8dcf6cbf9496769d7cf8bdbba37a0ec709ad98f88d103238b62f10bdf37`.

A inspeção confirmou metadata JSON nativa por arquivo e seleção de mutantes por nome/padrão, mas nenhuma opção `--max-mutants`. Também revelou estados adicionais: `no tests`, `skipped`, `suspicious`, `segfault`, `caught by type check`, interrupção e não verificado. O desenho adotou descoberta seguida de admissão determinística e execução apenas dos nomes selecionados; o hard timeout continua externo.

O contrato inicial de mutation precisou ser corrigido. Antes, ele proibia `mutants_total` maior que o budget, o que esconderia mutantes descobertos e deferidos. Agora o total representa descobertos, o budget limita processados e `not_run` reconcilia os demais.

Foram adicionados requests neutros, estados de observation, report agregado e admission control puro. Os primeiros testes encontraram e corrigiram uma perda dos percentuais derivados de coverage na serialização aninhada. Após o ajuste, os dez testes novos, os dez contratos Alpha e os sete testes da matriz de oracle passaram.

## Implementação e revisão local

As seis fatias foram executadas no mesmo dia. A imagem de qualidade foi mantida separada da imagem pytest e teve coverage `7.10.7`, mutmut `3.6.0`, pytest `8.3.3` e transitivas fixadas por hashes. O primeiro download cross-platform não conseguiu resolver wheels compatíveis de `libcst`/`pyyaml-ft`; a solução foi resolver os artifacts dentro da própria base Linux pinada, alinhando o lock ao ambiente real de execução.

A tentativa inicial de usar uma seleção sentinela para apenas gerar metadata falhou porque o mutmut rejeita seleções sem correspondência. A implementação foi redirecionada para um exporter interno e estreitamente acoplado à versão pinada somente na fase de descoberta; a execução dos mutantes admitidos continua usando a CLI pública. Outra correção importante impediu que o driver confiasse no `pyproject.toml` do SUT: a configuração de source e testes é agora produzida exclusivamente a partir do request validado, dentro da cópia descartável.

A fixture mínima produziu 7/8 linhas, 1/2 branches e cinco mutantes descobertos. O budget admitiu três: um morto e dois sobreviventes; dois ficaram explicitamente não executados. No SUT de referência, a baseline local observou 11/11 linhas, 2/2 branches e nove mutantes, dos quais oito foram admitidos, cinco mortos, três sobreviventes e um deferido. Esses números são evidência da fixture e da suíte pequena, não um benchmark nem meta universal.

O fluxo integrado revelou uma diferença de paths no Windows: o diretório da run era resolvido para absoluto, mas a base usada no `EvidenceRef` permanecia relativa. A revisão corrigiu a canonicalização e acrescentou a prova end-to-end. Também foi fechado um risco de diagnóstico sensível e garantido que JSON nativo malformado seja preservado como evidência de uma observation `FAILED`, em vez de escapar do adapter e ser perdido.

Ao final da primeira revisão local, 253 testes foram descobertos, 226 executados e 27 integrações opcionais ignoradas; branch coverage alcançou 86%. A matriz Docker aprovou 17 de 18 testes, com apenas o skip conhecido de symlink no Windows, e o Smoke permaneceu 20/20.

Na revisão de publicação, dois findings adicionais foram fechados antes do commit. Os testes Docker de quality receberam opt-in próprio para não dependerem da imagem nova dentro do job histórico `docker-security`. O serviço de quality passou também a reemitir o report JSON/Markdown depois de anexar `facts["quality"]`, quando a avaliação funcional Alpha está disponível. A candidata foi promovida para `0.1.0a4`; o próximo passo é publicar o commit e observar os cinco jobs da CI antes de criar tag/release.
