# Modelo de evidências e reprodutibilidade

## Objetivo

Permitir explicar, auditar e comparar cada execução sem prometer determinismo de provider ou imutabilidade do filesystem. O estado funcional, a trilha de eventos, as evidências brutas delimitadas e o relatório público têm papéis diferentes.

## Árvore real de uma run

Itens aparecem conforme o caminho executado; uma falha anterior ao artifact não inventa arquivos posteriores.

```text
.asef/runs/<run-id>/
├── context-snapshot.json
├── state.json
├── events.jsonl
├── manifest.json
├── artifacts/
│   ├── attempt-001/
│   │   ├── <teste-gerado>
│   │   └── metadata.json               # fluxo combinado
│   └── rejected/attempt-001.txt       # somente quando rejeitado
├── results/                            # fluxo linear
│   ├── static-validation.json
│   ├── execution.json
│   ├── <resultado-nativo>
│   ├── stdout.txt
│   └── stderr.txt
├── attempts/
│   └── 001/
│       ├── generated/
│       │   ├── execution.json
│       │   ├── <resultado-nativo>      # quando produzido
│       │   ├── stdout.txt
│       │   └── stderr.txt
│       ├── oracle/                     # fluxo combinado
│       └── evaluation.json
├── oracle/                            # oracle curado, quando usado
│   ├── test_oracle.py
│   └── identity.json
├── quality/                            # capabilities solicitadas
├── report.json
└── report.md
```

Workspaces efêmeros podem existir durante a execução, mas não são superfície pública nem evidência final por si só. Smoke, Security, doctor e cleanup têm stores próprios sob `.asef`; seus reports não devem ser confundidos com `AlphaRunReport`.

## Papéis dos documentos

- `context-snapshot.json`: contexto efetivo primitivo e scopes resolvidos;
- `state.json`: estado, classificação, budgets, usage e referências funcionais;
- `events.jsonl`: sequência append-only em condições normais, com transições e decisões;
- `manifest.json`: identidade da run, hashes do SUT, status, usage, refs e hashes dos reports;
- `artifacts/`, `attempts/`, `oracle/` e `quality/`: evidências delimitadas por tentativa/capability;
- `report.json`: projeção normativa validada como `AlphaRunReport 1.0.0`;
- `report.md`: view determinística do JSON validado, sem fatos adicionais.

Logs operacionais ficam em `.asef/logs/asef.jsonl` e servem a diagnóstico, não a decisão funcional. Veja [`observability.md`](observability.md).

## Eventos e manifest

Cada evento novo possui schema, `event_id`, `run_id`, timestamp UTC, tempo desde o anterior, tipo e campos específicos; transições registram source, target e reason. Saves idempotentes não duplicam eventos e corrupção não é sobrescrita silenciosamente. Parent/correlation IDs completos, assinatura e coordenação multiwriter continuam ausentes.

O manifest registra os dados efetivamente disponíveis: identidade e versão, status/classificação, hashes do SUT, contexto/policies, usage, evidências e reports. Campos aspiracionais — por exemplo seed de um provider que não a expõe — não são fabricados.

Após a publicação, `reports.json` e `reports.markdown` contêm `relative_path` e SHA-256. O report não referencia o próprio hash; o manifest é atualizado depois da escrita para evitar circularidade.

## Integridade de evidências

Antes de compor o report, `ReportEvidenceVerifier`:

1. aceita somente path relativo canônico e contido na run;
2. rejeita traversal, path absoluto, symlink e junction;
3. limita a superfície a tipos publicáveis allowlisted;
4. recalcula SHA-256 e compara com a referência persistida;
5. retorna `VERIFIED`, `MISSING` ou `MISMATCH`.

Somente evidência `VERIFIED` e sanitizada pode sustentar um fato publicável. Ausência/divergência gera limitação e `EVIDENCE_INTEGRITY_FAILURE`; não altera retrospectivamente o terminal funcional da run. Hash detecta diferença de bytes, mas não prova autoria, correção semântica, ausência de comprometimento anterior ou armazenamento imutável.

`AlphaReportStore` valida contrato, JSON reaberto e paridade do Markdown; reconcilia hashes existentes para detectar tamper e persiste JSON, Markdown e manifest por transação recuperável. A operação reduz estados parciais, mas não cria transação ACID entre todos os arquivos históricos da run.

## Fatos, inferências e decisões

Fatos apontam para evidências/trace IDs existentes. Inferências declaram suas bases e nunca são serializadas como observação. Recomendações usam códigos allowlisted. Decisões humanas são sanitizadas, identificadas e append-only; não reescrevem o que a ferramenta observou.

## Privacidade e publicação

O report público não inclui source, prompt, resposta bruta do provider, environment bruto, headers, secrets ou stdout/stderr bruto. Ele publica metadados fechados, contagens, códigos, paths relativos e hashes. Evidência bruta continua local e não deve ser anexada automaticamente.

O threat model normativo da superfície pública está em [`report-publication-threat-model.md`](report-publication-threat-model.md). Suporte e limites estão em [`../project/support-and-limitations.md`](../project/support-and-limitations.md).
