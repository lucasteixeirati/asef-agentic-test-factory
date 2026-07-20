# Revisão local — incremento 6.5 Java/JUnit

**Data local:** 19/07/2026  
**Decisão:** candidata técnica completa; promoção reservada à validação final do Gate 6.

## Evidências

- contrato/plano fechado, política anti-secrets e overflow fail-closed;
- detector Maven, fixture Calculator e manifest reconciliado por SHA-256;
- Maven 3.9.16/Temurin 21 por digest, cache offline e probe não-root;
- compilador JUnit determinístico e XML Surefire autoritativo;
- `java-generate` gravado, checkpoint por hash e `java --run-id`;
- conformance positivo/negativo/adversarial/segurança, com duas repetições estáveis;
- fixture empacotada para execução fora do checkout;
- nenhum provider live, alvo externo, push, tag ou release.

A prova instalada criou um venv temporário fora do checkout, instalou o wheel sem
dependências e executou `java-generate` seguido de `java --run-id`: 2/2 testes,
`SUCCEEDED` e `ACCEPTED`, provider `recorded`. O ambiente temporário foi removido.

- wheel SHA-256: `432451b08efc1161bfb5ed8d372e97e33ff2d3eedd5bbebe35ae1b28ebbadf5c`;
- sdist SHA-256: `f374a06a9eb6388c9e42000cd6093d4a8b57e8befdbc3398537d77ff326c1a98`.

Gate local final da fatia: 491 testes Python aprovados (40 skips condicionais),
cobertura global 85%, 3/3 integrações Java Docker aprovadas, docs 163 arquivos/128
links sem findings, secret scan e `git diff --check` limpos.

## Limites preservados

Somente `JAVA-CALCULATOR-001`, quatro operações e Maven/JUnit pinados. Projetos do
usuário, Java livre, Gradle, Kotlin, Spring, Android, API, coverage e mutation Java
continuam fora. O perfil segue `planned` até a decisão humana do Gate 6.
