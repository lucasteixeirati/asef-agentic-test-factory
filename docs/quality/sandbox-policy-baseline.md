# Política baseline de sandbox e budgets

## Status

Baseline validada no ambiente de referência durante a Etapa 3. Não representa garantia de segurança para código arbitrariamente hostil nem autorização de uso em produção.

## Ambiente de referência

- Host: Windows.
- Containers: Docker Desktop com backend WSL2.
- Execução do SUT: container Linux efêmero.
- Rede: `none` por padrão.
- Usuário: não root.
- Docker socket: nunca montado.
- Workspace: mount dedicado; SUT original read-only; diretório de testes/resultados gravável.
- Secrets do provider: disponíveis somente ao processo host que chama o modelo.

## Política de imagens

- imagens permitidas por identificador e digest;
- tags flutuantes proibidas em runs reproduzíveis;
- imagem mínima por `LanguageProfile`;
- inventário de pacotes registrado;
- atualização exige conformance e security datasets;
- build de imagem separado da execução do SUT.

## Baseline de recursos por comando

| Budget | Valor inicial proposto | Comportamento ao exceder |
|---|---:|---|
| CPU | 2 vCPUs | Interromper comando |
| Memória | 1 GiB | Encerrar e classificar budget |
| Processos/PIDs | 128 | Bloquear/encerrar |
| Timeout de validação estática | 60 s | Encerrar etapa |
| Timeout de testes | 120 s | Encerrar execução |
| Timeout de coverage | 180 s | Encerrar capability |
| Timeout de mutation testing | 600 s | Encerrar mutação e relatar parcial |
| stdout | 1 MiB | Truncar, armazenar hash e sinalizar |
| stderr | 1 MiB | Truncar, armazenar hash e sinalizar |
| Arquivo individual gerado | 2 MiB | Bloquear artifact |
| Workspace gravável | 100 MiB | Encerrar e bloquear novas escritas |
| Número de arquivos gerados | 100 | Bloquear artifact adicional |

## Baseline por workflow

| Budget | Valor inicial proposto | Observação |
|---|---:|---|
| Duração total | 15 min sem revisão humana | Tempo pausado aguardando humano não conta |
| Correções de teste | 2 | Não autoriza alterar SUT |
| Retry de design | 1 | Apenas erro estruturado/cobertura mínima |
| Retry de provider transitório | 2 | Dentro do orçamento geral |
| Retry de infraestrutura | 1 | Recria ambiente efêmero |
| Chamadas de modelo | 8 | Inclui análise, design, geração e correção |
| Tokens de entrada acumulados | 120.000 | Medido quando provider informar |
| Tokens de saída acumulados | 40.000 | Hard stop lógico no runtime |
| Custo de API | R$ 0,00 por padrão | Modo live bloqueado até configurar budget explícito |

O custo padrão de API é zero porque o custo registrado até agora é uma licença mensal, não um orçamento autorizado para chamadas programáticas. Qualquer provider pago exigirá configuração explícita de limite antes do modo live.

## Contexto enviado ao modelo

| Item | Limite inicial |
|---|---:|
| Requisito | 20.000 caracteres |
| Conteúdo total do SUT | 100.000 caracteres |
| Feedback de stdout/stderr por correção | 20.000 caracteres combinados |
| Número de arquivos de contexto | 50 |

A poda preservará início, fim, códigos de erro, stack traces relevantes e referência ao log integral sanitizado. O agente receberá indicação explícita de truncamento.

## Comandos e dependências

- somente comandos registrados pelo `LanguageProfile`;
- sem shell arbitrário solicitado pelo modelo;
- argumentos construídos como lista, não string concatenada;
- dependências somente por lockfile e allowlist;
- instalação com rede exige fase separada, aprovação e cache controlado;
- imports podem gerar finding, mas não são tratados como sandbox.

## Filesystem

- paths normalizados e validados contra a raiz;
- symlinks e junctions avaliados antes do mount;
- SUT original read-only;
- escrita somente em diretórios de tentativa e resultados;
- arquivos sensíveis conhecidos excluídos;
- limpeza verificada ao encerrar.

## Decisões humanas obrigatórias

- aumentar budget durante uma run;
- habilitar rede;
- instalar dependência fora da allowlist;
- exportar testes para o projeto original;
- continuar após resultado inconclusivo;
- classificar possível defeito do SUT.

## Critérios de validação na Etapa 3

- medir overhead do Docker Desktop;
- testar OOM, timeout, PID limit e truncamento;
- provar ausência de secrets no container;
- provar rede desabilitada;
- testar path traversal, symlink e escrita fora do workspace;
- avaliar compatibilidade dos budgets com Python, TypeScript e Java;
- ajustar limites sem reduzir controles obrigatórios.

## Resultado da Etapa 3

- rede, identidade não root, ausência de secrets, rootfs e workspace read-only: aprovados;
- timeout com remoção forçada do container: aprovado;
- limite de memória e de PIDs: aprovados;
- traversal por `..` e symlink para fora da raiz autorizada: rejeitados antes do Docker;
- 10/10 integrações reais aprovadas no Windows + Docker Desktop/WSL2: 9 de segurança e 1 conformance de containers multilíngues;
- truncamento real de stdout/stderr aprovado e OOM classificado por exit 137;
- Python, Node e Java iniciaram sob a política comum por imagens fixadas em digest;
- overhead mediano do container Python mínimo: 341,65 ms contra 39,67 ms local (7 amostras; fotografia do ambiente);
- `DOCKER_INSECURE_NO_IPTABLES_RAW` permanece como risco do daemon e restringe a baseline a desenvolvimento experimental;
- validação em macOS, Linux nativo, ARM64 e cenários de workspace gravável permanece futura;
- conformance completa e calibração de budgets de Node/Java permanecem nas etapas multilíngues.
