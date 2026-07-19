# Contrato não é autoridade de rede

**Estado editorial:** revisado e aprovado pelo autor em 2026-07-19.

OpenAPI parece, à primeira vista, fornecer tudo o que uma IA precisa para testar uma API. A experiência da fatia 6.3.3 mostrou uma separação mais importante: o contrato descreve operações; ele não autoriza destinos nem efeitos.

Por isso o ASEF usa o contrato para reduzir o espaço de geração, mas ignora `servers` ao escolher o alvo. A origem continua sendo uma decisão explícita, revisada e limitada pela política. Da mesma forma, um provider live pode propor um plano, mas não ganha autoridade para executá-lo.

Essa separação tornou a implementação menos conveniente e mais honesta. Suportar um hostname externo com segurança não é trocar loopback por uma allowlist textual: resolução DNS e conexão precisam permanecer vinculadas, com HTTPS, verificação de hostname, egress limitado e proteção contra rebinding. Até que esse conjunto exista e seja testado, falhar fechado é uma funcionalidade, não uma lacuna escondida.

Esta nota foi estruturada pela IA a partir do código, dos testes e do journal da 6.3.3; Lucas aprovou a interpretação editorial em 2026-07-19.
