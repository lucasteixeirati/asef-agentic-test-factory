# Skill `unit`

- **Versão:** 1.0.0
- **Estado:** partial em `python-pytest`; planned em `node-typescript`; candidata a partial, ainda não promovida, em `java-junit`.
- **Propósito:** produzir testes isolados e rastreáveis para funções, classes e módulos delimitados.
- **Fora de escopo:** validar o sistema completo, declarar segurança de produção ou executar dependências arbitrárias.
- **Contexto obrigatório:** requisito, comportamento esperado, perfil de linguagem e arquivos do SUT autorizados.
- **Entradas:** análise tipada e cenários; no Alpha Python, `UnitTestArtifact`.
- **Saídas:** automação, validação de política, execução normalizada e evidências.
- **Técnicas:** classes de equivalência, valores-limite, tabelas de decisão, oracles explícitos, arrange-act-assert e independência entre testes.
- **Adapters:** pytest no perfil Python; JUnit 5/Maven candidato na fixture Calculator; Vitest/Jest permanecem planejados.
- **Permissões:** leitura do SUT delimitado e escrita apenas no workspace da tentativa; sem rede por padrão.
- **Checkpoint humano:** ambiguidades de requisito, instalação de dependência, exportação e alteração do SUT.
- **Conformance:** sintaxe válida, imports permitidos, ao menos um teste, rejeição de secrets e operações proibidas, execução reproduzível.
- **Limitações:** Java aceita somente quatro operações da fixture Calculator e não representa suporte geral a projetos; o Alpha não mede universalmente a qualidade dos testes.
