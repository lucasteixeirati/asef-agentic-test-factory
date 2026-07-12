# Journal — 2026-07-12 — Planejamento do Walking Skeleton

## Identificação

- **Dia do projeto:** Dia 2
- **Etapa:** Etapa 4 — Walking Skeleton
- **Situação:** planejamento aprovado; incremento 4.1 implementado
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

Submeter a reavaliação após rejeição da ADR-007. Se aprovada, iniciar 4.R1 — consolidação em package único.

## Implementação 4.1

- novo package público `asef`, mantendo `asef_spike` como baseline;
- contratos de request, artifact, snapshot, evidence e execução;
- estado v2, budgets, classificações e exit codes;
- 19 testes próprios e regressão local aprovada;
- nenhuma integração de LangGraph, OpenAI ou Docker nesta rodada.

### Falhas e correções assistidas por IA

1. A primeira chamada do harness tentou importar o path do teste como módulo; foi corrigida para discovery.
2. A execução revelou dois `ResourceWarning` em um teste que lia arquivos sem fechar handles; a leitura passou a usar `Path.read_text`.
3. Uma revisão após os primeiros testes adicionou validação de budget persistido e bloqueio de marcadores sensíveis em comandos.
4. A primeira build continha o novo package, mas ainda gerava wheel `asef-spike 0.0.1`; o metadata foi corrigido para representar o produto público antes do commit.
5. A CI passou, mas revelou depreciação do runtime Node 20 nas actions v4/v5; as actions oficiais foram atualizadas para v6/Node 24 em vez de silenciar o warning.

### Decisão relevante

A proposta inicial era não migrar automaticamente estado `1.x`, por ausência de contexto e scopes. O responsável rejeitou essa solução; a reavaliação passou a propor importação `1.0 → 1.1` com contexto explicitamente não resolvido e revalidação antes de efeitos colaterais.

## Rejeição da ADR-007 e aprendizado

O responsável rejeitou a ADR-007 e pediu uma análise mais profunda antes de continuar. O inventário mostrou que a maior parte do comportamento ainda estava em `asef_spike`, enquanto `asef` continha apenas contratos. A crítica revelou que o checkpoint havia decidido uma separação antes de implementar contexto, application service e fluxo integrado.

A nova recomendação é consolidar um único package, permitir importação segura de estado `1.0` para `1.1` com contexto não resolvido e implementar o primeiro WS-001 funcional antes de uma nova ADR. Este é um exemplo de decisão humana impedindo que uma estrutura tecnicamente defensável se torne arquitetura prematura.
