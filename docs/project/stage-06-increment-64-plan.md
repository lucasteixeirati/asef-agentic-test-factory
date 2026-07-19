# Plano detalhado do incremento 6.4 — TypeScript, Playwright e Web UI

**Status:** 6.4.2 aprovada por Lucas em 2026-07-19; 6.4.3 concluída e 6.4.4 implementada localmente como candidata. Nenhuma chamada live foi realizada.

## Objetivo

Entregar a primeira jornada Web UI cotidiana do ASEF: uma intenção em linguagem natural produz um plano tipado e revisável; após aprovação humana, uma automação TypeScript/Playwright executa com Chromium em ambiente controlado e produz resultado e evidências reconciliáveis.

O incremento comprovará somente uma aplicação fictícia local e autorizada. Não autoriza sites públicos, produção, login real, pagamento, comunicação externa ou ações destrutivas.

## Estado de partida

- `node-typescript` está `planned`; a imagem Node por digest comprovou apenas `node --version`;
- `web-ui` partiu de contrato apenas documental; a 6.4.1 agora possui contrato executável, parser, política e fixture, sem browser ou adapter;
- o envelope genérico de capability run pode ser reutilizado sem incorporar lógica Playwright ao core;
- o ponto de partida não possuía tool image, adapter ou resultado Web UI; 6.4.1 e 6.4.2 já materializaram contratos, fixture e toolchain, sem execução de plano ou dataset;
- a política Docker comum já oferece usuário não privilegiado, rootfs/workspace read-only, limites e rede desligada.

## Decisões de escopo

### Incluído

- Chromium único;
- TypeScript e Playwright Test;
- fixture web autocontida no repositório;
- fluxos de leitura e uma mutação local reversível/resetável;
- seletores por `role`, `label` e `data-testid` quando a semântica não bastar;
- assertions de URL, visibilidade, texto, estado e acessibilidade semântica básica;
- screenshot apenas em falha, não publicável por padrão;
- execução e servidor da fixture no mesmo container com rede externa desligada;
- geração por cassette primeiro e provider live somente após o caminho determinístico estar estável.

### Excluído

- Firefox, WebKit, dispositivos reais e mobile emulado como alegação de suporte;
- sites externos ou publicamente acessíveis;
- autenticação real, CAPTCHA, MFA, pagamento, e-mail/SMS e credenciais;
- upload, download, clipboard, geolocalização, câmera, microfone e pop-ups;
- visual regression, performance, accessibility audit completo e pentest;
- instalação dinâmica de dependências durante a run;
- YAML ou scripts livres fornecidos diretamente pelo modelo.

## Contratos e fronteiras

O modelo poderá propor somente um `WebUiTestPlan` declarativo com ações de vocabulário fechado. Ele não fornecerá JavaScript arbitrário, comandos, host, credenciais ou configuração do browser. O runtime injeta a origem autorizada e compila o plano para um artifact TypeScript controlado.

Vocabulário inicial:

- ações: `goto`, `click`, `fill`, `check`, `uncheck`;
- localizadores: `role`, `label`, `test_id`;
- assertions: `url`, `visible`, `text`, `value`, `checked`;
- dados: strings públicas e delimitadas, sem nomes/campos sensíveis;
- navegação: somente caminhos relativos da origem local autorizada.

O resultado normalizado deverá distinguir `PASSED`, `FAILED`, `ERROR`, `TIMEOUT` e `POLICY_BLOCKED`, preservando contagens, duração, cenário, etapa, diagnóstico e referências de evidência. Resultado funcional não será confundido com infraestrutura ou política.

## Política de segurança

- somente endereço literal de loopback e porta explicitamente autorizada;
- container com `--network none`; fixture e browser no mesmo namespace de rede;
- origem, browser, imagem, argv e diretórios definidos pelo runtime;
- redirects/navegações para outra origem bloqueados e detectados;
- service workers, downloads, dialogs e novas páginas negados;
- requests inesperados fora da origem abortados;
- secrets rejeitados antes da geração e nunca persistidos no plano/artifact;
- screenshot, stdout, stderr e relatório limitados e registrados por hash;
- screenshot começa `sanitized=false`, `publishable=false`; publicação exige revisão separada;
- trace e vídeo ficam desabilitados na primeira fatia para reduzir exposição e volume;
- plano por hash e checkpoint humano antes da execução.

## Fatias de implementação

### 6.4.1 — contratos, threat model e fixture

**Progresso:** candidata local concluída. Contratos de plano e resultado, parsers
estritos, política fail-closed por host/porta, loader JSON com chaves duplicadas
negadas, fixture resetável, testes adversariais e threat model foram materializados.
Isso não executa browser nem promove o perfil Node.

**Entrega:** `WebUiTestPlan`, cenários, ações, localizadores, assertions e resultado; parser estrito; política `web-ui`; fixture local pequena com estado resetável; threat model de browser e evidência visual.

**Aceite:** contratos rejeitam campos desconhecidos, hosts, comandos, scripts, secrets, seletores CSS/XPath livres, ações fora do vocabulário e budgets inválidos. A fixture funciona sem rede e não contém dados privados.

