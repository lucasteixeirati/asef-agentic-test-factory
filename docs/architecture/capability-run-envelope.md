# Envelope genérico de capability run

## Motivação

O estado do WF-001 nasceu para teste unitário e contém pressupostos de artifact, correção e execução específicos. Reutilizá-lo diretamente em API espalharia condicionais de skill pelo core. A Etapa 6.3.2 introduz um envelope menor e neutro, inicialmente consumido por `backend-api` e candidato a reutilização por `web-ui` e outros workflows.

## Conteúdo

`CapabilityRunState` registra:

- identidade da run, workflow, skill e perfil;
- status e classificação fechados;
- budgets de modelo, tokens, requests, duração e custo;
- usage observado;
- identidade e SHA-256 do plano revisado;
- fatos, erros, histórico e evidências;
- terminalidade derivada do status.

O envelope não conhece pytest, HTTP, Playwright ou JUnit. Contratos específicos continuam em módulos da capability.

## Workflow API atual

```text
RECEIVED
  -> GENERATING_PLAN
  -> WAITING_FOR_HUMAN_REVIEW
  -> EXECUTING
  -> SUCCEEDED | FAILED | BUDGET_EXHAUSTED
```

Política pode bloquear antes da execução. `api-generate` persiste a run antes da chamada gravada ou live opt-in, registra usage e custo estimado e salva o plano por hash. `api --run-id` é a aprovação operacional explícita; a retomada reconcilia o hash antes de qualquer request. OpenAPI JSON opcional restringe as operações propostas e somente seu hash e resumo sanitizado entram na run.

## Persistência

`state.json` e `manifest.json` são substituídos como bundle com restauração dos dois arquivos se uma troca falhar. Plano, resultado e reports são registrados por caminho contido na run e SHA-256. JSON persistido rejeita chaves duplicadas.

SHA-256 detecta divergência, mas não prova autoria, veracidade ou armazenamento imutável.

## Sandbox e rede

O adapter cotidiano permanece restrito a HTTP em loopback literal no host. A prova Docker 6.3.2 executa fixture e cliente dentro do mesmo container com `--network none`, filesystem raiz read-only, capabilities removidas, usuário não privilegiado e budgets de recurso.

Um container sem rede não alcança o loopback do host. Suporte a um serviço real exigirá threat model, allowlist e isolamento de rede próprios; a implementação não deve relaxar `--network none` silenciosamente.

## Limitações

- provider live opt-in registra tokens e custo estimado, mas qualidade, disponibilidade, preço e custo final do provider permanecem externos;
- a prova Docker é somente conformance autocontida;
- OpenAPI JSON é parcial; não há autenticação, métodos mutáveis, referências externas ou alvos externos;
- o envelope ainda é experimental e não substitui o estado WF-001 existente.
