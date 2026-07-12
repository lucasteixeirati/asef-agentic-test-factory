# ADR-005 — Gateway direto e PydanticAI disponível sob política

- **Status:** proposta para aprovação no Gate 3
- **Data:** 2026-07-12
- **Responsável pela decisão:** Lucas

## Contexto

PydanticAI reduziu o código do adaptador e fortaleceu structured output, mas não teve chamada live equivalente. O metapacote completo aumentou significativamente o ambiente e `pydantic_graph` emitiu warning no Python 3.13. O responsável optou por preservar o pacote completo para cenários futuros com providers, evals, MCPs e observabilidade, sem torná-lo autoridade do workflow.

## Decisão proposta

- manter o gateway OpenAI Responses direto na Etapa 4;
- manter validação e recuperação sob controle do runtime;
- manter `pydantic-ai==2.9.0` no ambiente experimental;
- não ativar suas integrações automaticamente no walking skeleton;
- exigir seleção por `QualityContext`, skill e política para cada integração;
- impedir que um adapter de provider controle o workflow.

## Consequências

- menor superfície de dependências no primeiro skeleton;
- parsing e integração HTTP permanecem responsabilidade local;
- a portabilidade multi-provider não será antecipada;
- o ambiente experimental é maior, mas permite comparações e integrações futuras sem nova decisão de instalação;
- cada uso efetivo ainda exige evidência, teste e limites próprios.

## Evidências

- `EXP-003`, `EXP-004` e `EXP-005`;
- 5/5 testes PydanticAI offline;
- gateway direto executado live uma vez;
- matriz de decisão do Gate 3.
