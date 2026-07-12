# EXP-002 — Baseline de isolamento no Docker Desktop

- **Data:** 2026-07-12
- **Status:** controles da Etapa 3 aprovados para desenvolvimento experimental
- **Ambiente:** Docker Desktop 4.42.1, Engine 28.2.2, WSL2/Linux x86-64
- **Imagem:** `python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0`

## Pergunta

Os controles iniciais do `DockerRunner` bloqueiam rede, escrita no workspace/rootfs e exposição da API key no ambiente de referência?

## Controles aplicados

- `--network none`;
- `--read-only`;
- `--cap-drop ALL`;
- `no-new-privileges`;
- usuário `65534:65534`;
- limite de 128 PIDs, 1 GiB e 2 CPUs;
- `--memory-swap` igual ao limite de memória;
- tmpfs limitado para `/tmp`;
- workspace montado read-only;
- raiz de workspaces autorizada e validada após resolução de symlinks;
- nome único por container e remoção forçada após timeout;
- nenhuma variável de secret encaminhada;
- imagem fixada por digest.

## Resultados

| Verificação | Resultado |
|---|---|
| UID não root | 65534 — aprovado |
| `OPENAI_API_KEY` visível | `false` — aprovado |
| Workspace gravável | `false` — aprovado |
| Conexão externa | bloqueada — aprovado |
| Escrita no rootfs | bloqueada — aprovado |
| Timeout | classificado como exit 124; container removido — aprovado |
| Memória | alocação acima de 64 MiB interrompida — aprovado |
| PIDs | fan-out bloqueado com limite 16 — aprovado |
| Path `..` fora da raiz | rejeitado antes do Docker — aprovado |
| Symlink para fora da raiz | rejeitado antes do Docker — aprovado |
| Truncamento real de stdout/stderr | ambos limitados — aprovado |
| Testes de segurança reais | 9/9 aprovados |

## Finding de harness no Windows

Diretórios criados por `TemporaryDirectory` no perfil temporário do Windows foram negados pelo Docker Desktop com exit code 125. O mount da raiz do projeto e de `.asef` funcionou. O harness passou a usar workspace estável e ignorado pelo Git dentro de `.asef/`.

Isso é uma limitação de ACL/compartilhamento do ambiente de testes, não evidência de falha dos controles do container.

## Risco observado

`docker info` continua reportando `DOCKER_INSECURE_NO_IPTABLES_RAW`. Segundo as notas oficiais do Docker Engine 28, essa configuração impede regras na tabela `raw` e reduz a proteção de portas publicadas, não sendo recomendada para produção. O runner ASEF não publica portas e usa `--network none`; o teste funcional de rede passou. O risco permanece aberto e impede alegações de isolamento de produção neste ambiente.

## Limitações

- container não equivale a isolamento perfeito;
- testes cobrem o ambiente atual, não macOS ou Linux nativo;
- mount de workspace gravável será testado separadamente.
- o warning `DOCKER_INSECURE_NO_IPTABLES_RAW` permanece no daemon;
- limites de arquivos e tamanho total do workspace ainda pertencem a etapas posteriores.
