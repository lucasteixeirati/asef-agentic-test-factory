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

## Aprovação da Opção C e implementação 4.R1

O responsável aprovou a promoção completa. Todos os módulos funcionais foram movidos para o package `asef`, organizados em adapters, runtime, evidence e legacy. O source package anterior deixou de fazer parte da distribuição; o histórico Git preserva sua evolução.

### Evidências

- 50 testes locais efetivos aprovados;
- 10 testes LangGraph/PydanticAI aprovados;
- 10 integrações Docker aprovadas;
- demo legada terminou em `SUCCEEDED` pelo novo import;
- wheel contém 17 módulos `asef` e nenhum módulo do package removido.

### Falha encontrada

O primeiro teste criado para detectar imports do package removido encontrou a string dentro da própria asserção. O falso positivo foi corrigido construindo o nome dinamicamente, e todas as suítes foram repetidas.

### Próximo passo

4.R2: implementar QualityContext e fixture calculator no package consolidado, evoluir estado `1.0 → 1.1` com `CONTEXT_UNRESOLVED` e definir import/replay sem alegar retomada insegura.
## Continuação — incremento 4.R2

- **Decisão humana:** seguir com a Opção C após a consolidação 4.R1.
- **Implementação assistida por IA:** estado `1.1`, import/replay, resolver contextual e fixtures calculator/spike.
- **Revisão crítica:** a primeira versão normalizava apenas parte do usage legado; usage e budgets brutos passaram a ser preservados para não apagar evidência histórica.
- **Fronteira definida:** import é leitura auditável, replay é nova execução e resume no meio de nó não é suportado.
- **Evidência:** 67 testes descobertos, 57 aprovados, 10 Docker desabilitados e 10 testes de frameworks aprovados.
- **Falha útil:** a primeira proteção do import tratou `input_tokens` como secret; a regressão revelou o falso positivo e a regra foi refinada para chaves sensíveis específicas.
- **Fricção:** a tentativa inicial via paths falhou no harness; discovery executou corretamente.
- **Próximo passo:** 4.R3, application service determinístico antes de nova ADR.
## Continuação — incremento 4.R3

- **Objetivo:** criar o primeiro application service e a CLI pública sem consolidar frameworks prematuramente.
- **Resultado:** `asef prepare` valida request, contexto, scopes e SUT, persistindo evidências até `ANALYZING_REQUIREMENT`.
- **Decisão de transparência:** a preparação não recebe status `SUCCEEDED`; permanece não terminal e `UNCLASSIFIED` porque análise e testes ainda não aconteceram.
- **Finding:** o contexto criado em 4.R2 referenciava `examples/calculator`, mas o SUT ainda não existia. O arquivo controlado foi incluído em 4.R3.
- **Evidência:** 73 testes descobertos, 63 aprovados e 10 Docker desabilitados; 6 testes novos cobrem serviço e CLI.
- **Próximo passo:** 4.R4, gateway gravado, artifact, skill unit, policy e workspace efêmero.
## Continuação — incremento 4.R4

- **Objetivo:** atravessar a fronteira agêntica gravada sem delegar policy ou controle de fluxo ao modelo.
- **Resultado:** análise e artifact tipados, skill unit, static validation, quarentena e workspace efêmero.
- **Decisão de arquitetura:** manter o adapter gravado simples e colocar rastreabilidade, transições, usage e escrita sob o application service/runtime.
- **Falha evitada:** artifact rejeitado usaria inicialmente o próprio path não confiável ao ser preservado; passou a ser salvo com nome fixo em quarentena.
- **Evidência adversarial:** path traversal produz `POLICY_BLOCKED` sem workspace; imports, chamadas e sintaxe inválida também são rejeitados.
- **Evidência de imutabilidade:** hashes do calculator original e da cópia são verificados durante o staging.
- **Métrica:** 81 testes descobertos, 71 aprovados, 10 Docker desabilitados; 8 testes novos do incremento.
- **Prova adicional:** os 4 testes gerados pelo cassette passaram contra a cópia efêmera do calculator; isso valida o artifact, mas ainda não substitui a execução Docker do 4.R5.
- **Próximo passo:** 4.R5, Docker, execução, avaliação e relatório para fechar WS-001.
