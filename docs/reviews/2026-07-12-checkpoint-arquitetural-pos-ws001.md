# Checkpoint arquitetural pós-WS-001

- **Data:** 2026-07-12
- **Status:** revisão concluída; ADR-008 aceita pelo responsável
- **Gatilho:** primeiro WS-001 funcional no package único `asef`

## Resultado observado

O fluxo explícito atual conclui, sem LangGraph no runtime principal:

1. validação de request e QualityContext;
2. seleção da skill `unit`;
3. análise e geração por cassettes tipados;
4. policy e static validation;
5. workspace efêmero;
6. execução Docker;
7. avaliação determinística;
8. relatórios e estado terminal.

Evidências do checkpoint:

- `SUCCEEDED`/`ACCEPTED` no WS-001;
- 4 testes reais aprovados no container;
- 90 testes descobertos, 11 integrações Docker e 10 testes de frameworks;
- wheel com cerca de 41 KiB;
- zero dependências obrigatórias no runtime da distribuição;
- application services sem imports de OpenAI, LangGraph ou Docker.

## O que mudou desde a ADR-004

A ADR-004 foi aceita condicionalmente quando só existiam baseline e spikes. Agora há uma implementação vertical real. Ela mostra que LangGraph não é necessário para:

- fluxo linear;
- policy, budgets e outcomes;
- geração e execução;
- evidências e relatórios;
- classificação de falhas;
- composição por ports.

Ao mesmo tempo, o runtime explícito ainda não implementa a principal vantagem demonstrada pelo spike:

- interrupção humana durável;
- retomada após recriar o processo;
- prevenção de repetição de etapas concluídas;
- snapshot consultável do ponto de espera.

Portanto, a pergunta correta deixou de ser “LangGraph deve controlar o WF-001?” e passou a ser “LangGraph deve implementar a capacidade de checkpoint e retomada humana sem assumir o domínio ASEF?”.

## Opções avaliadas

### A — Substituir o runtime explícito por LangGraph

**Rejeitada como recomendação.** O WS-001 já funciona e a substituição introduziria migração ampla sem benefício para o caminho linear. Também aumentaria o risco de dois runtimes disputarem transições, budgets e outcomes.

### B — Não usar LangGraph

Manter JSON/JSONL e implementar checkpoint, resume e deduplicação em Python/SQLite próprios.

**Vantagens:** dependências mínimas e controle total.

**Riscos:** construir infraestrutura de workflow antes de demonstrar que isso é parte do diferencial do ASEF; maior superfície própria para concorrência, corrupção e idempotência.

### C — Adoção limitada por port para waits humanos

Manter os application services explícitos como implementação canônica. Introduzir uma porta de checkpoint/orquestração e um adapter LangGraph + SQLite somente para WS-002/WS-007 e futuras esperas humanas.

**Vantagens:** usa o benefício já comprovado, demonstra tecnologia moderna e preserva o domínio independente.

**Riscos:** dependências adicionais e necessidade de sincronizar checkpoint do framework com state/evidências ASEF.

**Recomendação:** opção C.

## Comparação baseada na evidência atual

| Critério | Runtime explícito atual | LangGraph limitado |
|---|---|---|
| WS-001 funcional | Comprovado | Não necessário |
| Controle de policy/outcomes | Comprovado | Deve permanecer fora do adapter |
| Dependências obrigatórias | Zero | 35 pacotes no ambiente experimental |
| Interrupção/retomada | Ainda ausente | Comprovada no spike |
| Reinício de processo | Ainda ausente | Comprovado com SQLite no spike |
| Integração com estado 1.1 | Nativa | Ainda não comprovada |
| Risco de retrabalho | Baixo se preservado | Alto se substituir o fluxo atual |
| Valor educacional | Arquitetura explícita | Comparação real e uso moderno focalizado |

## Limites obrigatórios da recomendação

- LangGraph não define status, classification, budgets ou policy;
- contratos e application services não importam LangGraph;
- estado persistido pelo framework contém somente tipos primitivos e referências;
- `run_id` é a identidade da thread/checkpoint;
- SQLite fica dentro da pasta da run;
- resume nunca repete análise/model call já concluída;
- side effects usam chaves de idempotência ASEF;
- ausência ou corrupção do checkpoint falha de forma segura e explicável;
- dependências entram como extra opcional até demonstrarem necessidade no caminho padrão;
- o adapter pode ser removido sem migrar contratos públicos.

## Critérios para considerar a adoção comprovada

1. WS-002 pausa em `WAITING_FOR_CLARIFICATION` e persiste state, eventos e checkpoint;
2. novo processo retoma a mesma run com uma resposta humana;
3. análise gravada permanece em uma única model call;
4. nenhum artifact ou container é criado antes da resposta;
5. resposta humana é append-only e sanitizada;
6. WS-007 cancela a espera com outcome e exit code corretos;
7. checkpoint ausente/corrompido é classificado sem perda silenciosa;
8. testes rodam com serialização estrita;
9. core continua verde sem instalar o extra LangGraph;
10. documentação diferencia checkpoint do framework, state ASEF e evidência pública.

## Parecer

**Decisão:** opção C aprovada com escopo estreito. LangGraph deve entrar como adapter de checkpoint e retomada humana, não como novo proprietário do workflow. Esta decisão maximiza aprendizado e valor de portfólio sem descartar a simplicidade que já provou funcionar.
