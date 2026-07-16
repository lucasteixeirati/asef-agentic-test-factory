# Caracterização do mutmut 3.6.0 para a capability do SUT

- **Data:** 2026-07-15
- **Fatia:** 5.6.1
- **Estado:** caracterização estática e desenho de admission control concluídos; prova Docker pertence às fatias 5.6.2/5.6.4
- **Distribuição observada:** `mutmut-3.6.0-py3-none-any.whl`
- **SHA-256 observado:** `a9f5b8dcf6cbf9496769d7cf8bdbba37a0ec709ad98f88d103238b62f10bdf37`
- **Origem:** PyPI oficial, publicado em 2026-06-06

## Objetivo

Determinar se a versão pinada oferece dados suficientes para normalização auditável e se o budget de quantidade pode interromper a execução de mutantes antes do trabalho ilimitado. Esta caracterização não promove a capability para `available` e não substitui a conformance real no container Linux.

## Interface observada

O entry point público é `mutmut = mutmut.__main__:cli`. O comando `run` aceita `--max-children` e uma lista opcional de nomes/padrões de mutantes. Não existe `--max-mutants` na CLI 3.6.0.

A execução:

1. copia fonte/configuração para `mutants/`;
2. gera todos os mutantes do escopo;
3. persiste metadata JSON por arquivo em `mutants/<source>.meta`;
4. coleta associação entre testes e funções;
5. valida a suíte limpa e a capacidade de forçar uma falha;
6. seleciona nomes/padrões pedidos;
7. executa os selecionados com `fork`, até `--max-children` em paralelo.

O formato `.meta` contém:

- `exit_code_by_key`;
- `type_check_error_by_key`;
- `durations_by_key`;
- `estimated_durations_by_key`.

Esse JSON é nativo e estruturado, mas não é documentado como API pública. O driver ASEF poderá lê-lo somente sob pin exato, schema defensivo e fixture de conformance. O arquivo bruto será preservado como evidência.

## Estados nativos

| Estado mutmut | Origem observada | Normalização neutra proposta |
|---|---|---|
| `killed` | teste falhou com o mutante | `killed` |
| `survived` | testes passaram | `survived` |
| `timeout` | limite interno/SIGXCPU | `timed_out` |
| `caught by type check` | type checker rejeitou o mutante | `invalid` quando type checking estiver explicitamente configurado |
| `suspicious` | exit code desconhecido | `invalid` + observation `PARTIAL` e limitação nativa |
| `segfault` | processo terminou por falha de memória/sinal | `invalid` + observation `PARTIAL` e limitação nativa |
| `no tests` | nenhum teste associado | `not_run`, preservando motivo nativo |
| `skipped` | ferramenta marcou como ignorado | `not_run`, preservando motivo nativo |
| `not checked` | gerado, ainda não executado | `not_run` |
| `check was interrupted by user` | interrupção | `not_run` + observation `PARTIAL`/`BUDGET_EXHAUSTED` conforme a causa externa |

`mutation_score` permanece calculado somente sobre `killed + survived`. Inválidos, timeout e não executados não entram no denominador.

## Admission control aprovado para implementação

O budget será aplicado em duas fases:

1. **descoberta:** gerar metadata no workspace descartável sem executar mutantes;
2. **admissão:** ler e validar todos os nomes, ordenar canonicamente e selecionar no máximo `max_mutants`;
3. **execução:** chamar `mutmut run` apenas com os nomes admitidos;
4. **normalização:** contar os descobertos não admitidos em `not_run` e preservar o motivo `deferred_by_budget` no output nativo ASEF.

A geração de mutantes ainda possui custo, mas a execução da suíte mutada — parte dominante e potencialmente não limitada — fica restrita antes de começar. O hard timeout do host continua soberano sobre geração, baseline e execução.

O comando público não possui uma fase documentada de “generate only”. A implementação poderá usar um exporter controlado sobre a versão pinada ou uma invocação sentinela provada pela fixture. Essa escolha será fechada no driver da 5.6.2; qualquer mudança de layout/status fará a observation falhar como `UNAVAILABLE`/`FAILED`, sem parser heurístico.

## Correção do contrato `MutationResult`

A regra inicial `mutants_total <= max_mutants` não permitia descrever mutantes descobertos e recusados pelo budget. A 5.6.1 corrigiu a semântica:

- `mutants_total` é o total descoberto;
- `killed + survived + invalid + timed_out` é o total processado;
- o total processado não pode superar `max_mutants`;
- `not_run` reconcilia descobertos não admitidos, sem testes ou interrompidos;
- todas as categorias continuam somando `mutants_total`.

Assim, o report não esconde o universo descoberto e o budget limita trabalho real, não a apresentação.

## Decisão e limitações

Mutmut `3.6.0` foi aprovado para a capability limitada do Alpha porque oferece nomes determinísticos, metadata JSON e execução por seleção explícita. A conformance no container Linux confirmou o exporter pinado e a execução somente dos nomes admitidos.

Limitações abertas:

- metadata é interna e requer pin/conformance forte;
- `--max-children` limita paralelismo, não quantidade;
- timeout interno usa configurações declaradas instáveis pelo projeto;
- geração cria todos os mutantes antes da seleção;
- funcionamento nativo no Windows é rejeitado pela própria ferramenta;
- qualquer upgrade exige nova caracterização e baseline deliberada.

## Conformance fechada no container

A fixture versionada em `examples/python-alpha/quality_conformance` congelou cinco mutantes descobertos. Com `max_mutants=3`, a ordem canônica admitiu três antes de `mutmut run`: um foi morto, dois sobreviveram e os dois restantes foram registrados como deferidos/não executados. A mesma fixture confirmou 7/8 linhas e 1/2 branches pelo JSON nativo do coverage.py.

Uma baseline independente no SUT de referência descobriu nove mutantes e, com budget oito, executou somente os oito admitidos: cinco mortos, três sobreviventes e um deferido. O teste integrado compara hashes antes/depois e confirmou que o mount original permaneceu imutável. Hard timeout, remoção do container, resultado inválido e ferramenta indisponível possuem regressões próprias.

Fontes primárias:

- [mutmut 3.6.0 no PyPI](https://pypi.org/project/mutmut/3.6.0/);
- [documentação oficial do mutmut](https://mutmut.readthedocs.io/en/latest/).
