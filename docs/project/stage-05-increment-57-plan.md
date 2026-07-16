# Incremento 5.7 — Segurança, diagnóstico e retenção

- **Data:** 2026-07-15
- **Estado:** implementação local das seis fatias concluída; candidata `0.1.0a5` aguarda checkpoint e CI pública
- **Dependências:** incrementos 5.1 a 5.6 concluídos; pré-alpha `v0.1.0a4` publicada; o sexto job de CI ainda não existe
- **Gate relacionado:** G5-11, G5-15 e G5-16, com evidência complementar para G5-02, G5-04, G5-09, G5-17, G5-18 e G5-20
- **Decisão para implementar:** Lucas autorizou explicitamente as seis fatias; publicação continua condicionada à revisão e CI

## 1. Objetivo

Transformar os controles de segurança já exercitados isoladamente em uma superfície Alpha reproduzível e diagnosticável. O incremento entregará os casos públicos `SEC-001` a `SEC-012`, um comando `asef doctor`, uma política de retenção/debug aplicável e cleanup seguro de recursos gerenciados pelo ASEF.

O resultado não será apresentado como certificação, pentest, proteção contra código arbitrariamente hostil ou garantia de isolamento absoluto. O Security Dataset prova apenas os controles explícitos do perfil Python de referência, no ambiente suportado e nas versões pinadas.

## 2. Escopo

### Incluído

- contratos neutros e versionados para casos, resultados e suite de segurança;
- materialização exata de `SEC-001` a `SEC-012` com fixtures públicas fictícias;
- runner offline/keyless, sem comandos arbitrários definidos pelo dataset;
- comando público `asef security` com JSON/Markdown e exit codes estáveis;
- hardening do `DockerRunner` para labels, interrupção, cleanup verificável e socket ausente;
- comando público `asef doctor` com checks tipados e recomendações sanitizadas;
- distinção entre CLI ausente, daemon indisponível, imagem ausente, contexto inválido, requisito live ausente e erro interno do check;
- política versionada para efêmeros, evidências finais, logs, cassettes, debug e artifacts de CI;
- comando `asef cleanup` conservador, dry-run por padrão e mutação apenas com `--apply`;
- tombstone/report de manutenção para cada cleanup aplicado;
- regressão de sanitização e secret scan em source, package, logs e evidências;
- job de CI `alpha-security`, preservando os cinco jobs existentes;
- atualização de README, arquitetura, Gate 5, progresso, journal e notas editoriais.

### Não incluído

- declarar Docker uma sandbox suficiente para workloads hostis ou produção;
- scanner de vulnerabilidades, SAST/DAST genérico, antivírus ou detecção de malware;
- SBOM, assinatura de artifacts, provenance criptográfica ou publicação de imagens em registry;
- gestão de secrets, rotação de credenciais ou integração com vault;
- telemetria remota, SIEM, OpenTelemetry ou execução multiusuário;
- secure erase ou garantia forense de eliminação física;
- cleanup automático de evidência final sem ação explícita do operador;
- `docker system prune`, remoção por nome parcial ou limpeza de recursos não rotulados pelo ASEF;
- debug bundle contendo prompt, resposta integral, ambiente, SUT ou workspace bruto;
- red team live de modelos, avaliação estatística de prompt injection ou benchmark de segurança;
- consolidação completa de troubleshooting/documentação pública, pertencente ao 5.8;
- decisão final do Gate 5, release estável ou início da Etapa 6.

## 3. Findings da baseline

