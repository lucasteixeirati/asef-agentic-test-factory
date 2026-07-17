# Estratégia de avaliação

## Princípio de independência

Gerar implementação e testes com o mesmo modelo comprova, no máximo, consistência interna. Quando o resultado é objetivamente verificável, execução e oracle curado têm precedência sobre julgamento generativo. O oracle do fluxo combinado não entra no prompt e possui identidade por hash.

## O que o Alpha avalia hoje

Há dois recortes que não devem ser confundidos:

- a demo pública linear (`asef run`) gera, valida estaticamente e executa um teste recorded; ela não afirma usar o oracle combinado;
- o fluxo combinado/datasets executa teste gerado e oracle curado por tentativa, compara outcomes, limita correções e pode solicitar revisão humana diante de suspeita de defeito.

A aceitação funcional é determinística: execução classificada como pass, contagem positiva, zero falhas/erros e total aprovado reconciliado. Falha de teste, erro de coleta/tooling, policy, budget, provider e infraestrutura permanecem classes distintas. Correção automática só altera o artifact gerado dentro do budget; nunca o SUT.

## Datasets e evidência atual

| Dataset | Situação | Interpretação permitida |
|---|---|---|
| Smoke | 10 casos públicos; baseline executa duas repetições | regressão determinística desses 20 observations e estabilidade de fingerprint |
| Security | 12 controles enumerados | controles observados no ambiente/versão registrados |
| Development | catálogo evolutivo | material para desenvolver contratos e adapters |
| Evaluation / Holdout | planejados | nenhuma alegação estatística geral ainda |
| Language Conformance | catálogo de invariantes | ainda não há suite completa que promova outro perfil |

Caso negativo esperado só é aprovado quando o controle realmente foi observado. Primitive ausente, caso não executado ou falha do runner vira `UNSUPPORTED`/erro, nunca pass.

## Quality capabilities

Coverage e mutation são observações opcionais do perfil Python delimitado. Cada capability separa request, disponibilidade, execução, resultado normalizado, evidência e diagnóstico. `AVAILABLE`, `FAILED`, `UNSUPPORTED` e não solicitado não são equivalentes.

Coverage e mutation score ajudam a localizar lacunas; não provam correção e não são threshold universal de aceitação. Falha ou ausência de quality não reclassifica silenciosamente um resultado funcional já observado. O report deve mostrar a limitação.

## Taxonomia no relatório

`AlphaRunReport 1.0.0` separa:

- **facts:** observações sustentadas por trace/evidence existentes;
- **inferences:** interpretações com bases explícitas;
- **recommendations:** ações de enumeração revisada;
- **limitations:** o que não foi observado ou não pode ser concluído.

JSON é normativo e Markdown não acrescenta conclusões. Integridade `MISSING`/`MISMATCH` impede tratar a referência como verificada, sem fabricar nova decisão funcional.

## Governança de casos

Cada caso deve registrar ID/versão, origem/licença, curadoria, requisito, riscos, oracle, perfil, exposição e histórico. Development e Evaluation não devem ser misturados silenciosamente; holdout exposto muda de categoria. Alteração de ground truth requer revisão e versão/hash novos. LLM-as-a-judge não pode ser evidência única para critério mecanicamente verificável.

## Métricas e validade

Métricas úteis incluem taxa de aceite, primeira tentativa/correção, outcomes de teste/oracle, coverage, mutation, regressões, duração, usage/custo, policies e intervenções. Toda métrica precisa de definição operacional, denominador, ambiente, repetições e dados ausentes explícitos.

As baselines atuais são pequenas, públicas, focadas em um SUT/perfil e parcialmente determinísticas por cassettes. Elas não sustentam generalização para projetos reais, linguagens, providers, distribuição de defeitos, segurança adversarial ampla ou produtividade humana. Resultados live variam e custo é estimado com tarifas fornecidas pelo operador.

Veja a fonte canônica de [suporte e limitações](../project/support-and-limitations.md) e o [guia de interpretação](../guides/report-interpretation.md).

