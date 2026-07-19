# Etapa 6.4.6 — documentação e experiência instalada Web UI

Data: 2026-07-19

A fatia começou pela perspectiva da distribuição e encontrou dependência acidental
do checkout: `DockerWebUiExecutor` copiava a fixture de `examples/web-ui`, ausente no
wheel. Os assets cotidiano e adversarial foram empacotados, ligados ao executor e
protegidos por igualdade byte a byte com os exemplos públicos.

O wheel e o sdist foram reconstruídos. Uma virtualenv temporária fora do checkout
instalou o wheel sem dependências. `web-generate` por cassette criou plano em
`WAITING_FOR_HUMAN_REVIEW`; após leitura do plano e manifest, `web --run-id` executou
a fixture empacotada em Chromium/Docker sem rede e terminou `SUCCEEDED/ACCEPTED`,
1/1 teste. Nenhum provider foi chamado e a virtualenv foi removida.

Tutorial, mapa do produto, matriz, suporte, arquitetura, contrato da skill e planos
foram atualizados como candidata. A promoção para `partial` continua reservada à
revisão humana final da Etapa 6, junto do pacote completo do Gate 6.
