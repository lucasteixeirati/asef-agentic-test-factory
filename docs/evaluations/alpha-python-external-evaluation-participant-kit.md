# Kit do participante — avaliação externa do Alpha Python

- **Versão do kit:** `1.0.0`
- **Estado:** `READY — distribuição depende de autorização e consentimento`
- **Release alvo:** `v0.1.0a7`, aprovada no postflight remoto `ASEF-PF-20260718-A7`
- **Protocolo aplicável:** `ASEF-EXT-ALPHA 1.0.1`

Este material contém somente instruções destinadas ao participante. Rubrica, respostas esperadas, severidade e parecer de prontidão não pertencem ao kit.

## Condição para liberação

O facilitador só altera o estado para `READY` depois que:

- a release alvo imutável estiver publicada;
- README, quickstart e suporte declararem a mesma versão;
- wheel e sdist possuírem hashes auditados;
- o preflight instalado passar integralmente;
- o protocolo estiver aprovado por Lucas.

## Material que será entregue

Links imutáveis congelados para a sessão:

1. [página da release alvo](https://github.com/lucasteixeirati/asef-agentic-test-factory/releases/tag/v0.1.0a7);
2. [README da mesma tag](https://github.com/lucasteixeirati/asef-agentic-test-factory/blob/v0.1.0a7/README.md);
3. [quickstart da mesma tag](https://github.com/lucasteixeirati/asef-agentic-test-factory/blob/v0.1.0a7/docs/getting-started/quickstart.md);
4. [suporte e limitações da mesma tag](https://github.com/lucasteixeirati/asef-agentic-test-factory/blob/v0.1.0a7/docs/project/support-and-limitations.md);
5. [interpretação de report](https://github.com/lucasteixeirati/asef-agentic-test-factory/blob/v0.1.0a7/docs/guides/report-interpretation.md) e [troubleshooting](https://github.com/lucasteixeirati/asef-agentic-test-factory/blob/v0.1.0a7/docs/guides/troubleshooting.md).

Nenhum checkout, comando privado, resposta esperada ou explicação individual será fornecido.

## Preparação do ambiente

O participante usará:

- Windows e PowerShell;
- Python 3.13;
- Docker Desktop iniciado;
- diretório novo e descartável;
- nenhum código, dado, credencial ou repositório real;
- `OPENAI_API_KEY` ausente.

## Cartões de tarefa

### EXT-01 — Estado e limites

Identifique o estado atual, os requisitos e as limitações do ASEF antes de instalar.

### EXT-02 — Release

Obtenha os dois assets oficiais e confira se pertencem à release indicada.

### EXT-03 — Instalação

Em diretório vazio, instale o wheel e prepare somente a imagem necessária para a demo.

### EXT-04 — Diagnóstico

Diagnostique o ambiente e decida se é seguro prosseguir.

### EXT-05 — Demo

Execute a demo pública sem provider.

### EXT-06 — Reports

Localize e valide os reports produzidos.

### EXT-07 — Interpretação

Explique o resultado, as evidências e os limites usando a documentação disponível.

### EXT-08 — Manutenção e ajuda

Planeje cleanup e encontre suporte, segurança e contribuição.

## Segurança e retirada

Não execute `--apply`, `docker system prune`, provider live ou código real. O participante pode interromper a sessão ou retirar suas observações conforme o consentimento combinado. Nenhuma gravação será feita por padrão.