1. O catálogo já descreve `SEC-001` a `SEC-012`, mas não há manifests, loader, runner agregado ou reports executáveis.
2. Nove integrações Docker já provam usuário não root/secret ausente, rede, rootfs, timeout, memória, PIDs, traversal, symlink quando o host permite e truncamento.
3. `UnitSkill` já bloqueia imports fora da allowlist, calls proibidas, markers sensíveis e artifacts inválidos/grandes; esses controles cobrem parte de SEC-009 e SEC-012.
4. O adapter live delimita source e não entrega autoridade de workflow ou ferramentas ao provider, mas SEC-010 precisa provar que uma instrução em comentário não altera policy, budget, path ou transição.
5. `DockerRunner` usa `--rm` e força remoção em timeout, porém interrupções/exceções fora do timeout não possuem prova explícita de cleanup nem labels de ownership.
6. Vários application services usam `shutil.rmtree(..., ignore_errors=True)`. Isso evita mascarar o resultado principal, mas também pode ocultar workspace residual.
7. Não existe `asef doctor`. Hoje erros de CLI ausente, daemon parado, imagem não construída e contexto inválido aparecem em momentos diferentes do workflow.
8. Logs operacionais rotacionam em 1 MiB com dois backups e sanitização defensiva, mas não há política única que relacione logs, runs, suites, cassettes e CI.
9. Artifacts Smoke e quality já usam `retention-days: 7`; evidência local é mantida indefinidamente e efêmeros são removidos ad hoc.
10. O secret scanner cobre assinaturas de alta confiança e archives sem imprimir o valor encontrado, mas não é DLP completo e alguns erros de leitura/tamanho são silenciosamente ignorados.
11. Python 3.13 expõe `Path.is_junction()`; `shutil.rmtree()` não percorre o conteúdo de junctions Windows desde 3.8, mas a proteção contra ataques de symlink depende da plataforma. Cleanup precisa validar cada alvo, não apenas confiar em uma chamada recursiva.
12. A CI possui cinco jobs verdes. Segurança continua diluída em `docker-security`; G5-11, G5-15 e G5-16 permanecem abertos ou parciais.

## 4. Princípios e fronteiras

### 4.1 O dataset valida controles, não ausência universal de risco

Cada caso terá um controle, precondições, executor interno, outcome esperado e evidências mínimas. Um caso passa quando o ASEF bloqueia/classifica o vetor como especificado. O runner não conclui que o container é invulnerável nem extrapola o resultado para outras imagens, hosts ou linguagens.

Resultados negativos esperados são sucesso da suite. Falha de infraestrutura, caso não executado ou primitive indisponível não pode virar `PASSED`. O report separará `passed`, `failed`, `errors` e `unsupported`; aceite 12/12 exige doze `PASSED` e zero nos demais.

### 4.2 Nenhum payload controla comandos do host

Manifests não conterão shell, argv livre, imagem, mount ou path absoluto. `case_id` selecionará um executor compilado no package por enum/registry fechado. Fixtures entram apenas como dados limitados e hasheados. Unknown executor, field ou arquivo falha antes de Docker/provider.

### 4.3 Diagnóstico não corrige nem instala

`asef doctor` será read-only em relação ao projeto e ao Docker: não fará pull, build, login, prune, provider call, mudança de contexto Docker ou edição de arquivo. Um probe gravável poderá criar um arquivo aleatório somente dentro de `.asef/doctor-probe`, validá-lo e removê-lo no mesmo check; falha de remoção será explícita.

### 4.4 Retenção conservadora

Workspaces, outputs operacionais temporários e containers são efêmeros obrigatórios. Reports, state e evidências finais permanecem até ação explícita. `asef cleanup` é dry-run por padrão; `--apply` e selectors delimitados são necessários para deletar. Não há cleanup por idade implícito ao iniciar uma run.

### 4.5 Debug não amplia coleta

`DEBUG` aumenta detalhe operacional permitido, não autoriza prompt/resposta integral, conteúdo do SUT, variáveis de ambiente, credenciais ou workspace bruto. Redaction é defesa adicional; se um dado não é autorizado, ele não deve ser coletado antes da redaction.

## 5. Security Dataset executável

### 5.1 Contratos

Criar contratos versionados:

- `SecurityCaseSpec`: ID, versão, controle, executor, fixture refs, precondições, expected outcome e limitações;
- `SecurityCaseResult`: status, classificação, duração, evidence refs, facts observados e diagnóstico estável;
- `SecuritySuiteReport`: hash efetivo, totais, ambiente, duração, resultados e conclusão;
- enums fechados para executor e status;
- loader estrito com limites de bytes, duplicate-key rejection, paths POSIX contidos e exatamente doze IDs.

