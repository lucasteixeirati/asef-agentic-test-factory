# Política de rede da capability backend API

## Decisão atual

O executor público aceita somente `http`, endereço IP literal de loopback e porta explicitamente autorizada. Redirects e proxies não são seguidos. Como nomes DNS e hosts externos são rejeitados antes do request, o recorte atual não cria uma superfície de DNS rebinding ou SSRF para serviços privados.

OpenAPI descreve operações, não autoridade: `servers` nunca substitui a `base_url` revisada e a fonte não habilita hosts, credenciais ou métodos.

## Condição para expansão

Alvos externos continuam indisponíveis até existir um adapter isolado que implemente, em conjunto: HTTPS obrigatório; allowlist exata de hostname e porta; resolução controlada; rejeição de IPs privados, loopback, link-local, reservados e multicast; conexão pinada ao endereço validado mantendo SNI e verificação do hostname; redirects desabilitados; egress do container limitado; proteção contra proxies; budgets; consentimento e evidência da autorização.

Permitir apenas um hostname e depois deixar a biblioteca resolver novamente não é suficiente, porque abriria uma janela de rebinding. Enquanto esse conjunto não for comprovado, a política correta é falhar fechado.
