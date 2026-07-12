# Preparação para a Etapa 4

- **Data:** 2026-07-12
- **Status:** em conclusão
- **Objetivo:** tornar o repositório público, contextual e reproduzível antes do walking skeleton.

## Decisões do responsável

- autorizar primeira publicação pública no GitHub;
- criar README e pacote comunitário;
- manter o metapacote PydanticAI no ambiente experimental para cenários futuros;
- antecipar baselines de Python, Node/TypeScript e Java;
- modelar o contexto do QA, equipe, sistemas, repositórios, skills, MCPs e LLMs;
- aplicar melhorias de CI, segurança, contribuição e evidências.

## Entregáveis

| Entregável | Situação | Evidência |
|---|---|---|
| README público | Concluído | `README.md` |
| Licença MIT | Concluído | `LICENSE` |
| Guia de contribuição | Concluído | `CONTRIBUTING.md` |
| Política de segurança | Concluído | `SECURITY.md` |
| CI inicial | Concluído localmente; execução remota pendente | `.github/workflows/ci.yml` |
| Templates públicos | Concluído | `.github/ISSUE_TEMPLATE/` e PR template |
| QualityContext | Concluído no recorte inicial | código, 5 testes, exemplo e referência |
| Catálogo de skills | Concluído como planejamento | `docs/skills/catalog.md` |
| Governança MCP/LLM | Concluída como baseline | `docs/context/mcp-and-llm-governance.md` |
| Python/Node/Java por digest | Concluído | EXP-006 e integração Docker |
| OOM e truncamento real | Concluído | integração Docker |
| Overhead Docker | Medido | EXP-006 |
| Git local | Inicializado; commit pendente | branch `main` |
| GitHub público | Pendente | autenticação e criação remota |

## Limites preservados

- catálogo não equivale a skills implementadas;
- containers multilíngues não equivalem a profiles suportados;
- PydanticAI instalado não significa integração habilitada;
- MCPs do exemplo não executam operações reais;
- contexto real de equipes não será publicado;
- nenhuma capability recebe escrita por inferência.

## Critérios de saída

- regressão local, Docker e frameworks aprovada;
- arquivos públicos e YAML validados;
- varredura de secrets sem finding;
- Git inicializado com snapshot coerente;
- repositório público criado sem `.env`, `.venv` ou `.asef`;
- Gate 3 revisado com as novas evidências.