### 6.4.2 — toolchain TypeScript/Playwright reproduzível

**Progresso:** candidata local concluída. A imagem usa Playwright 1.61.0 Noble por
digest, Node 24.16.0, Chromium 149.0.7827.55 e package npm 1.61.0 por lockfile. Um
driver de comandos fechados e um adapter que resolve a tag para image ID comprovam
Chromium headless como UID/GID 65534, rede desligada, rootfs/workspace read-only,
output separado e budgets de CPU, memória, PIDs e tempo. Nenhum plano é compilado.

**Entrega:** imagem dedicada por digest, Chromium/Playwright/Node pinados, lockfile, driver controlado e adapter de execução; nenhum `npm install` durante a run.

**Aceite:** build reproduzível; browser inicia como usuário não privilegiado; rootfs read-only; workspace de entrada read-only; output separado; limites de CPU, memória, PIDs e duração; rede externa desligada.

### 6.4.3 — compilador de plano e primeira execução determinística

**Progresso:** candidata local concluída em 2026-07-19. O compilador produz um
módulo TypeScript determinístico e data-only, reconciliado byte a byte com o plano
revisado antes do Docker. O driver serve a fixture em `127.0.0.1:4173` e executa o
vocabulário fechado no Chromium dentro do mesmo container sem rede. Jornada
positiva, falha funcional com PNG privado, anti-tamper, identidade de resultado e
falhas de infraestrutura foram cobertas. Linguagem natural, capability run e
provider live Web UI continuam pertencendo à 6.4.4.

**Entrega:** compilação do plano declarativo para TypeScript, execução contra fixture, parser de resultado e evidências de falha; abstração de página somente se repetição observada justificar.

**Aceite:** fluxo positivo e mutação reversível passam; assertion incorreta é `FAILED`; erro de browser é `ERROR`; timeout é explícito; artifact não pode escapar do workspace nem alterar a fixture fonte.

### 6.4.4 — linguagem natural, run e revisão humana

**Progresso:** candidata local concluída. O caminho determinístico por cassette
passou ponta a ponta.
`web-generate` cria a run antes do gateway, injeta origem e IDs, contabiliza tokens,
persiste o plano por hash e termina em `WAITING_FOR_HUMAN_REVIEW`. `web --run-id`
reconcilia o hash, compila e executa somente após a revisão operacional, preservando
resultado, manifest e identidade do artifact. O modo live é opt-in, exige modelo,
budget e tarifas positivas e contabiliza custo/retry; sua integração foi coberta
com gateway falso, sem usar chave ou fazer chamada. Uma chamada live real continua
dependente do checkpoint próprio.

**Entrega:** `web-generate` por cassette, saída estruturada, budgets, persistência no envelope genérico e `web --run-id` após revisão; provider live opt-in integrado somente após o cassette passar.

**Aceite:** a run existe antes do modelo; tokens, retries, duração e custo live estimado são contabilizados; plano e artifact são reconciliados por hash; nenhuma execução ocorre antes do checkpoint; saída rejeitada não esconde uso observado.

### 6.4.5 — dataset de conformance e hardening

**Entrega:** dataset versionado com casos positivos, negativos e adversariais; repetição para observar flakiness; prova Docker real.

**Matriz mínima:** leitura, mutação resetável, seletor semântico, assertion divergente, timeout, navegação externa, request externo, popup/dialog, download, secret, adulteração, screenshot não publicável e budget.

**Aceite:** casos esperados reconciliam; duas repetições determinísticas mantêm fingerprint funcional; nenhum caso acessa rede externa; findings altos/críticos bloqueiam promoção.

### 6.4.6 — documentação, experiência instalada e revisão

**Entrega:** tutorial diário, mapa do projeto, matriz de linguagem, suporte/limitações, arquitetura, journal, livro/source map/proveniência, wheel/sdist e pacote de revisão da 6.4.

**Aceite:** pessoa revisora consegue instalar, gerar, revisar e executar a fixture usando apenas material público; documentação não chama Node de suportado antes da conformance; regressão total, cobertura mínima de 85%, docs checker, secret scan e experiência instalada passam.

## Critério de promoção

Ao final da 6.4, somente `web-ui` poderá passar de `planned` para `partial` dentro de `node-typescript`, se todas as provas forem concluídas. O perfil continua experimental ou planned conforme a matriz geral; inicializar Chromium ou passar uma fixture não cria suporte geral a projetos TypeScript.

## Checkpoints humanos

1. aprovação deste plano;
2. aprovação dos contratos e da política após 6.4.1;
3. aprovação da imagem/toolchain pinada após 6.4.2;
4. aprovação para qualquer chamada live com budget explícito;
5. revisão final antes de promoção documental, push, tag ou release.

## Ordem recomendada

Executar estritamente 6.4.1 → 6.4.6. A primeira autorização deve abranger somente 6.4.1, preservando checkpoints pequenos e auditáveis.
