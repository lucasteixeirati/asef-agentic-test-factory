# Threat model da primeira jornada Web UI

## Escopo e alegação limitada

Este documento governa a fatia 6.4.1 do ASEF. O único alvo admitido é a fixture
fictícia, local e resetável em `examples/web-ui`. A existência dos contratos não
promove `web-ui` nem `node-typescript`: a 6.4.2 comprova somente a toolchain e o
probe Chromium; compilação do plano, execução funcional e conformance pertencem às
fatias seguintes.

Sites públicos, produção, autenticação real, pagamento, comunicação externa,
uploads, downloads e dados privados continuam fora do escopo. Uma URL acessível
não constitui autorização.

## Ativos protegidos

- host, daemon Docker e outros serviços locais;
- credenciais, tokens, cookies e dados pessoais do operador;
- source da fixture e workspaces de entrada;
- plano revisado e sua identidade por hash;
- stdout, stderr, screenshots e relatórios;
- integridade da classificação funcional e da trilha de evidências.

## Fronteiras de confiança

Requisito, resposta do modelo, plano JSON, conteúdo DOM e mensagens do browser são
entradas não confiáveis. O runtime, a política versionada, a imagem pinada futura,
o compilador de vocabulário fechado e o store de evidências ficam na fronteira
confiável. O modelo não define origem, porta, browser, imagem, argv, mounts,
política, paths de output ou publicação de evidências.

```text
intenção não confiável
  -> WebUiTestPlan declarativo
  -> parser estrito + WebUiPolicy
  -> revisão humana + hash
  -> compilador controlado (6.4.3)
  -> fixture + Chromium no container sem rede (6.4.2/6.4.3)
  -> resultado normalizado + evidência privada
```

## Ameaças e controles obrigatórios

| Ameaça | Controle da primeira jornada |
|---|---|
| navegação para outra origem | somente paths relativos sem `//`, backslash, fragmento ou whitespace; origem injetada pelo runtime |
| acesso a serviço local não autorizado | host literal loopback e porta não vazia explicitamente allowlisted |
| JavaScript ou comando arbitrário proposto pelo modelo | ações, locators e assertions usam vocabulários fechados; CSS, XPath, scripts e argv não entram no contrato |
| segredo persistido no plano | nomes e marcadores sensíveis são bloqueados; login real e credenciais estão fora do escopo |
| popup, dialog, download ou nova página | negados pelo futuro driver; ocorrência deve ser `POLICY_BLOCKED` ou `ERROR`, nunca sucesso silencioso |
| request inesperado | futuro routing do browser aborta qualquer request fora da origem da fixture |
| alteração da fixture fonte | input read-only e output separado; mutações existem apenas no estado em memória e possuem reset |
| evidência visual expor conteúdo | screenshot somente em falha, limitada, `sanitized=false` e `publishable=false` por padrão |
| path traversal em screenshot | apenas path POSIX relativo, contido e terminado em `.png` |
| adulteração entre revisão e execução | plano persistido e reconciliado por SHA-256 no envelope de capability run |
| spoofing de resultado | parser estrito, contadores reconciliados e precedência determinística de status |
| indisponibilidade ou flakiness | timeout por cenário, budget global e repetição no dataset da 6.4.5 |

## Evidência visual

Trace e vídeo ficam desativados na primeira jornada. Screenshot é evidência privada
de diagnóstico e não pode ser anexada automaticamente a documentação, issue,
release ou report público. Publicação futura exige revisão humana separada e um
processo verificável de sanitização; hash não prova que pixels estão livres de
segredos.

## Critérios que bloqueiam 6.4.2 e promoção

- política aceita host ou porta não explicitamente autorizados;
- contrato permite script, comando, selector livre ou navegação entre origens;
- fixture contém egress, persistência, credencial ou dependência externa;
- resultado não distingue falha funcional, timeout, erro e bloqueio de política;
- screenshot é tratado como publicável por padrão;
- finding alto ou crítico não está remediado ou aceito explicitamente.

## Riscos residuais

A 6.4.2 inicializa Chromium sob a política Docker e comprova o bloqueio de egress do
container, mas ainda não executa cenários nem comprova handlers reais de requests,
popups, dialogs, service workers ou downloads. Docker e Chromium não provam
isolamento absoluto contra browser ou código hostil. A conformance desses controles
é condição das fatias 6.4.3 a 6.4.5.
