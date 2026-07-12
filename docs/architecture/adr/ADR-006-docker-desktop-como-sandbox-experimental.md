# ADR-006 — Docker Desktop como sandbox experimental de referência

- **Status:** aceita
- **Data:** 2026-07-12
- **Responsável pela decisão:** Lucas
- **Decisão registrada em:** 2026-07-12

## Contexto

Executar código gerado exige uma fronteira externa ao processo Python. Docker Desktop com WSL2 foi escolhido como ambiente inicial e submetido a testes reais de rede, filesystem, identidade, secrets, timeout, memória, PIDs e paths.

## Decisão proposta

Adotar Docker Desktop/WSL2 como sandbox de desenvolvimento experimental da Etapa 4, com imagem por digest e os controles do `DockerPolicy`.

Não declarar o ambiente apropriado para código arbitrariamente hostil ou produção. `subprocess` e bloqueio de imports não serão apresentados como sandbox equivalente.

## Risco aceito provisoriamente

O daemon reporta `DOCKER_INSECURE_NO_IPTABLES_RAW`, configuração que reduz proteções de rede para portas publicadas. ASEF usa `--network none` e não publica portas, e o teste funcional passou. Mesmo assim, o warning permanece bloqueador para alegações mais fortes de segurança.

## Evidências

- `EXP-002`;
- 9/9 testes de segurança Docker e 1 teste multilíngue real;
- política baseline de sandbox;
- documentação oficial do Docker Engine 28.

## Revisitar quando

- houver upgrade do Docker Desktop/Engine ou remoção do warning;
- forem anunciados macOS, Linux nativo ou ARM64;
- o projeto permitir workspace gravável ou dependências com rede;
- antes de qualquer alegação de uso em produção.
