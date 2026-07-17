# Política de segurança

## Estado

ASEF é experimental e não oferece garantia de isolamento para código arbitrariamente hostil ou uso em produção.

## Relatar vulnerabilidade

Não publique secrets, exploits funcionais ou detalhes sensíveis em uma issue pública. Use o recurso privado de reporte de vulnerabilidades do GitHub quando estiver habilitado no repositório. Se ele ainda não estiver disponível, abra uma issue pública sem detalhes técnicos solicitando um canal privado.

Inclua, quando seguro:

- versão/commit;
- componente afetado;
- impacto esperado;
- precondições;
- reprodução sanitizada;
- mitigação conhecida.

## Escopo prioritário

- escape de sandbox ou acesso ao host;
- exposição de credenciais;
- bypass de path, budget ou aprovação;
- operações MCP não autorizadas;
- prompt injection que altere políticas;
- falsificação ou perda de evidências;
- dependências comprometidas.

## Limitações conhecidas

A matriz vigente de hosts, perfis, sandbox, provider live, cleanup e datasets está em [`docs/project/support-and-limitations.md`](docs/project/support-and-limitations.md). Em particular, resultados Smoke/Security não são certificação, e hash/sanitização não tornam evidência imutável ou provam ausência de vulnerabilidade.

Não execute artifacts gerados no host, não monte o socket Docker e não relaxe rede, mounts ou budgets como workaround.
