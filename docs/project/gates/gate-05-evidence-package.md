# Gate 5 — Pacote de evidências e decisão do Alpha Python

- **Etapa:** 5 — Alpha Python
- **Data da auditoria local:** 2026-07-18
- **Release avaliada:** `v0.1.0a7`
- **Estado técnico:** candidata local; aguarda commit, CI pública e decisão humana
- **Autoridade de aprovação:** Lucas

## Parecer técnico

**Recomendação condicionada à CI final: `APPROVE_WITH_CONDITIONS`.** Dezenove critérios estão `MET`; G5-18 está `MET_WITH_RESIDUAL_RISK`. Não há finding crítico/alto aberto. A release e o postflight são reproduzíveis, mas não houve avaliação externa independente e a jornada humana isolada foi pulada na sessão interna.

A recomendação não é aprovação automática. Antes da decisão, o commit documental/checker final precisa passar nos sete jobs públicos. Uma aprovação deve aceitar expressamente as condições abaixo e autoriza somente planejar a Etapa 6.

## Matriz consolidada

| Critérios | Estado | Evidência consolidada |
|---|---|---|
| G5-01 a G5-04 | MET | package/postflight a7, demo keyless, live controlado e pytest Docker |
| G5-05 a G5-09 | MET | report tipado, oracle independente, correção limitada, checkpoint humano e exits distintos |
| G5-10 a G5-13 | MET | Smoke 20/20, Security 12/12, coverage e mutation com budgets |
| G5-14 a G5-17 | MET | JSON/Markdown, logs/retention, doctor e fronteiras neutras do core |
| G5-18 | MET_WITH_RESIDUAL_RISK | documentação/postflight coerentes e sessão I01 informativa; QE externo ausente |
| G5-19 | MET | baseline, journals, retrospectiva, Lesson 003 e contribuição IA/humana |
| G5-20 | MET; confirmação final pendente | três matrizes públicas de sete jobs verdes; nova CI necessária para o pacote local |

O inventário mecânico contém G5-01 a G5-20, release, hashes, CIs e caminhos primários. O checker local aprovou 20 critérios e 42 evidências antes da criação deste pacote.

## Release e supply chain observada

- tag: `v0.1.0a7`;
- commit da tag: `79fbeb0dbbef39799801b86cebd59f8b55edaa0a`;
- wheel: 167.638 bytes, SHA-256 `f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad`;
- sdist: 536.458 bytes, SHA-256 `d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af`;
- postflight: instalação sem dependências fora do checkout, doctor 12 checks, demo aceita, auditor 9/9, cleanup dry-run, scanner e zero containers gerenciados.

## Regressão local da candidata

- 362 testes aprovados;
- 33 skips opt-in esperados no host local;
- branch coverage geral: 85%;
- Gate checker: 15 testes adversariais específicos aprovados;
- documentação e links: checker sem findings;
- nenhum produto/package foi alterado após a release a7.

As provas Docker, Smoke, Security e experiência instalada permanecem atribuídas às CIs públicas da release/postflight. A CI do commit final ainda é obrigatória porque checker e documentos de Gate foram alterados.

## Avaliação humana e findings

A avaliação externa está `DEFERRED`. A sessão interna `I01` foi publicada como `INFORMATIVE_INTERNAL`, com autoria e assistência de IA explícitas. EXT-03 não foi tentada; as demais tarefas tiveram recuperação ou intervenção.

| Finding | Estado final | Consequência |
|---|---|---|
| `INT-F-001` HIGH | FIXED | interpretação passou a limitar maturidade, segurança e produção |
| `INT-F-002` MEDIUM | ACCEPTED_RISK | instalação humana isolada/usabilidade independente não observadas |
| `INT-F-003` MEDIUM | FIXED | cleanup inseguro passou a exigir fail-closed |

## Condições propostas

1. coletar e versionar feedback anonimizado de usuário/QE externo quando houver adoção;
2. repetir a jornada instalada fora do checkout com pessoa não pertencente à autoria;
3. manter linguagem `experimental`, sem aprovação para produção ou código hostil;
4. tratar um experimento com SUT público como planejamento futuro autorizado, não como feature implícita;
5. não iniciar implementação da Etapa 6 sem planejamento detalhado e aprovação próprios.

## Riscos residuais

| Risco | Consequência | Proprietário/tratamento |
|---|---|---|
| ausência de avaliação externa | documentação pode refletir conhecimento dos autores | Lucas; feedback pós-Alpha como condição |
| EXT-03 não executada por I01 | fricção humana da instalação isolada não observada | Lucas; repetir com usuário externo |
| recorte sintético Python | não demonstra generalização para projeto público | planejamento futuro, sem ampliar Gate 5 |
| runtime experimental | não há garantia de produção ou isolamento hostil | manter limites e controles atuais |
| redação do livro assistida | voz editorial não é automaticamente autoral | revisão editorial separada por Lucas |

## Decisão humana

- [ ] `APPROVE` — não recomendado sem remover o risco externo;
- [ ] `APPROVE_WITH_CONDITIONS` — recomendação técnica após CI final verde;
- [ ] `REJECT/BLOCK` — devolver para correções ou exigir avaliação externa antes do Gate.

**Decisão/condições de Lucas:** pendente.

**Data:** pendente.

Uma decisão favorável encerra a Etapa 5 e autoriza somente o planejamento detalhado da Etapa 6. Não autoriza produção, feature nova, execução contra alvo público ou implementação multilíngue.
