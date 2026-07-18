# Plano detalhado do incremento 6.4 — TypeScript, Playwright e Web UI

**Status:** proposto após aprovação da 6.3 em 2026-07-18; implementação aguarda aprovação explícita deste plano.

## Objetivo

Entregar a primeira jornada Web UI cotidiana do ASEF: uma intenção em linguagem natural produz um plano tipado e revisável; após aprovação humana, uma automação TypeScript/Playwright executa com Chromium em ambiente controlado e produz resultado e evidências reconciliáveis.

O incremento comprovará somente uma aplicação fictícia local e autorizada. Não autoriza sites públicos, produção, login real, pagamento, comunicação externa ou ações destrutivas.

## Estado de partida

- `node-typescript` está `planned`; a imagem Node por digest comprovou apenas `node --version`;
- `web-ui` possui contrato documental planejado, sem implementação;
- o envelope genérico de capability run pode ser reutilizado sem incorporar lógica Playwright ao core;
- não existem tool image Playwright, fixture web, adapter, resultado normalizado ou dataset Web UI;
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

**Entrega:** `WebUiTestPlan`, cenários, ações, localizadores, assertions e resultado; parser estrito; política `web-ui`; fixture local pequena com estado resetável; threat model de browser e evidência visual.

**Aceite:** contratos rejeitam campos desconhecidos, hosts, comandos, scripts, secrets, seletores CSS/XPath livres, ações fora do vocabulário e budgets inválidos. A fixture funciona sem rede e não contém dados privados.

### 6.4.2 — toolchain TypeScript/Playwright reproduzível

**Entrega:** imagem dedicada por digest, Chromium/Playwright/Node pinados, lockfile, driver controlado e adapter de execução; nenhum `npm install` durante a run.

**Aceite:** build reproduzível; browser inicia como usuário não privilegiado; rootfs read-only; workspace de entrada read-only; output separado; limites de CPU, memória, PIDs e duração; rede externa desligada.

### 6.4.3 — compilador de plano e primeira execução determinística

**Entrega:** compilação do plano declarativo para TypeScript, execução contra fixture, parser de resultado e evidências de falha; abstração de página somente se repetição observada justificar.

**Aceite:** fluxo positivo e mutação reversível passam; assertion incorreta é `FAILED`; erro de browser é `ERROR`; timeout é explícito; artifact não pode escapar do workspace nem alterar a fixture fonte.

### 6.4.4 — linguagem natural, run e revisão humana

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