O hash efetivo incluirá manifests, fixtures e arquivos concretos usados. Resultados terão fingerprint semântico sem duração/timestamp para detectar regressão entre execuções.

### 5.2 Estrutura proposta

```text
datasets/security/
  manifest.json
  SEC-001/
    case.json
    README.md
    fixtures/
  ...
  SEC-012/
```

O dataset será público, fictício e sem secrets reais. Sentinels sensíveis serão montados em runtime ou fragmentados no source para não se confundirem com credenciais publicáveis.

### 5.3 Matriz de execução

| ID | Executor | Prova mínima | Resultado esperado |
|---|---|---|---|
| SEC-001 | Docker | sentinel presente no host não aparece no env/container/report | secret ausente e evidência sanitizada |
| SEC-002 | Docker | network mode none + conexão bloqueada | nenhuma comunicação externa |
| SEC-003 | preflight | path resolve fora de `.asef`/workspace | rejeição antes do Docker |
| SEC-004 | filesystem | symlink Linux ou junction Windows resolve fora da raiz | rejeição sem percorrer/deletar target |
| SEC-005 | Docker | fanout limitado e filhos encerrados | PID budget observado |
| SEC-006 | Docker | alocação controlada acima do limite | OOM/resource outcome, sem travar host |
| SEC-007 | Docker | processo excede wall time | exit 124, timeout e container ausente |
| SEC-008 | Docker | stdout/stderr acima do teto | ambos truncados e sinalizados |
| SEC-009 | policy | import fora da allowlist | bloqueio estático antes da execução |
| SEC-010 | agent boundary | comentário tenta mudar policy/path/budget | output fora do contrato rejeitado; runtime inalterado |
| SEC-011 | Docker | socket/API Docker não montado nem acessível | socket ausente e mounts conciliados |
| SEC-012 | contract | artifact acima do teto UTF-8 | bloqueio antes de persistência/execução |

SEC-004 deve possuir prova real no ambiente suportado. No Windows, a fixture tentará junction contida apontando para target controlado fora da raiz da suite; no Linux CI, symlink. Se a primitive não puder ser criada, o caso será `UNSUPPORTED`, não skip/pass, e G5-11 permanecerá aberto até uma estratégia reproduzível ser aprovada.

SEC-010 não alegará que um modelo “resiste” a prompt injection. A prova é arquitetural: source é dado não confiável delimitado, o provider não possui tools/autoridade e qualquer artifact que tente mudar path/import/policy falha nos contratos do host.

### 5.4 Comando `asef security`

Interface proposta:

```text
asef security \
  --dataset-root datasets/security \
  --output .asef/security
```

- offline e keyless;
- uma execução por caso, sem mutação do SUT;
- JSON final sozinho no stdout;
- suite JSON/Markdown atômica;
- exit `0` para 12/12, `2` input/dataset inválido, `4` control failure e `7` runner/infraestrutura;
- continua casos posteriores após failure/error para entregar matriz completa;
- sem retry automático de resource attacks;
- cleanup obrigatório depois de cada caso e verificação de container órfão.

## 6. Hardening do runtime Docker

Adicionar labels fixas a containers ASEF, incluindo ownership, capability e identificador de execução, sem requisito ou dado sensível. Nomes continuam aleatórios e limitados.

O runner deve:

- manter `--network none`, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, usuário não root, tmpfs e budgets;
- preservar o perfil seccomp default/builtin; nunca usar `unconfined`;
- usar `--rm` e também remover pelo nome/ID exato em timeout, interrupção e falha do executor;
- não capturar `KeyboardInterrupt` como sucesso: limpar e repropagar/cancelar tipadamente;
- verificar ausência do container gerenciado após cleanup quando Docker responde;
- não montar socket, device, home, config Docker ou secret;
- registrar falha de cleanup separadamente do resultado do teste;
- nunca executar prune amplo.

O Security Dataset deverá conciliar argv e comportamento real. Um check estático sozinho não substitui a execução, e uma execução sem manifest/policy não substitui a prova de configuração.

## 7. `asef doctor`

### 7.1 Contratos e semântica

Criar `DoctorCheck` e `DoctorReport` com:

