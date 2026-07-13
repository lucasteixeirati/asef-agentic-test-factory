# EXP-007 — Mutation pilot no core determinístico

- **Data:** 2026-07-13
- **Estado:** concluído
- **Ferramenta:** Mutmut 3.6.0 em Python 3.13/Linux

## Hipótese

Line e branch coverage podem permanecer verdes mesmo quando asserts não verificam semântica suficiente. Um recorte pequeno de mutation testing deverá revelar ao menos uma lacuna útil sem impor o custo de mutar todo o projeto.

## Escopo

- `src/asef/runtime/budgets.py`;
- `src/asef/runtime/__init__.py`;
- `src/asef/outcomes.py`;
- testes de budgets e contratos/outcomes.

## Execução

O piloto foi executado em cópia descartável dentro do container Python fixado por digest. O repositório original foi montado read-only.

Duas tentativas iniciais falharam durante a coleta porque o isolamento do Mutmut não havia copiado `asef.legacy` e a fixture `examples/state`. Essas dependências passaram a constar explicitamente em `also_copy`.

## Resultado

Na primeira execução completa, 8 de 13 mutantes morreram. Cinco sobreviveram: quatro alteravam campos/mensagem de `BudgetExceeded`, e um enfraquecia o happy path de `exit_code_for`.

Após ampliar os asserts, a reexecução matou 13 de 13 mutantes. O score de 100% vale apenas para o recorte do piloto.

## Decisão

- manter Mutmut como extra separado, sem contaminar runtime;
- executar manualmente e em agenda semanal no GitHub Actions;
- não bloquear todo push com mutation neste estágio;
- expandir o escopo somente quando houver capacidade e benefício demonstrado.

## Aprendizado

O primeiro valor do mutation testing foi revelar asserts superficiais. O segundo foi revelar dependências implícitas do harness quando o código foi copiado para um ambiente isolado.
