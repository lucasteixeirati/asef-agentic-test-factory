# Skill `unit`

- **Versão:** 1.0.0
- **Estado:** partial nos perfis experimentais `python-pytest`, `node-typescript` e `java-junit`, cada qual somente no recorte comprovado.
- **Propósito:** produzir testes isolados e rastreáveis para funções, classes e módulos delimitados.
- **Fora de escopo:** validar o sistema completo, declarar segurança de produção ou executar dependências arbitrárias.
- **Contexto obrigatório:** requisito, comportamento esperado, perfil de linguagem e arquivos do SUT autorizados.
- **Entradas:** análise tipada e cenários; no Alpha Python, `UnitTestArtifact`.
- **Saídas:** automação, validação de política, execução normalizada e evidências.
- **Técnicas:** classes de equivalência, valores-limite, tabelas de decisão, oracles explícitos, arrange-act-assert e independência entre testes.
- **Adapters:** pytest no perfil Python; Node test/TAP no recorte aritmético de conformance; JUnit 5/Maven na fixture Calculator. Vitest/Jest permanecem planejados.
- **Permissões:** leitura do SUT delimitado e escrita apenas no workspace da tentativa; sem rede por padrão.
- **Checkpoint humano:** ambiguidades de requisito, instalação de dependência, exportação e alteração do SUT.
- **Conformance:** sintaxe válida, imports permitidos, ao menos um teste, rejeição de secrets e operações proibidas, execução reproduzível.
- **Limitações:** Node não possui CLI unitária própria; Java aceita somente quatro operações da fixture Calculator; nenhum dos recortes representa suporte geral a projetos. O Alpha não mede universalmente a qualidade dos testes.
