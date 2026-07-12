# Arquitetura de adaptadores multilíngues

## Objetivo

Permitir que workflows e o runtime operem sobre diferentes ecossistemas sem incorporar comandos ou formatos específicos de uma linguagem no core.

## Princípio de composição

Não haverá um `LanguageAdapter` monolítico responsável por todo o toolchain. Um perfil de linguagem será composto por capacidades menores:

```text
LanguageProfile
├── ProjectDetector
├── DependencyManager
├── BuildAdapter
├── StaticAnalysisAdapter
├── TestRunnerAdapter
├── CoverageAdapter
├── MutationAdapter
└── ResultNormalizer
```

Exemplo conceitual:

```text
JavaMavenProfile
├── MavenDependencyManager
├── MavenBuildAdapter
├── JUnit5TestRunner
├── JaCoCoCoverageAdapter
└── PitMutationAdapter
```

## Responsabilidade do core

O core deve conhecer contratos e resultados normalizados, não comandos como `pytest`, `npm test` ou `mvn test`.

## Conformidade entre linguagens

O Language Conformance Dataset validará invariantes contratuais:

- descoberta de projeto;
- execução do build quando aplicável;
- execução e cancelamento de testes;
- aplicação de timeout e budgets;
- coleta e normalização de resultados;
- geração de evidências;
- classificação de falhas;
- cumprimento das políticas de sandbox.

Conformidade não significa gerar código idêntico ou ignorar práticas idiomáticas de cada linguagem.

## Ordem inicial proposta

1. Python como implementação de referência.
2. TypeScript como validação no ecossistema Node.js.
3. Java como validação de tooling corporativo e build mais complexo.
4. Go ou .NET como candidato posterior.

## Níveis de suporte

- **Referência:** todas as capacidades obrigatórias e documentação completa.
- **Suportado:** workflow end-to-end e conformance suite aprovada.
- **Experimental:** subconjunto de capacidades documentado e sujeito a mudanças.
- **Planejado:** ainda sem compromisso de implementação.

Os níveis e capacidades obrigatórias da v0.1 serão definidos na Etapa 1.

