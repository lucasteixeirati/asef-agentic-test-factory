# ADR-002 — Perfis de linguagem compostos por capabilities

- **Status:** aceita
- **Data:** 2026-07-11
- **Responsável:** Lucas

## Contexto

Uma linguagem pode utilizar diferentes gerenciadores, builds, test runners, coverage e mutation engines. Um único `LanguageAdapter` concentraria responsabilidades e impediria combinações como Maven/JUnit e Gradle/JUnit.

## Drivers

- suporte multilíngue;
- separação de responsabilidades;
- conformance testing;
- níveis de suporte explícitos;
- manutenção por contribuidores.

## Opções consideradas

1. Um adapter por linguagem com todo o toolchain.
2. Comandos configuráveis sem contratos por capability.
3. `LanguageProfile` composto por adapters pequenos e tipados.

## Decisão

Adotar a opção 3. Perfis compõem `ProjectDetector`, `DependencyManager`, `BuildAdapter`, `StaticAnalysisAdapter`, `TestRunnerAdapter`, `CoverageAdapter`, `MutationAdapter` e `ResultNormalizer` conforme disponibilidade.

O core depende dos contratos e resultados normalizados, não de comandos concretos.

## Consequências

### Positivas

- toolchains combináveis;
- testes de contrato menores;
- capabilities ausentes explicitamente declaradas;
- menor impacto ao adicionar ferramenta.

### Negativas

- mais interfaces e composição;
- matriz de compatibilidade necessária;
- normalização pode perder detalhes se mal projetada.

## Revisitar quando

Os alphas demonstrarem excesso de interfaces sem variação real ou quando uma capability não puder ser normalizada sem comprometer sua semântica.

