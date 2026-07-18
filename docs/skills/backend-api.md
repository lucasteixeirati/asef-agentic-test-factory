# Skill `backend-api`

- **Versão:** 0.1.0
- **Estado:** partial em `python-pytest`; primeira subfatia 6.3 disponível somente para REST read-only em loopback.
- **Propósito:** derivar cenários e automações para APIs autorizadas, com rastreabilidade entre requisito, contrato, request, response e assertion.
- **Escopo inicial:** HTTP/REST e OpenAPI opcional contra alvo fictício/local.
- **Fora do escopo inicial:** GraphQL, gRPC, eventos, carga, exploração de vulnerabilidades e alvos sem autorização.
- **Contexto obrigatório:** objetivo, base URL/servidor local, hosts e métodos permitidos, política de dados, autenticação por referência e efeitos tolerados.
- **Entradas atuais:** intenção natural para cassette ou provider live opt-in, OpenAPI 3.0/3.1 JSON opcional, plano JSON revisado, origem loopback, porta autorizada e budgets.
- **Saídas atuais:** capability run, plano por hash, cenários, assertions, execução normalizada, manifest e relatórios JSON/Markdown sem corpo de resposta.
- **Técnicas:** particionamento, boundary values, schema/contract testing, idempotência quando aplicável, autenticação/autorização delimitadas e negative testing seguro.
- **Permissões:** rede desligada por padrão; allowlist explícita de host, porta, método e redirects; secrets nunca persistidos.
- **Budgets:** requests, duração, payload e retries limitados; carga não é implícita.
- **Checkpoints humanos:** habilitar rede, usar credencial, chamar método mutável, acessar dado privado e exportar código.
- **Conformance atual:** dataset dedicado de oito controles, host permitido/proibido, redirect, resposta, headers, campos sensíveis, métodos mutáveis, OpenAPI, divergência de status/JSON, adulteração, budget, persistência transacional e Docker networkless autocontido.
- **Limitações:** execução cotidiana ocorre no host somente contra loopback; Docker cobre apenas fixture interna; provider live gera o plano, mas não autoriza rede do executor; OpenAPI YAML, parâmetros de rota e referências externas não são suportados; acessibilidade pública não constitui autorização; aceite funcional não certifica segurança ou correção universal da API.
