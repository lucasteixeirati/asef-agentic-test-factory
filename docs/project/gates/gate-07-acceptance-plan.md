# Plano de aceitação do Gate 7

**Estado:** planejado; sem candidata ou decisão.

**Fonte operacional:** `../stage-07-developer-preview-plan.md`.

## Decisão pretendida

O Gate 7 decide se a evidência externa controlada é suficiente para encerrar o
Developer Preview e autorizar somente o planejamento do hardening da Etapa 8.

Decisões possíveis:

- `APPROVE`;
- `APPROVE_WITH_CONDITIONS`;
- `REJECT/BLOCK`.

Nenhuma contagem ou automação aprova o Gate sem decisão explícita de Lucas.

## Critérios obrigatórios

| ID | Critério | Evidência esperada | Regra |
|---|---|---|---|
| G7-01 | candidata imutável e coerente | tag, commit, artifacts, hashes, docs, CI e postflight | todos apontam para a mesma identidade |
| G7-02 | protocolo congelado antes das sessões | versão, kit, rubrica, consentimento e checklist | nenhuma resposta preenchida antecipadamente |
| G7-03 | 3–5 QEs externos elegíveis | resultados anonimizados e matriz de elegibilidade | sessões inválidas/retiradas não contam |
| G7-04 | instalação e diagnóstico observados | DP-02–DP-04 em cada sessão válida | sem checkout ou comando privado |
| G7-05 | demo keyless observada | DP-05 em cada sessão válida | sem provider ou credencial |
| G7-06 | reports compreendidos | DP-06 e rubrica sem intervenção central | terminal, classificação, integridade e limites corretos |
| G7-07 | trilha API observada | ao menos um resultado DP-T1 | somente fixture loopback autorizada |
| G7-08 | trilha Web UI observada | ao menos um resultado DP-T2 | somente fixture/Chromium locais |
| G7-09 | trilha Java observada | ao menos um resultado DP-T3 | somente fixture Calculator/Maven |
| G7-10 | extensibilidade tentada | ao menos um resultado DP-T4 | tentativa conta; sucesso não pode ser presumido |
| G7-11 | segurança e cleanup compreendidos | DP-01, DP-07 e DP-08 | sem alvo real ou ação destrutiva |
| G7-12 | intervenções rastreadas | tabela por sessão | assistência central não conta como independência |
| G7-13 | findings triados | backlog com severidade, recorrência, estado e decisão | crítico/alto aberto bloqueia |
| G7-14 | privacidade e consentimento preservados | revisão, retirada, sanitização e secret scan | PII/secret bloqueia publicação |
| G7-15 | síntese honesta | relatório agregado, contagens e limitações | sem percentual populacional ou seleção favorável |
| G7-16 | regressão final verde | testes, coverage, Docker aplicável, docs e package audit | falha material bloqueia candidata |
| G7-17 | memória e decisões atualizadas | Planejamento Mestre, journal, livro e backlog | críticas e resultados negativos preservados |

## Validade do corpus

Uma sessão conta para G7-03 quando:

- elegibilidade e consentimento são válidos;
- candidata e ambiente correspondem ao protocolo;
- DP-01–DP-08 foram tentadas;
- instalação, demo e interpretação não foram completadas pelo facilitador;
- material publicável foi revisado, anonimizado e não foi retirado.

`ENVIRONMENT_BLOCKED`, `WITHDRAWN` e `INVALID` permanecem no inventário, mas não
substituem uma das 3–5 sessões válidas. Se uma correção material mudar a candidata,
o pacote separa versões e identifica quais tarefas foram repetidas.

## Bloqueadores automáticos de recomendação

- finding crítico/alto aberto;
- menos de três sessões válidas;
- API, Web UI, Java ou extensibilidade sem observação mínima;
- interpretação central dependente de explicação individual;
- release, hash, documentação ou package divergente;
- PII, secret ou consentimento inválido;
- resultado atribuído a participante inexistente, IA ou autor;
- regressão material vermelha.

## Limites de uma aprovação

Gate 7 aprovado não declara produção, segurança geral, compatibilidade com projetos
reais ou representatividade estatística. Não promove automaticamente capabilities,
não publica v0.1 e não autoriza a implementação da Etapa 8 sem planejamento próprio.
