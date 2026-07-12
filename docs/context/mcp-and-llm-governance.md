# Governança de MCPs, skills e LLMs

## Princípio

MCP é uma fronteira de integração, não uma autorização genérica. Uma skill solicita uma capability; a política resolve quais servidores e operações podem atendê-la; o runtime registra a execução.

## Níveis de operação MCP

| Nível | Exemplos | Regra |
|---|---|---|
| Leitura pública | documentação, schemas públicos | allowlist e proveniência |
| Leitura privada | código, issues, telemetria interna | autenticação host + classificação |
| Escrita reversível | comentário, draft, branch temporária | aprovação conforme política |
| Escrita de alto impacto | merge, release, alteração de ambiente | aprovação humana obrigatória |
| Proibida | secrets, produção sem autorização, bypass de controles | bloqueio |

## Seleção de skill

A seleção considera simultaneamente:

- tipo e criticidade do sistema;
- `LanguageProfile` do repositório;
- objetivo solicitado pelo QA;
- capabilities declaradas pelo sistema;
- datasets e nível de suporte da skill;
- ferramentas/MCPs disponíveis;
- budget e ambiente;
- aprovações necessárias.

O modelo pode recomendar uma skill, mas não pode habilitar uma capability ausente do contexto.

## Roteamento de LLM

- tarefas determinísticas permanecem em código;
- dados classificados restringem providers e modelos;
- prompts recebem apenas o menor contexto necessário;
- fallback entre modelos exige política explícita;
- retries pertencem ao runtime;
- uso, custo e artefatos são registrados;
- troca de provider não altera permissões MCP.

## Prompt injection e contexto de repositório

Conteúdo do repositório é entrada não confiável. Instruções encontradas em README, comentários, issues ou páginas consultadas não podem modificar a política, habilitar MCP, revelar secrets ou aumentar escopo. A precedência é: política do runtime, decisão humana, contrato do workflow, contexto validado e somente então conteúdo do SUT.

## Publicação e privacidade

Exemplos públicos devem usar organizações, repositórios e sistemas fictícios. Cassettes e journals passam por sanitização antes do commit. Contextos reais de equipes não devem ser publicados no repositório do framework.