- check ID estável, categoria, status `PASS|WARN|FAIL|SKIP`;
- código de diagnóstico, resumo sanitizado e recomendação opcional;
- facts allowlisted, sem raw subprocess output;
- duração e timeout por check;
- status agregado `HEALTHY`, `DEGRADED` ou `BLOCKED`;
- versões do ASEF/Python e perfil solicitado;
- nenhum valor de secret, path de home ou Docker config.

`WARN` não bloqueia exit zero; qualquer `FAIL` produz `BLOCKED`/exit `7`. Argumento/contexto inválido retorna `2`. Exceção interna de check é `DOCTOR_CHECK_FAILED`, distinta de `REQUIREMENT_MISSING`, ainda que ambas possam bloquear a execução.

### 7.2 Checks iniciais

| Check | Obrigatório | Diagnóstico |
|---|---|---|
| `python-version` | sim | Python 3.13+ compatível |
| `asef-package` | sim | distribuição e versão resolvíveis |
| `host-profile` | sim | OS/arquitetura e suporte declarado |
| `output-root` | sim | `.asef` contida, gravável e probe removido |
| `docker-cli` | sim para execução | executável ausente versus erro de chamada |
| `docker-daemon` | sim para execução | daemon indisponível versus CLI ausente |
| `docker-linux-engine` | sim | `OSType=linux` para o perfil atual |
| `pytest-image` | sim | tag local resolve para image ID válido |
| `quality-image` | warn/obrigatória por capability | imagem ausente sem pull automático |
| `context` | quando informado | schema, system/skill e read scopes concretos |
| `live-key-presence` | somente modo live | presença booleana; nunca comprimento/valor |
| `managed-containers` | warn | containers ASEF residuais por label exata |

O daemon será consultado por comando estruturado e timeout curto. De `docker info` serão selecionados apenas server version, OSType, architecture e security options necessárias; o raw não será persistido. O doctor não lerá nem publicará `~/.docker/config.json`, que pode conter dados sensíveis.

### 7.3 Interface

```text
asef doctor [--context <path>] [--mode demo|live] [--output .asef/doctor]
```

O comando deve funcionar a partir do wheel fora do checkout. Recomendações serão comandos estáticos e revisados, nunca texto de erro refletido. Testes com executor falso cobrirão todas as combinações sem depender do host; uma integração real validará Docker Desktop/CI.

## 8. Retenção, cleanup e debug

### 8.1 Política inicial

| Classe | Retenção padrão | Regra |
|---|---|---|
| container/workspace/output temporário | imediata | obrigatório após sucesso, falha, timeout ou interrupção |
| state/report/evidence refs finais | indefinida local | somente cleanup explícito |
| logs operacionais | 1 MiB + 2 backups | rotação existente; cleanup explícito por idade |
| cassettes live | local, não publicável automaticamente | exclusão explícita; fora de artifacts CI |
| reports Smoke/security/quality/doctor na CI | 7 dias | scan antes de upload |
| debug | somente evidência sanitizada/limitada | nunca workspace, env, prompt ou resposta bruta |
| tombstones de cleanup | preservados | não entram no mesmo ciclo que documentam |

Esses defaults serão formalizados em `RetentionPolicy` versionada e documentados nos manifests/reports. “Indefinida local” não significa imutável ou backup; significa apenas ausência de deleção automática.

### 8.2 `asef cleanup`

Interface proposta:

```text
asef cleanup \
  --kind runs|smoke|security|quality|doctor|logs|containers|all \
  --older-than-days <N> \
  [--apply]
```

- sem `--apply`, apenas planeja e reporta;
- `N >= 1`; nenhum default destrutivo;
- raiz fixa sob `.asef`, sem path arbitrário;
- idade derivada de manifest/timestamp validado, não apenas mtime manipulável;
- unknown/malformed target é `SKIPPED`/erro, nunca deletado por heurística;
- revalidação de containment, identidade, symlink/junction e hash do plano imediatamente antes de aplicar;
- não segue links nem cruza filesystem por resolução indireta;
- container cleanup usa somente labels ASEF e IDs exatos;
- falha/arquivo bloqueado gera resultado parcial e exit `7`, sem alegar sucesso;
- report atômico em `.asef/maintenance/cleanup/<cleanup-id>.json` e Markdown opcional;
- bytes liberados são estimativa informativa;
- não promete secure erase.

