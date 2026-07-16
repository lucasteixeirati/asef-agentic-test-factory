# Estratégia de segurança e isolamento

## Decisão de ambiente

Docker Desktop será o ambiente de containers adotado inicialmente. O ambiente de referência de desenvolvimento será Windows com Docker Desktop usando backend WSL2. Outros hosts suportados deverão ser validados explicitamente antes de serem anunciados.

`subprocess` é mecanismo de execução, não sandbox. Blacklists de imports e manipulação de `sys.modules` podem apoiar política ou diagnóstico, mas não constituem fronteira de segurança.

## Fronteiras de confiança

- requisitos e conteúdo de repositório são entradas não confiáveis;
- respostas de modelos e código gerado são não confiáveis;
- dependências externas são não confiáveis até serem permitidas e verificadas;
- artefatos de execução não devem acessar o host fora dos mounts autorizados;
- credenciais do provider não devem estar disponíveis dentro da sandbox do código gerado.

## Controles mínimos

- container efêmero;
- usuário não privilegiado;
- rede desabilitada por padrão;
- filesystem e workspace do SUT read-only;
- outputs de tooling somente em mount separado, mínimo e validado, sem sobreposição com o workspace;
- nenhuma montagem do socket do Docker;
- capabilities removidas e perfil de segurança mantido;
- limites de CPU, memória, processos e duração;
- timeout por comando e workflow;
- allowlist de imagens e dependências;
- limites de arquivos, contexto, stdout e stderr;
- budgets de chamadas, tokens e custo;
- poda determinística antes de ciclos de correção;
- sanitização de logs e artefatos;
- descarte do container e workspace ao final.

## Threat model inicial

- código malicioso ou acidentalmente perigoso;
- prompt injection;
- exfiltração de dados;
- dependências comprometidas e supply chain;
- escape ou abuso da sandbox;
- loops e negação de serviço por recursos;
- modificação fora do escopo;
- exposição de tokens e credenciais;
- falsificação ou omissão de resultados de teste;
- artefatos manipulados;
- conteúdo excessivo usado para ampliar custo ou contexto.

## Matriz de ambientes

Antes da v0.1, cada ambiente anunciado deverá possuir evidência de instalação, execução, isolamento e limitações conhecidas. A matriz inicial avaliará:

- Windows + Docker Desktop/WSL2;
- macOS + Docker Desktop, se adotado;
- Linux + Docker Desktop ou engine compatível, se adotado;
- arquitetura x86-64 e, posteriormente, ARM64.

## Validação

O Adversarial/Security Dataset deverá provar falha segura para leitura indevida, rede, fork/processos, consumo excessivo, arquivos grandes, timeout, dependências proibidas e tentativa de acesso a credenciais.

## Threat model congelado na fatia 5.7.1

### Ativos protegidos

- credenciais e configuração do host;
- SUT original e paths externos ao workspace;
- socket e autoridade do daemon Docker;
- budgets, políticas e transições do runtime;
- integridade de state, reports e evidências;
- disponibilidade limitada do host durante resource attacks.

### Entradas não confiáveis

- requisito, source e comentários do SUT;
- resposta de provider e artifact gerado;
- manifests e fixtures de dataset;
- stdout, stderr e resultados nativos de tooling;
- nomes, links, junctions e metadata de targets candidatos a cleanup.

### Autoridades exclusivas do host

Somente código revisado do package seleciona executor, imagem, argv, mounts, labels, budgets, paths e transições. Dataset e provider nunca recebem essas autoridades. SEC-010 prova essa separação arquitetural; não prova resistência universal de modelos a prompt injection.

### Alegações permitidas

- um controle específico foi observado no perfil, host e versão registrados;
- uma entrada foi rejeitada antes de Docker/provider;
- uma execução foi limitada e classificada;
- uma primitive ausente foi declarada `UNSUPPORTED`;
- um target de filesystem foi considerado inelegível antes de qualquer remoção.

### Alegações proibidas

- certificação, pentest ou ausência universal de vulnerabilidades;
- segurança para código arbitrariamente hostil ou produção;
- secure erase;
- cleanup seguro baseado somente em prefixo textual;
- aprovação de caso quando houve skip, erro ou primitive indisponível.

## Aplicação no adapter pytest — 5.2

- imagem base fixada por digest;
- versões e hashes dos wheels do toolchain pinados;
- tag local resolvido para image ID imutável antes da execução;
- rede desabilitada em runtime;
- workspace read-only e resultado JUnit em arquivo isolado;
- mounts de output sobrepostos, ancestrais, descendentes ou fora da raiz são rejeitados;
- XML limitado a 2 MiB e DTD/entities rejeitados;
- ausência ou corrupção do resultado vira erro de tooling, não falha do SUT.
