# Referência do QualityContext

## `qa_profile`

Descreve o papel operacional do profissional, não sua identidade pessoal completa.

- `id`: identificador local ou pseudônimo;
- `role`: papel no fluxo;
- `experience_level`: contexto para nível de explicação, nunca autorização implícita;
- `domains`: domínios conhecidos;
- `responsibilities`: arquitetura, automação, análise, coaching etc.;
- `preferred_evidence`: formatos úteis ao profissional;
- `approval_boundaries`: ações que exigem sua decisão.

## `team`

- objetivos de qualidade;
- taxonomia de riscos;
- compliance aplicável;
- classificação dos dados;
- convenções e critérios de aceite;
- owners e canais de escalonamento por referência.

## `systems`

Cada sistema registra `kind`, repositórios, fluxos críticos, capabilities de qualidade, ambientes, SLOs e owners. Tipos iniciais incluem `web-ui`, `webview`, `backend-api`, `mobile`, `library`, `batch`, `event-driven` e `data-pipeline`.

Um sistema pode exigir múltiplas skills. Por exemplo, um backend crítico poderá combinar unitários, API, mutation, performance e segurança sem transformar tudo em uma única skill monolítica.

## `repositories`

- referência estável, sem token na URL;
- branch padrão;
- `LanguageProfile`;
- escopo de leitura;
- escopo de escrita separado;
- diretórios proibidos;
- estratégia de checkout e hash do conteúdo na run.

Escrita fora de workspace efêmero exige aprovação e etapa de exportação.

## `skill_catalog`

Uma entrada seleciona uma skill ASEF versionada e declara capability, status e MCPs permitidos. Futuramente incluirá precondições, budgets, tipos de artefato, datasets de conformance e critérios de suporte.

## `mcp_servers`

Cada servidor registra transporte, operações permitidas, operações de escrita, classificação de dados e referência de autenticação gerenciada pelo host. Configuração não deve conter secrets literais.

## `llm_policy`

Define tarefas autorizadas, regras de dados, modo padrão, necessidade de budget live, fallback e modelos/providers permitidos por classificação. A ausência de permissão significa bloqueio.

## Snapshot por execução

O runtime deverá persistir:

- versão do schema;
- IDs e versões selecionadas;
- hashes de documentos e repositórios lidos;
- skill e MCP efetivamente usados;
- modelo/provider e política aplicados;
- decisões humanas;
- campos removidos durante sanitização.

O snapshot permite reproduzir e explicar uma execução sem copiar todo o contexto sensível.
