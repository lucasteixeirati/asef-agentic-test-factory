# Arquitetura de resolução de contexto

## Componentes

- `ContextLoader`: carrega documentos autorizados;
- `ContextValidator`: valida schema, referências e ausência de secrets;
- `ContextResolver`: seleciona sistema, repositórios e capabilities;
- `SkillRegistry`: resolve implementações e níveis de suporte;
- `McpPolicy`: intersecta operações solicitadas e permitidas;
- `ModelPolicy`: aplica provider, modelo, dados e budget;
- `ContextSnapshot`: persiste proveniência sanitizada;
- runtime: executa o workflow e exige aprovações.

## Relação de autoridade

```text
Decisão humana + políticas do runtime
                  |
          QualityContext validado
          /        |         \
      sistemas   skills     MCP/LLM
          \        |         /
             workflow ASEF
                  |
       evidências + snapshot
```

## Invariantes

- uma referência ausente falha antes da chamada ao modelo;
- secret literal falha antes da persistência;
- capability solicitada precisa existir no sistema e na skill;
- operação MCP precisa estar permitida no servidor e na skill;
- acesso de escrita não é inferido de acesso de leitura;
- contexto efetivo da run é imutável; mudanças criam nova versão/snapshot;
- conteúdo do SUT nunca ganha precedência sobre política.

## Fronteira com o walking skeleton

A Etapa 4 deverá carregar um contexto mínimo, selecionar uma skill e persistir seu snapshot. Integrações MCP reais e as seis implementações completas permanecem incrementais; o skeleton prova o contrato, não finge suporte total.
