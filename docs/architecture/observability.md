# Observabilidade do ASEF

## Objetivo

Separar diagnóstico operacional de evidência auditável. Logs ajudam a operar e depurar o processo; eventos da run explicam o que aconteceu e fazem parte do resultado reproduzível.

## Dois canais

| Canal | Local | Finalidade | Autoridade |
|---|---|---|---|
| Audit trail | `.asef/runs/<run-id>/events.jsonl` | sequência da execução, decisões e transições | evidência da run |
| Log operacional | `.asef/logs/asef.jsonl` | inicialização, componentes, falhas e conclusão de comandos | diagnóstico local |

O JSON final da CLI continua sozinho no stdout. Mensagens públicas de erro continuam no stderr. O arquivo operacional não altera status, classificação ou decisão do workflow.

## Audit trail implementado

Cada novo evento contém:

- `schema_version`;
- `event_id`;
- `run_id`;
- `timestamp` UTC;
- `elapsed_since_previous_ms`;
- tipo do evento e campos específicos;
- source, target e reason em transições.

O stream é append-only em condições normais. Saves repetidos não duplicam eventos, eventos históricos sem ID recebem identidade determinística durante a reconciliação e um stream corrompido não é sobrescrito silenciosamente. `state.json` e demais documentos JSON usam substituição atômica no mesmo diretório.

## Log operacional implementado

O logger usa apenas a biblioteca padrão do Python:

- JSON Lines UTF-8;
- níveis `DEBUG`, `INFO`, `WARNING` e `ERROR`;
- rotação em 1 MiB;
- dois backups locais;
- campos de operação, componente, run, status, classificação, duração e exit code quando disponíveis;
- sanitização de assinaturas de chave OpenAI e atribuições sensíveis conhecidas;
- nenhuma emissão adicional no stdout.

O nível pode ser escolhido em cada comando com `--log-level`.

## Segurança e privacidade

Dados completos de prompts, respostas, contexto, decisões humanas e stdout/stderr não devem ser copiados para o log operacional. O audit trail usa referências e fatos delimitados. Redaction é defesa adicional, não autorização para registrar secrets.

Testes verificam que valores sensíveis conhecidos não sobrevivem à formatação. O secret scan continua sendo executado sobre artefatos de demo.

## Limitações atuais

- não há OpenTelemetry ou exportação remota;
- não há coordenação de múltiplos writers para o mesmo arquivo;
- rotação e retenção são locais;
- eventos importados das versões anteriores podem não possuir o schema novo;
- atomic replace reduz arquivos parciais, mas não implementa transação entre state, manifest e events;
- logs não são assinados e não constituem armazenamento imutável.

Essas limitações são aceitáveis para uma CLI experimental de usuário único e devem ser revistas antes de execução distribuída ou compartilhada.

A árvore de evidências, integridade e relação entre eventos, manifest e `AlphaRunReport` estão em [`evidence-model.md`](evidence-model.md). Ambientes e garantias não oferecidas estão em [`../project/support-and-limitations.md`](../project/support-and-limitations.md).
