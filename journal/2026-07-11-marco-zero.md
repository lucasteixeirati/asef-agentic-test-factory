# Journal — 2026-07-11 — Marco Zero e consolidação da visão

## Identificação

- **Dia do projeto:** Dia 1
- **Etapa/milestone:** Etapa 0 — Marco Zero
- **Período coberto:** 2026-07-11
- **Tipo de registro:** retrospectivo, consolidado a partir dos artefatos e decisões disponíveis

## Entregáveis trabalhados

| Entregável | Estado inicial | Estado final | Observação |
|---|---|---|---|
| Ideia da plataforma | Fábrica ampla para o SDLC | Fábrica de testes agêntica | Reposicionada para Quality Engineering |
| Planejamento | Quatro esboços independentes | Planejamento Mestre vigente | Revisado e modularizado |
| Arquitetura | Coleção de agentes | Runtime, workflows, skills e adaptadores | Frameworks permanecem como hipóteses |
| Linguagens | Escopo inicialmente genérico, depois restrito | Core agnóstico com implementação progressiva | Python será referência; TypeScript e Java validarão extensibilidade |
| Segurança | Lista inicial de ferramentas | Docker Desktop como ambiente inicial | Windows com backend WSL2 como referência |
| Livro | Índice antecipado | Jornada factual com índice provisório | Journals e reflexões acompanharão a construção |

## Medição em dias

- **Data de início:** 2026-07-11
- **Data de consolidação deste registro:** 2026-07-11
- **Dias corridos do Marco Zero até este registro:** 1
- **Situação:** concluído e aprovado

## Uso de IA

| Ferramenta/IA | Finalidade | Resultado | Decisão humana |
|---|---|---|---|
| GPT-5.6 Sol no ChatGPT/Codex | Planejamento, crítica, consolidação, edição documental e início do desenvolvimento | Planejamento Mestre, documentos especializados e implementação experimental | Sugestões foram revisadas e redirecionadas pelo responsável |
| Gemini Pro | Concepção e exploração inicial da ideia | Proposta inicial de uma ferramenta agêntica para automatizar todo o SDLC | O responsável redirecionou a visão para a disciplina de Quality Engineering |
| IA de revisão externa | Revisão adversarial do planejamento | Findings sobre escopo, frameworks, livro e segurança | Parte aceita, parte ajustada e parte rejeitada |
| IAs mencionadas nos esboços históricos | Brainstorms e comparações iniciais | Insumos preservados em `concepcao/` | Não constituem decisões vigentes por si só |

## Custos

- **Custo fixo inicial:** R$ 100,00 pela licença ChatGPT Plus.
- **Validade informada:** 1 mês.
- **Novo custo adicional:** R$ 0,00.
- **Valor-hora:** não será contabilizado.

## Decisões principais

- O projeto será open source, educacional, experimental e de portfólio.
- O foco será uma fábrica de testes agêntica, não todo o SDLC.
- A arquitetura será multilíngue e progressiva.
- A v0.1 será uma versão pública robusta, precedida por milestones e alphas.
- Técnicas avançadas de QE serão preservadas e introduzidas por precondições.
- SUT, testes gerados e oracle serão separados.
- Docker Desktop será o ambiente inicial de containers.
- O livro será escrito durante a jornada sem antecipar acontecimentos.
- ADRs e especificações terão autoridade documental definida.

## Aprendizados

- Uma revisão de IA é insumo para decisão, não autoridade.
- Reduzir o primeiro incremento não exige reduzir a visão final.
- Gerar implementação e testes com a mesma interpretação pode criar falsa confiança.
- Suporte multilíngue exige composição de capacidades, não uma interface monolítica.
- Documentação extensa precisa ser modularizada para continuar útil.
- Segurança precisa ser externa ao código gerado; `subprocess` não é sandbox.

## Falhas, retrabalho e fricções

- O planejamento inicial ficou amplo e orientado por uma lista de tecnologias.
- Uma revisão externa sugeriu soluções de sandbox que foram consideradas tecnicamente inadequadas.
- A primeira consolidação cresceu além de mil linhas e exigiu revisão estrutural.
- O escopo da v0.1 precisou ser redefinido para refletir a ambição real do projeto.
- Os quatro documentos históricos apresentam inconsistências editoriais que foram preservadas como evidência da concepção.

## Artefatos produzidos

- `PLANEJAMENTO_MESTRE.md`;
- `concepcao/` e sua linha do tempo;
- governança documental;
- estratégias de segurança, avaliação, evidências e open source;
- arquitetura de adaptadores multilíngues;
- estratégia do livro;
- templates operacionais;
- visão resumida;
- baseline de medição;
- este journal.

## Próximos passos

- iniciar a Etapa 1 — Visão, domínio e escopo;
- detalhar personas e necessidades;
- priorizar casos de uso;
- especificar o primeiro workflow vertical;
- definir os requisitos de independência de linguagem.

## Encerramento

O responsável aprovou explicitamente o pacote documental e o Gate 0 em 2026-07-11. Não foram registradas pendências bloqueadoras para iniciar a Etapa 1.
