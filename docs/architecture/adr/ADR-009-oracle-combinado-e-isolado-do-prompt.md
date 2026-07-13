# ADR-009 — Interpretação combinada com oracle isolado do prompt

- **Status:** aceita por Lucas em 2026-07-13
- **Data:** 2026-07-13
- **Relacionada:** ADR-003
- **Escopo:** Alpha Python, com contrato neutro para outros perfis

## Contexto

O walking skeleton trata exit code de teste como falha funcional. Isso não é suficiente no Alpha: um teste gerado pode estar errado, o SUT pode conter defeito ou a infraestrutura pode impedir uma conclusão. Usar a própria LLM como juiz repetiria parte da interpretação que produziu o teste.

A ADR-003 já exige SUT existente e oracle independente. Falta decidir como combinar as duas evidências e em que momento o oracle pode ser disponibilizado.

## Drivers

- evitar falso diagnóstico de defeito no SUT;
- impedir vazamento do oracle ao gerador;
- preservar explicabilidade e revisão humana;
- corrigir somente artifacts de teste;
- manter o contrato aplicável a outras linguagens.

## Opções consideradas

1. Classificar somente pelo resultado do teste gerado.
2. Usar uma LLM julgadora como autoridade final.
3. Executar teste gerado e oracle curado separadamente, combinando os fatos por regras determinísticas.

## Decisão proposta

Adotar a opção 3.

- `oracle_ref` nunca pertence a `generation_input_refs`;
- oracle é materializado somente na fase de avaliação;
- o repositório pode publicar o oracle, mas o componente avaliado não o recebe;
- teste gerado e oracle produzem evidências e hashes distintos;
- a interpretação considera os dois resultados e a causa técnica observável;
- LLM-as-a-judge pode acrescentar análise, mas não substitui o oracle determinístico;
- nenhuma divergência autoriza alteração automática do SUT.

## Matriz proposta

| Teste gerado | Oracle | Resultado |
|---|---|---|
| erro de sintaxe, import ou coleta | não necessário | `TEST_ERROR`; correção dentro do budget |
| falha | passa no comportamento relacionado | `TEST_ERROR`; teste provavelmente incoerente |
| passa | falha | `SUT_DEFECT_SUSPECTED`; revisão humana |
| falha | confirma divergência do SUT | `SUT_DEFECT_SUSPECTED`; revisão humana |
| passa | passa | candidato a `ACCEPTED` |
| inconclusivo ou infraestrutura falha | inconclusivo | classificar somente a causa comprovável |

“Provavelmente” e “suspected” são deliberados: a evidência sustenta investigação, não uma afirmação absoluta sobre causa raiz.

## Consequências positivas

- reduz circularidade entre geração e avaliação;
- permite distinguir correção de teste de investigação do SUT;
- cria um caso didático forte sobre oracles em sistemas com IA;
- mantém decisões críticas fora do provider.

## Consequências negativas

- aumenta custo de curadoria e execução;
- exige mapear comportamentos entre teste gerado e oracle;
- um oracle também pode estar errado e precisa de versionamento/revisão;
- repositório público não oferece sigilo, apenas isolamento de contexto.

## Controles

- schema rejeita oracle entre inputs de geração;
- casos e fixtures têm versão, origem, licença, curador e hashes;
- mudanças intencionais exigem revisão do manifest e da versão do caso;
- SUT defeituoso é fixture controlada e read-only durante a run;
- estado inconclusivo prevalece quando não houver evidência suficiente.

## Evidência inicial

- `DatasetCase` implementa separação entre geração e avaliação;
- SMK-001, SMK-002, SMK-003 e SMK-007 possuem requisitos e oracles próprios;
- SUT correto e variante defeituosa possuem manifest de hashes;
- testes de contrato rejeitam leakage e path traversal.

## Critérios para aceite

- Lucas aprova a matriz e o significado de `SUT_DEFECT_SUSPECTED`;
- teste automatizado prova que oracle não entra no payload de geração;
- 5.3 demonstra os quatro cruzamentos relevantes;
- revisão humana permanece obrigatória para suspeita de defeito.

## Decisão humana

Lucas aprovou explicitamente a ADR-009 em 2026-07-13. A matriz, o significado não conclusivo de `SUT_DEFECT_SUSPECTED`, o isolamento do oracle e a obrigatoriedade de revisão humana passam a ser decisões vigentes. A aceitação não autoriza correção automática do SUT.
