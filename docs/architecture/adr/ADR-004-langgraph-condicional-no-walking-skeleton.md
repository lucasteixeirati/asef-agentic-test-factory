# ADR-004 — LangGraph condicional no walking skeleton

- **Status:** aceita
- **Data:** 2026-07-12
- **Responsável pela decisão:** Lucas
- **Decisão registrada em:** 2026-07-12
- **Reavaliação:** ADR-008 proposta após WS-001 funcional; ADR-004 permanece vigente até decisão humana

## Contexto

A baseline Python foi comparada ao LangGraph no WF-001. LangGraph demonstrou checkpoint, snapshot, interrupção humana e retomada após recriação do grafo sem repetir a chamada ao modelo. A baseline continua mais simples e sem dependências externas.

## Decisão proposta

Adotar LangGraph 1.2.9 condicionalmente na Etapa 4 para composição do grafo, checkpoint SQLite e interrupção/retomada.

As seguintes responsabilidades não serão delegadas ao framework:

- definição semântica dos estados e transições;
- budgets e critérios de parada;
- políticas de segurança;
- contratos de evidência;
- classificação final da execução;
- autorização de retries.

A máquina Python explícita permanece como baseline comparativa e referência de conformance.

## Consequências

- persistência e human-in-the-loop entram no skeleton com evidência prévia;
- o produto assume dependências adicionais;
- estados persistidos devem permanecer compostos por tipos primitivos;
- upgrades do framework exigirão testes de retomada e serialização;
- LangGraph será removido se o walking skeleton mostrar que o benefício não compensa o acoplamento.

## Evidências

- `EXP-001`;
- 5/5 testes LangGraph em serialização estrita;
- matriz de decisão do Gate 3;
- ADR-001 sobre autoridade do runtime.