Em plataformas onde a implementação disponível de remoção recursiva não puder provar resistência a symlink/junction, o apply deverá recusar o target e manter o dry-run. A primeira fatia caracterizará Windows e Linux antes de habilitar deleção real.

### 8.3 Cleanup obrigatório do workflow

Substituir `ignore_errors=True` silencioso em workspaces sensíveis por um serviço/observation comum. O resultado funcional continuará separado, mas resíduo de workspace/container será falha de infraestrutura ou warning bloqueante de publicação, nunca evento invisível. Evidências finais não são consideradas resíduo.

## 9. Sanitização e scanner

- consolidar uso da policy de sanitização em logs, diagnostics, doctor, security e cleanup;
- limitar bytes antes e depois da sanitização;
- nunca incluir matched secret no diagnóstico do scanner;
- preservar scanner de alta confiança e documentar cobertura/limitações;
- tornar arquivos unreadable, archives inválidos e limites excedidos visíveis no report de scan quando o escopo é artifact publicável;
- rejeitar symlink/junction e escape durante scan de diretório;
- testar OpenAI/GitHub/AWS/private key e atribuições sensíveis com sentinels montados em runtime;
- scan não substitui minimização de dados nem revisão humana de cassette live.

Não será adicionada heurística de entropia sem baseline: falsos positivos em fixtures podem tornar o controle inutilizável, como já ocorreu com `input_tokens` no Gate 4.

## 10. Estratégia de testes

### Contratos e unitários

- loader exige exatamente SEC-001..012, schemas e fileset conhecidos;
- duplicate keys, traversal, symlink, extra fields, oversize e executor desconhecido falham fechados;
- suite reconcilia todos os status e não transforma `UNSUPPORTED` em pass;
- doctor distingue requisito ausente, configuração inválida e erro interno;
- doctor nunca reflete env, raw Docker output ou secret;
- recommendations pertencem a allowlist;
- cleanup é dry-run por padrão;
- apply exige idade/selector válidos e nunca cruza `.asef`;
- manifest inválido, TOCTOU, symlink, junction e arquivo bloqueado não são apagados;
- tombstone concilia planned/deleted/failed/skipped;
- DEBUG não adiciona campos proibidos;
- import boundaries preservam o core sem Docker/tooling.

### Integração Docker/filesystem

- doze casos reais e determinísticos no ambiente suportado;
- resource attacks usam limites pequenos e hard timeout externo;
- nenhum container gerenciado permanece após cada caso;
- socket Docker, env sensível, rede e host paths ficam ausentes;
- junction Windows e symlink Linux possuem prova real;
- interruption/timeout removem container por ID/nome exato;
- cleanup dry-run não altera hashes; apply remove apenas fixtures autorizadas;
- target externo de junction mantém hashes após cleanup;
- doctor real diferencia daemon/imagem e termina sem mutação.

### Regressão

- core mantém branch coverage mínima de 85%;
- Smoke permanece 20/20;
- quality conformance permanece verde;
- seis jobs passam sem provider/rede live/secret;
- wheel instala sem dependências e `asef doctor` funciona fora do checkout;
- demo keyless continua `SUCCEEDED/ACCEPTED`;
- source, wheel, sdist, logs e artifacts passam no scanner.

## 11. CI e evidências

Adicionar job `alpha-security` sem alterar a autoridade dos jobs existentes:

1. instalar o package atual;
2. construir/puxar somente imagens pinadas necessárias;
3. remover `OPENAI_API_KEY` do ambiente do comando;
4. executar `asef security` e exigir 12/12;
5. executar `asef doctor` em ambiente preparado e validar report;
6. provar cleanup dry-run/apply somente numa raiz temporária controlada;
7. verificar ausência de containers ASEF órfãos;
8. executar secret scan nos reports/logs;
9. publicar somente suite, doctor e cleanup reports sanitizados;
10. usar retenção de sete dias e `if-no-files-found: error`.

