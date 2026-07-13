# Modelo de evidências e reprodutibilidade

## Objetivo

Permitir explicar, auditar e comparar cada execução dentro dos limites de reprodutibilidade dos modelos utilizados.

## Artefatos mínimos

```text
runs/<run-id>/
├── input.json
├── manifest.json
├── events.jsonl
├── artifacts/
├── test-results/
├── metrics.json
└── report.md
```

## Evento mínimo

- `run_id`, `event_id`, `parent_event_id` e correlation IDs;
- timestamp e duração;
- versão do schema do evento;
- workflow, etapa, tentativa e operação;
- provider e modelo quando aplicável;
- status e classificação de erro;
- consumo e custo estimado;
- referências a inputs e artefatos por hash;
- decisão automática ou humana;
- política ou aprovação relacionada;
- indicador de sanitização.

## Baseline implementada no walking skeleton

A implementação atual cobre identidade do evento e da run, timestamp UTC, tempo desde o evento anterior, transições, motivos, decisões humanas sem duplicação e sequência append-only. O schema completo acima continua como alvo evolutivo: parent/correlation IDs, duração de operações agênticas, custo estimado por evento e indicador explícito de sanitização ainda não estão todos presentes.

Logs operacionais não são confundidos com evidência. A separação, o formato e as limitações estão em [`observability.md`](observability.md).

## Manifest mínimo

- versão e hash do workflow;
- provider, identificador exato do modelo e parâmetros;
- hashes dos prompts e templates;
- versão e hash dos datasets;
- adaptadores e versões;
- imagem e digest da sandbox;
- dependências e lockfiles;
- sistema operacional, arquitetura e configuração relevante;
- seeds, quando suportadas;
- budgets e políticas aplicados;
- referências imutáveis aos artefatos de entrada e saída.

## Privacidade

Prompts, logs e artefatos não serão publicados automaticamente. Conteúdo sensível deve ser removido ou substituído por referências sanitizadas antes de qualquer publicação.
