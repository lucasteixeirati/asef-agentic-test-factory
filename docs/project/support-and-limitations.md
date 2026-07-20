# Suporte e limitações do Alpha

Este documento é a fonte canônica para suporte operacional e limitações públicas. Tutoriais e políticas podem explicar o contexto, mas não devem manter matrizes concorrentes.

## Estado do produto

ASEF é uma pré-release experimental. A última versão publicada é `0.1.0a7`, com os incrementos 5.1 a 5.8 e a correção documental identificada no preflight 5.9.2. A versão atual do package também é `0.1.0a7`. O projeto não oferece garantia de uso em produção, certificação de segurança, pentest ou isolamento de código arbitrariamente hostil.

## Ambiente de referência

| Componente | Situação comprovada |
|---|---|
| Host de desenvolvimento | Windows 11 x86-64 |
| Runtime local | Python 3.13 |
| Containers | Docker Desktop com backend Linux/WSL2 |
| Package publicado | requer Python `>=3.13` |
| Provider da demo | recorded, keyless e sem rede de provider |

A CI executa testes do core e provas delimitadas em Linux x86-64, incluindo Security 12/12, symlink e cleanup recursivo controlado. Isso não equivale a validar toda a jornada instalada em Linux como ambiente anunciado. macOS, Linux como host público geral, WSL sem Docker Desktop e ARM64 não foram validados para suporte.

## Perfis de linguagem

| Perfil | Nível atual | Capabilities comprovadas | Limites |
|---|---|---|---|
| `python-pytest` | experimental | `unit` parcial; `backend-api` parcial em loopback; detecção de projeto parcial; coverage e mutation disponíveis no recorte de referência | API ainda executa no host somente contra loopback; imagem pytest precisa de build local; projetos externos não têm compatibilidade geral prometida |
| `node-typescript` | planejado, candidato a parcial | `web-ui` completa no recorte e unit aritmético de conformance com Node test/TAP | somente Chromium/fixtures locais; unit não possui CLI própria; promoção depende da revisão final; live exige autorização, budget e chave somente no host |
| `java-junit` | planejado, candidato a experimental | `unit` com contrato, detector Maven, compilador JUnit, toolchain offline, run revisável, Surefire e conformance repetida | somente fixture Calculator empacotada; promoção depende da revisão final; sem projetos externos, Gradle, Kotlin, Spring, API, coverage ou mutation Java |
| Go / .NET | planejado | nenhuma capability executável | seleção de tooling e conformance futuras |

Níveis significam:

- **reference:** caminho principal completo, documentado e coberto pela conformance definida;
- **supported:** caminho completo mantido com contrato e documentação públicos;
- **experimental:** executável no recorte declarado, sujeito a mudança e limitações conhecidas;
- **planned:** intenção ou spike, sem suporte de uso.

O código ainda declara `python-pytest` como experimental com alvo futuro `reference`; alvo não é estado atual.

### Backend API em desenvolvimento

`api-generate` converte uma intenção natural em plano revisável por cassette ou provider live opt-in e cria uma capability run; `api --run-id` reconcilia o plano por hash, aplica budgets e produz state, manifest, resultado e reports com evidências. OpenAPI 3.0/3.1 é aceito somente em JSON local de até 1 MiB: referências externas, chaves duplicadas, rotas parametrizadas e operações mutáveis não entram no recorte, e `servers` nunca define o alvo. O resumo sanitizado e o hash da fonte são preservados; a fonte bruta não é copiada para a run.

A capability bloqueia hosts externos, redirects, proxies, credenciais persistidas, headers de transporte e métodos mutáveis por padrão. Requests cotidianos ainda executam no host somente contra endereços literais de loopback; portanto não fazem DNS e não abrem uma superfície de rebinding. Docker foi comprovado apenas em conformance autocontida com rede desligada. Não há autenticação, POST, GraphQL, gRPC, acesso a serviço externo real ou aprovação de produção.

### Web UI candidata local

`web-generate` transforma uma intenção em plano declarativo por cassette ou provider
live opt-in. O plano persistido por hash precisa ser revisado antes de `web --run-id`.
A execução usa Chromium dentro do mesmo container que serve a fixture empacotada,
com `--network none`, origem literal `127.0.0.1:4173`, workspace read-only e output
separado. Requests externos, popups, dialogs e downloads são bloqueados; screenshot
surge somente em falha e permanece privado.