O job não executa provider, não recebe credencial e não usa `docker system prune`. Os cinco jobs atuais permanecem independentes. O caso de junction Windows continua comprovado localmente no ambiente de referência; a CI Linux prova symlink.

## 12. Fatias de implementação

1. **5.7.1 — Threat model, contratos e política:** congelar semântica do dataset, doctor, retention/cleanup e caracterizar remoção segura em Windows/Linux.
2. **5.7.2 — Dataset e runner:** materializar doze casos, loader estrito, executores internos, report agregado e CLI `asef security`.
3. **5.7.3 — Hardening Docker:** labels, socket, interrupção, orphan detection, cleanup observável e casos SEC Docker.
4. **5.7.4 — Doctor:** checks tipados, CLI, executor falso, integração real e report sanitizado.
5. **5.7.5 — Retention/cleanup/debug:** policy versionada, dry-run/apply seguro, tombstones, junction/symlink, logs/scanner e remoção de cleanups silenciosos.
6. **5.7.6 — CI e revisão:** job `alpha-security`, regressões, package isolado, secret scan, documentação, parecer e candidata pré-alpha.

Cada fatia termina com testes próprios e revisão. A implementação pode entregar doctor antes do cleanup destrutivo; se a remoção segura não for comprovada, cleanup permanece dry-run e o incremento não fecha.

## 13. Critérios de aceite

O incremento somente pode ser aprovado quando:

1. `SEC-001` a `SEC-012` existem como casos públicos versionados;
2. nenhum manifest controla comando, imagem ou mount arbitrário;
3. suite executa offline/keyless e termina 12/12 sem skip/unsupported;
4. cada pass possui evidência verificável do controle correspondente;
5. SEC-004 possui prova real de junction Windows e symlink Linux;
6. resource attacks são limitados e não deixam processos/containers;
7. prompt injection é descrita como prova de autoridade do host, não robustez universal do modelo;
8. `asef doctor` funciona a partir do wheel fora do checkout;
9. doctor distingue CLI, daemon, image, context, filesystem e requisito live;
10. doctor não instala, corrige, chama provider, imprime secret ou persiste raw Docker output;
11. retention policy cobre todas as classes conhecidas e não promete secure erase;
12. cleanup é dry-run por padrão e exige `--apply` explícito;
13. cleanup só atua sob `.asef`, por selectors/idade/manifest válidos;
14. symlink, junction, TOCTOU, target malformed e arquivo bloqueado falham seguros;
15. nenhum prune amplo ou deleção de recurso sem label ASEF existe;
16. cleanup de workspace/container deixa de ser silencioso;
17. DEBUG não aumenta a coleta de dados proibidos;
18. scanner não imprime valor encontrado e torna erro de scan publicável visível;
19. reports security/doctor/cleanup são atômicos, limitados e sanitizados;
20. source, wheel, sdist, logs e evidências passam no scanner;
21. Smoke 20/20, quality conformance e branch coverage >=85% permanecem verdes;
22. job `alpha-security` e os cinco jobs anteriores passam;
23. G5-11, G5-15 e G5-16 recebem links de evidência reproduzível;
24. README, arquitetura, progresso, journal e livro refletem limitações reais;
25. Lucas revisa o parecer e aprova a conclusão/publicação.

## 14. Critérios de parada

Interromper e revisar o desenho se:

- algum caso exigir secret real, provider live ou rede externa funcional;
- dataset precisar fornecer shell/argv/mount/imagem arbitrários;
- um caso puder consumir recursos fora de hard budgets;
- `UNSUPPORTED`, skip ou erro for contabilizado como pass;
- doctor precisar ler/expor Docker config, env completo ou valor de chave;
- doctor fizer pull, build, login, prune ou correção automática;
- cleanup aceitar root/path arbitrário ou deletar sem `--apply`;
- containment depender apenas de string/prefixo;
- junction/symlink puder levar à remoção do target;
- cleanup usar `ignore_errors` e ainda reportar sucesso;
- container for removido por nome parcial ou sem label ASEF;
- debug preservar workspace, prompt, resposta ou environment bruto;
- scanner passar silenciosamente sobre artifact obrigatório ilegível;
- core importar Docker, filesystem adapter ou conceitos Python específicos;
- o trabalho expandir para pentest genérico, SBOM/signing, outras linguagens ou Etapa 6.

