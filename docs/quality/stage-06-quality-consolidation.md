# Consolidação de qualidade da Etapa 6

## Aplicabilidade por perfil

| Perfil | Funcional | Coverage | Mutation | Relações metamórficas |
|---|---|---|---|---|
| `python-pytest` | unit parcial + API | available no recorte Alpha | available no recorte Alpha | aritmética limitada |
| `node-typescript` | web-ui candidata + unit aritmético de conformance | planned/indisponível | planned/indisponível | aritmética limitada |
| `java-junit` | unit candidata | planned/indisponível | planned/indisponível | aritmética limitada |

Ausência explícita é o resultado LCF-010, não zero inventado. Coverage e mutation
continuam observações irmãs: não alteram silenciosamente uma aceitação funcional.
JaCoCo/PIT, Vitest coverage e Stryker exigem caracterização, imagem, budgets,
contrato nativo e conformance próprios antes de qualquer promoção.

## Relações metamórficas

`META-ARITHMETIC-001` registra três relações matematicamente válidas dentro de
`int32` sem overflow: comutatividade da soma, inversa da subtração e elemento zero da
multiplicação. O mesmo plano declarativo é compilado deterministicamente para JUnit
e TypeScript/Node; Python permanece a referência semântica. Divisão não recebeu
relação genérica porque truncamento, sinal, zero e overflow especial tornam uma
alegação ampla enganosa.

## Estratos e finalidade

- Smoke: regressão rápida e visível do WF-001;
- Security: 12 controles adversariais do sandbox/runtime;
- API/Web/Java Language Conformance: invariantes de adapter e tooling;
- metamórfico: relações entre transformações de entradas;
- Evaluation/Holdout: comparação e generalização futuras, ainda não executadas;
- benchmark de desempenho: não aplicável sem workload, SLO e ambiente aprovados.

Essa separação impede usar Smoke como benchmark, conformance como avaliação de
qualidade geral ou Security como certificação.