A conformance cobre 14 controles e executou os nove casos de browser duas vezes com
fingerprint funcional estável. Isso não autoriza sites externos, login, upload,
pagamento, múltiplos browsers, visual regression, auditoria completa de acessibilidade
ou compatibilidade geral com projetos TypeScript.

### Java/JUnit candidato local

`java-generate` transforma uma intenção pública em operações declarativas da fixture
Calculator usando cassette por padrão. O plano é persistido por hash e precisa ser
revisado antes de `java --run-id`. Um compilador determinístico — não o modelo —
define package, imports, classe e métodos JUnit. Maven 3.9.16, Java 21.0.11, JUnit
5.13.4, compiler 3.14.1 e Surefire 3.5.5 ficam na imagem dedicada; a run usa cache
offline, rede desligada, UID/GID não-root, rootfs/workspace read-only e output
separado. O XML Surefire é a evidência nativa autoritativa.

A conformance distingue sucesso, assertion failure e rejeições adversariais/de
segurança; os casos executáveis repetiram duas vezes com fingerprint estável. O
recorte não aceita Java livre, POM do usuário, dependências, repositórios, Gradle,
Kotlin, Spring, Android, API Java, coverage, mutation ou projetos externos. O modo
live permanece opt-in e não foi chamado nesta validação.

## Sandbox e segurança

O código gerado executa em container efêmero, com usuário não privilegiado, rede desabilitada, workspace read-only, output separado, imagem/argv controlados e budgets. O daemon Docker e o host permanecem parte da fronteira confiável. No ambiente de referência existe o diagnóstico `DOCKER_INSECURE_NO_IPTABLES_RAW`; os controles reduzem risco, mas não provam ausência de escape, vulnerabilidade do daemon, canal lateral ou negação de serviço no host.

Não execute artifacts gerados diretamente no host e não monte o socket Docker. `subprocess`, blacklist de imports e sanitização não são sandbox.

## Provider live

O modo live é experimental, opt-in e fora do gate obrigatório de PR. Exige contexto explícito, operações autorizadas, modelo, tarifas fornecidas pelo operador, budget positivo e `OPENAI_API_KEY` somente no host. Preço, câmbio e disponibilidade do provider são externos; custo persistido é estimativa. Cassettes live são opt-in e não devem ser publicados sem revisão humana.

O modo live não garante determinismo, qualidade sem revisão, confidencialidade de dados enviados ao provider ou compatibilidade futura do modelo/API. Use apenas contexto fictício ou autorizado e leia o [guia live](../tutorials/wf-001-live.md).

## Cleanup e retenção

`asef cleanup` é dry-run por padrão e atua somente sob `.asef`, por selectors, idade, identidade e manifest validados. No Windows caracterizado, apply recursivo de diretórios é recusado porque a primitive disponível não sustenta resistência a ataques de link. Arquivos regulares e containers gerenciados podem ser removidos após revalidação; a prova recursiva existe apenas no runner Linux controlado.

Não há secure erase, backup, recuperação ou garantia de espaço físico liberado. Não use `docker system prune` como substituto.

## Limites dos datasets

- **Smoke:** dez casos públicos e pequenos do WF-001, executados duas vezes na baseline publicada (20/20). Eles provam regressão determinística desses casos, não eficácia geral, ausência de vazamento, qualidade estatística ou desempenho em projetos reais.
- **Security:** doze controles enumerados (12/12 no ambiente registrado). O resultado prova apenas os controles, versões e precondições observados; não é certificação, pentest ou garantia contra código hostil.
- **Quality:** coverage e mutation usam fixtures e budgets delimitados. Percentuais e mutation score não são limiares universais de aceitação do produto.
- **Java Language Conformance:** quatro casos versionados (positivo, negativo,
  adversarial e segurança); os dois executáveis foram repetidos duas vezes. É prova
  somente da fixture Calculator, não uma matriz geral de projetos Java.
- Evaluation e Holdout completos continuam futuros.

## Evidência e operação

Reports públicos omitem source, prompt, ambiente bruto, stdout/stderr bruto e secrets. Hash SHA-256 detecta divergência; não prova autoria, veracidade do produtor ou armazenamento imutável. Logs são locais, rotacionados e sanitizados, sem OpenTelemetry ou coordenação multiwriter.

Para problemas operacionais, use [`../guides/troubleshooting.md`](../guides/troubleshooting.md). Para vulnerabilidades, siga [`../../SECURITY.md`](../../SECURITY.md).