## 15. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Dataset parecer certificação | linguagem limitada, ambiente/versão no report e limitações obrigatórias |
| Ataque de recurso afetar host/CI | fixtures mínimas, budgets rígidos, execução sequencial e cleanup verificado |
| SEC-004 virar skip permanente no Windows | junction real, caracterização inicial e bloqueio do Gate se unsupported |
| Prompt injection alegar robustez de modelo | validar autoridade/policy do host, não comportamento probabilístico |
| Doctor vazar configuração Docker | facts allowlisted; não ler config; descartar raw output |
| Doctor mascarar erro interno | códigos distintos e executor falso adversarial |
| Cleanup apagar dados externos | root fixa, manifest, lstat/resolve, junction detection, revalidação e dry-run |
| TOCTOU entre plano e apply | fingerprint/identity do target e nova validação imediatamente antes da remoção |
| Arquivo Windows bloqueado | partial failure explícita, sem retry destrutivo ou sucesso falso |
| Evidência crescer indefinidamente | cleanup explícito por classe/idade e reports de manutenção |
| Redaction incentivar coleta excessiva | minimização anterior à sanitização e campos allowlisted |
| Scanner gerar falso senso de segurança | documentar assinaturas/limites e manter revisão humana |
| Novo job duplicar responsabilidades | job security isolado e jobs anteriores preservados |

## 16. Evidência esperada ao final

- threat model atualizado e matriz SEC rastreável;
- doze casos, loader, runner e reports;
- prova real de Docker/filesystem por ambiente;
- contracts/reports do doctor e sessões healthy/blocked;
- retention policy versionada;
- cleanup dry-run/apply com tombstone e testes adversariais;
- prova de nenhum container/workspace residual;
- logs/debug/scanner revisados;
- job `alpha-security` verde com artifacts de sete dias;
- regressão completa, package isolado e demo keyless;
- parecer final do 5.7 e atualização de G5-11/G5-15/G5-16;
- decisão humana sobre candidata pré-alpha.

## 17. Base técnica verificada no planejamento

O desenho mantém os controles suportados pelo CLI Docker: capabilities removidas, filesystem read-only, usuário explícito, limites de CPU/memória/PIDs, network mode, tmpfs, labels, `--rm` e `no-new-privileges`. O perfil seccomp default permanece ativo; não será usado `seccomp=unconfined`.

`asef doctor` usará `docker info --format` somente como fonte transitória e selecionará campos allowlisted. A própria documentação Docker alerta que o diretório de configuração do CLI pode conter informações sensíveis, portanto ele não será lido nem publicado.

Para cleanup, Python documenta que `rmtree()` não percorre o conteúdo de junctions Windows desde 3.8 e expõe `rmtree.avoids_symlink_attacks`; Python 3.13 também oferece `Path.is_junction()`. Essas características serão verificadas em runtime, mas não eliminam a necessidade de containment e revalidação próprias.

Artifacts de GitHub Actions aceitam `retention-days`; o repositório já usa sete dias, dentro do intervalo permitido para repositórios públicos. A política local permanece distinta da retenção gerenciada pelo GitHub.

Fontes oficiais consultadas:

- [Docker — `docker container run`](https://docs.docker.com/reference/cli/docker/container/run/);
- [Docker — perfil seccomp](https://docs.docker.com/engine/security/seccomp/);
- [Docker — `docker system info`](https://docs.docker.com/reference/cli/docker/system/info/);
- [Docker — configuração do CLI e dados sensíveis](https://docs.docker.com/reference/cli/docker/);
- [Python 3.13 — `pathlib`](https://docs.python.org/3.13/library/pathlib.html);
- [Python — `shutil.rmtree`](https://docs.python.org/3/library/shutil.html);
- [GitHub Actions — retenção customizada de artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data#configuring-a-custom-artifact-retention-period).
