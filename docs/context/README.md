# Contexto operacional de Quality Engineering

## Objetivo

O ASEF precisa compreender onde, para quem e sob quais limites uma automação será desenvolvida. Esse contexto não será um único prompt. Será um conjunto versionado, validável e auditável de referências sobre o profissional de QA, equipe, sistemas, repositórios, políticas, skills, MCPs e modelos permitidos.

## Camadas de contexto

| Camada | Pergunta respondida | Exemplos |
|---|---|---|
| Perfil do QA | Quem está conduzindo e quais decisões pode tomar? | papel, experiência, responsabilidades, aprovações |
| Equipe | Quais objetivos e riscos orientam a qualidade? | domínio, taxonomia de risco, compliance, metas |
| Sistema | O que será testado e por quê? | criticidade, fluxos, SLOs, ambientes, owners |
| Repositório | Onde estão código e testes? | provider, branch, profile, read/write scopes |
| Skill | Qual capacidade de teste pode ser executada? | web, API, mobile, unit, mutation, performance |
| MCP | Qual sistema externo pode ser consultado ou alterado? | GitHub, Jira, observabilidade, device farm |
| LLM policy | Qual modelo pode receber qual dado e com qual budget? | tarefas, classificação, fallback e custo |
| Run snapshot | Qual contexto exato produziu esta execução? | IDs, versões, hashes e decisões humanas |

## Contexto não é autoridade ilimitada

- perfil do QA não contém credenciais;
- referências a repositórios não autorizam escrita automaticamente;
- uma skill não pode ativar MCP fora de sua allowlist;
- MCP de leitura não pode ser promovido a escrita por sugestão do modelo;
- LLM não decide aumentar budget, habilitar rede ou exportar artefatos;
- contexto sensível é referenciado e resolvido pelo host somente quando permitido;
- cada run persiste um snapshot sanitizado, nunca secrets.

## Fluxo de resolução

1. carregar e validar `QualityContext`;
2. selecionar sistema e repositórios autorizados;
3. intersectar capacidades solicitadas com `quality_capabilities` do sistema;
4. selecionar skills habilitadas;
5. verificar MCPs e operações permitidas por skill;
6. aplicar política de LLM, dados e budget;
7. exigir aprovação humana nas fronteiras declaradas;
8. persistir snapshot e proveniência junto das evidências.

## Artefatos

- `examples/context/quality-context.example.json` — exemplo fictício e seguro;
- `src/asef/context.py` — validação inicial;
- `docs/context/quality-context-reference.md` — referência dos campos;
- `docs/context/mcp-and-llm-governance.md` — política de integrações;
- `docs/skills/catalog.md` — catálogo inicial das capacidades.

## Privacidade

O contexto deve registrar informação profissional necessária à decisão de teste, não criar um perfil invasivo da pessoa. Dados pessoais, avaliações de desempenho, credenciais e conteúdo sem finalidade explícita ficam fora do contrato.
