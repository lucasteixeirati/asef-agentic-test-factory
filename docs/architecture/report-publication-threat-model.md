# Threat model de publicação do Alpha report

- **Estado:** contrato congelado na 5.8.1 e publicação implementada localmente na 5.8.2
- **Contrato:** `AlphaRunReport 1.0.0`
- **Código:** `src/asef/report_contracts.py`
- **Schema:** `src/asef/schemas/alpha-run-report.schema.json`

## Objetivo

Delimitar quais fatos podem entrar no report público do Alpha, quais autoridades o report não possui e quais falhas precisam permanecer visíveis. Desde a 5.8.2, os reports terminais persistidos usam este contrato.

## Ativos protegidos

- credenciais e configuração do host;
- conteúdo integral de prompts e respostas do provider;
- source do SUT e artifact quando não autorizado para publicação;
- stdout, stderr, logs e environment brutos;
- paths absolutos, home e identidade local do operador;
- integridade de state, manifest, evidências e classificação;
- separação entre fato, inferência, recomendação e limitação;
- nível de suporte real do perfil e ambiente;
- autoridade humana sobre decisões e publicação.

## Entradas não confiáveis

- título e descrição do requisito;
- comportamentos, riscos e cenários propostos pelo provider;
- nomes e conteúdo de artifacts;
- stdout, stderr e resultados nativos de tooling;
- diagnostic messages;
- metadata importada de state/manifest legado;
- texto de decisões humanas;
- paths e hashes declarados por referências persistidas.

O fato de um valor já estar em `state.json` não o torna automaticamente publicável.

## Autoridades exclusivas

O report não pode:

- executar provider, Docker, oracle ou quality tooling;
- alterar status, classification, budget ou policy;
- executar recommendation;
- resolver uma incerteza por conta própria;
- ler arquivo arbitrário do SUT ou do host;
- transformar ausência em zero, sucesso ou `not applicable`;
- promover ambiente ou perfil a um nível de suporte superior;
- publicar evidence content apenas porque existe uma referência.

O runtime continua responsável pela classificação. O builder produz apenas uma projeção tipada dos fatos já validados.

## Ameaças e controles contratuais

| Ameaça | Impacto | Controle da 5.8.1 |
|---|---|---|
| reflexão de secret | credencial em JSON/Markdown/artifact | texto/scalar público limitado e assinaturas sensíveis rejeitadas |
| path traversal ou path local | leitura externa e exposição de identidade | paths POSIX relativos, canônicos, sem drive, `..` ou backslash |
| evidence falsificada | conclusão sem base auditável | ID, SHA-256, schema, integridade e refs internas reconciliados |
| evidence publicável sem sanitização | publicação de conteúdo proibido | `publishable` exige `sanitized` e `VERIFIED` |
| laundering de inferência como fato | falsa certeza | tipos e coleções distintas; inference exige facts e evidence existentes |
| recommendation ganhar autoridade | ação automática indevida | enum fechada, template futuro e ausência de executor no contrato |
| link de rastreabilidade inventado | narrativa causal falsa | kinds fechados e relações permitidas; risco→cenário não é aceito |
| IDs instáveis ou com lacunas | comparação enganosa | `BEH`, `RSK` e `SCN` contíguos; attempt reconciliada por ID |
| status/classification contraditórios | resultado público incorreto | matriz de reconciliação e acceptance funcional estrita |
| contagens fabricadas | pass incorreto | inteiros não negativos, soma conciliada e acceptance sem failure/error/skip |
| schema confusion | parser aceitar semântica diferente | versão exata, fields obrigatórios e `additionalProperties: false` |
| JSON excessivo | consumo de memória/disco | texto, coleções e report total limitados |
| Markdown/HTML injection | apresentação enganosa | renderer recebe somente contrato validado e escapa conteúdo não confiável |
| hash mudar entre verificação e escrita | integridade incorreta | verificação confinada e transação recuperável para JSON/Markdown/manifest |
| report divergir do manifest | audit trail inconsistente | hashes reconciliados antes de reemissão e após persistência |

## Conteúdo permitido

- IDs e versões públicas;
- status e classification tipados;
- requisito limitado e sanitizado;
- comportamentos, riscos e cenários limitados;
- metadata e hash de artifact/evidence;
- contagens, outcomes e durações normalizadas;
- usage e budgets numéricos;
- decisões humanas por código e evidence ref;
- facts, inferences, recommendations e limitations tipados;
- capability/status de quality sem raw output;
- nível de suporte proveniente da matriz versionada.

## Conteúdo proibido

- API key, token, password ou private key;
- variável de ambiente completa;
- Docker config ou raw `docker info`;
- prompt ou resposta integral;
- source do SUT;
- stdout/stderr bruto no corpo do report;
- cassette live;
- path absoluto ou nome de usuário do host;
- conteúdo de evidence não autorizado;
- claim de certificação, pentest, produção segura ou isolamento absoluto;
- relação risco→cenário não observada;
- recomendação livre controlada pelo provider.

## Falha segura

- evidence `MISSING` ou `MISMATCH` exige `EVIDENCE_INTEGRITY_FAILURE` bloqueante;
- evidence publicável que não seja sanitizada e verificada torna o contrato inválido;
- inference sem fact/evidence conhecido torna o contrato inválido;
- recommendation sem inference ou limitation conhecida torna o contrato inválido;
- link para node desconhecido ou semanticamente incompatível torna o contrato inválido;
- schema/enum desconhecido falha antes da persistência;
- um report inválido nunca deve substituir o state/manifest original nem mudar o exit code funcional.

## Claims permitidos

- o report é válido para `AlphaRunReport 1.0.0`;
- uma observação foi registrada com referência de evidência;
- uma inferência foi derivada das facts listadas;
- uma recomendação determinística se aplica à classificação/limitação indicada;
- um hash foi verificado, não verificado, está ausente ou diverge;
- o resultado se limita ao perfil, ambiente e versões registrados.

## Claims proibidos

- o report prova correção universal do SUT ou do teste;
- coverage ou mutation isoladamente provam qualidade;
- classificação de suspeita confirma defeito do produto;
- Security 12/12 constitui certificação;
- Docker garante segurança contra código arbitrariamente hostil;
- evidence sanitizada é ausência garantida de todo dado sensível;
- recommendation equivale a decisão humana ou autorização de ação.

## Implementação da 5.8.2

- builder determinístico a partir de state/snapshot/avaliação/evidence observations;
- verifier de evidence no filesystem;
- renderer Markdown e escaping adversarial;
- store atômico JSON/Markdown;
- hash dos reports no manifest;
- cobertura uniforme dos terminais persistidos;
- atualização aditiva da CLI;
- migração do `JsonRunStore.save_report()`.

## Trabalho posterior

A jornada pública, exemplos narrados, arquitetura consolidada, package audit instalado e CI `public-experience` pertencem às fatias 5.8.3 a 5.8.5. Este threat model não antecipa aprovação de candidata ou release.
