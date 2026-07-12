# Journal — 2026-07-12 — Planejamento do Walking Skeleton

## Identificação

- **Dia do projeto:** Dia 2
- **Etapa:** Etapa 4 — Walking Skeleton
- **Situação:** planejamento concluído; implementação não iniciada
- **Tipo de registro:** contemporâneo

## Contexto

Após a aprovação do Gate 3 e publicação do repositório, o responsável autorizou iniciar o planejamento detalhado da Etapa 4 antes de alterar a implementação.

## Decisões de planejamento

- usar um SUT Python fictício e controlado;
- implementar apenas a skill `unit` no nível skeleton;
- gerar e executar um teste real, sem manter a execução simulada como prova do Gate 4;
- usar duas respostas gravadas: análise e artifact;
- exigir modo demo sem API key;
- tornar modo live opcional e não bloqueador;
- persistir QualityContext sanitizado e explicar seleção de skill;
- usar `unittest` no skeleton para evitar instalação com rede;
- manter pytest, coverage, mutation, MCPs e multilíngue end-to-end para etapas posteriores;
- definir sete cenários obrigatórios e quinze critérios de Gate 4.

## Estimativa inicial

- faixa planejada: 4–8 dias de projeto;
- unidade oficial: dias corridos por entregável;
- estimativa não extrapola a velocidade dos spikes;
- checkpoints humanos após contratos e após o primeiro fluxo de sucesso.

## Uso de IA

| Ferramenta/modelo | Finalidade | Resultado | Decisão humana |
|---|---|---|---|
| GPT-5.6 Sol/Codex | Revisar contratos e estruturar o plano executável | plano, arquitetura e critérios de aceite | escopo será submetido ao responsável antes do código |

## Reflexões para o livro

- planejar o skeleton após os spikes evita transformar experimentos diretamente em arquitetura de produto;
- “caminho completo” precisa gerar e executar algo real, não apenas percorrer estados;
- registrar o que não será feito protege o projeto contra expansão silenciosa;
- contexto do QA só prova valor quando altera de modo explicável a seleção de uma capability.

## Próximo passo

Submeter o plano ao responsável. Após aprovação, iniciar o incremento 4.1 — contratos e estado, sem integrar frameworks antes do primeiro checkpoint humano.
