# ADR-008 — LangGraph limitado a checkpoint e retomada humana

- **Status:** aceita
- **Data:** 2026-07-12
- **Responsável pela decisão:** Lucas
- **Decisão registrada em:** 2026-07-12
- **Refina:** ADR-004
- **Não altera:** ADR-001, ADR-005 e ADR-006

## Contexto

A ADR-004 autorizou LangGraph condicionalmente com base em spikes. Após a rejeição da ADR-007, a implementação foi consolidada e o WS-001 passou de ponta a ponta sem LangGraph no runtime principal.

O fluxo explícito provou ser suficiente para intake, contexto, geração, policy, Docker, avaliação e relatórios. A lacuna real agora é WS-002/WS-007: interrupção, retomada após reinício e cancelamento sem repetir efeitos concluídos.

O EXP-001 comprovou `interrupt`, `Command(resume=...)` e `SqliteSaver`, inclusive após recriar o grafo e sem repetir a model call. Ainda não comprovou integração com o estado `1.1`, os application services e as evidências atuais.

## Decisão proposta

Adotar LangGraph e o checkpointer SQLite de forma limitada e reversível para orquestrar pontos de espera humana.

O runtime explícito e os application services ASEF permanecem canônicos para o caminho linear. LangGraph não substituirá o WS-001 nem será autoridade de domínio.

### Responsabilidades do adapter LangGraph

- materializar o grafo mínimo das esperas humanas;
- persistir checkpoint técnico em SQLite por `run_id`;
- interromper e receber comandos de resume/cancel;
- impedir reexecução de nós já confirmados pelo checkpoint;
- traduzir snapshots do framework para dados primitivos na borda.

### Responsabilidades exclusivas do ASEF

- validar comandos humanos e autorização;
- definir transições, status e outcomes;
- impor budgets, retries e idempotência;
- persistir state, eventos, artifacts e reports públicos;
- classificar falhas de checkpoint como infraestrutura;
- decidir quais application services podem ser chamados.

## Dependências e empacotamento

- `langgraph==1.2.9` e `langgraph-checkpoint-sqlite==3.1.0` permanecem pinados durante a Etapa 4;
- entram inicialmente em extra opcional, não nas dependências obrigatórias do core;
- CI mantém job isolado com serialização estrita;
- o modo demo linear continua funcionando sem o extra;
- comandos de resume apresentam erro orientativo quando o extra não está instalado.

## Persistência

- checkpoint técnico: `.asef/runs/<run_id>/checkpoint.sqlite`;
- state público: `.asef/runs/<run_id>/state.json`;
- sequência pública: `events.jsonl`;
- decisões humanas: append-only com identificador e timestamp;
- nenhuma resposta humana ou payload do framework é tratada como autorizada antes da validação ASEF.

SQLite não substitui state/evidências. Divergência entre checkpoint e state bloqueia a retomada e gera finding de infraestrutura.

## Consequências positivas

- WS-002 pode retomar após reinício sem repetir model call;
- o projeto demonstra integração moderna sobre fronteiras explícitas;
- evita implementar prematuramente um engine próprio de checkpoint;
- mantém o core testável e utilizável sem framework;
- fornece comparação educacional real para o livro.

## Consequências negativas

- adiciona dependências e política de versões;
- cria duas representações técnicas que precisam de verificação de consistência;
- upgrades exigem testes de serialização e retomada;
- debugging passa a incluir state ASEF, eventos e snapshot LangGraph;
- SQLite local não resolve concorrência distribuída ou alta disponibilidade.

## Alternativas rejeitadas

### Substituir todo o workflow por LangGraph

Rejeitada por migrar um WS-001 funcional sem benefício demonstrado no caminho linear.

### Implementar engine próprio agora

Adiada. Poderá ser reconsiderada se o adapter não respeitar as fronteiras, aumentar excessivamente o metapacote ou falhar nos critérios de retomada.

### Não implementar retomada durável

Rejeitada por impedir WS-002, WS-007 e parte central da proposta agêntica controlada.

## Critérios de aceite

- cumprir os dez critérios do checkpoint pós-WS-001;
- provar WS-002 e WS-007;
- manter core sem dependência/import de LangGraph;
- não repetir model call, artifact ou Docker na retomada;
- documentar rollback e remover o adapter se os critérios falharem.

## Rollback

Remover o extra e o adapter, manter state/eventos ASEF e retornar erro explícito de resume não disponível. Contratos públicos, runs lineares e reports não exigirão migração.

## Decisão humana

Aceita explicitamente por Lucas. A implementação está autorizada dentro dos limites e critérios desta ADR; a aprovação não autoriza LangGraph a substituir o runtime explícito ou assumir responsabilidades de domínio.

## Evidência inicial de implementação

- extra opcional `workflow-langgraph` criado;
- core executado sem o extra e sem imports do framework;
- checkpoint SQLite local por run;
- retomada após recriar adapter/processo;
- decisão repetida tratada de forma idempotente;
- checkpoint ausente ou corrompido falha com erro explícito;
- WS-002 mantém a mesma run e não repete a análise;
- WS-007 cancela sem artifact, workspace ou Docker;
- serialização estrita aprovada nos testes opcionais.
