# Diagnóstico do ambiente

`asef doctor` é uma superfície estritamente diagnóstica. Ele observa requisitos conhecidos do perfil `python-pytest`, produz facts allowlisted e recomendações enumeradas e não modifica a configuração do host.

## Checks

O report contém exatamente a matriz inicial: Python, distribuição ASEF, host, output root, Docker CLI, daemon, engine Linux, imagens pytest/quality, contexto, presença de requisito live e containers gerenciados.

Comandos Docker são argv fixos compilados no package. `docker info` usa template que retorna somente server version, OSType e architecture; mesmo esses campos passam por formatos fechados. Stdout/stderr bruto é descartado.

O check live publica apenas `present: true|false`. Contexto explícito inválido é bloqueante, mas nenhum detalhe do parser ou path é refletido. Containers residuais são contados somente pelo label `com.asef.managed=true`.

## Semântica

- `HEALTHY`: todos os checks executados passaram;
- `DEGRADED`: existe warning ou skip opcional, com exit `0`;
- `BLOCKED`: ao menos um requisito obrigatório falhou, com exit `7`;
- input/output inválido: exit `2`.

`DOCTOR_CHECK_FAILED` identifica falha interna do check e não é usado como sinônimo de requisito ausente.

## Não autoridade

O doctor não instala package ou Docker, não inicia daemon, não constrói/puxa imagem, não remove container, não executa prune, não lê `~/.docker/config.json`, não chama provider e não imprime secret. As recomendações são IDs estáticos revisados.
