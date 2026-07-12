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

- Docker Desktop/WSL2 é a única baseline testada;
- o daemon de referência reporta `DOCKER_INSECURE_NO_IPTABLES_RAW`;
- macOS, Linux nativo e ARM64 ainda não foram validados;
- integrações MCP reais ainda serão adicionadas incrementalmente.
