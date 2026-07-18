# Incremento 5.9 — Avaliação final, livro e Gate 5

- **Data do planejamento:** 2026-07-17
- **Estado:** 5.9.1–5.9.5 concluídas; candidata local 5.9.6 pronta para commit/CI e decisão do Gate
- **Dependências:** incrementos 5.1 a 5.8 concluídos; pré-release `v0.1.0a7` publicada; postflight remoto aprovado; sete jobs verdes nas execuções `29647693611` e `29648119788`
- **Gate relacionado:** G5-19 como lacuna principal; revalidação de G5-01 a G5-20
- **Decisão vigente:** Lucas confirmou que não haverá participante externo neste fechamento, consentiu com a avaliação interna e com a publicação somente do resultado anonimizado, e definiu o chat como canal. A evidência externa fica adiada; a sessão interna não satisfaz independência. Correções materiais, publicação do resultado e decisão do Gate preservam checkpoints humanos. Etapa 6 continua não autorizada.

## 1. Objetivo

Transformar as evidências acumuladas do Alpha Python em um pacote decisório auditável e submetê-lo a uma avaliação externa real, limitada e ética. O incremento deve responder, sem ampliar artificialmente as alegações do projeto, se a experiência publicada permite que um QE independente instale o ASEF, diagnostique o ambiente, execute a demo e interprete corretamente o report usando apenas material público.

O 5.9 também fecha a baseline factual da Etapa 5, registra retrospectiva e lição aprendida, reconcilia o livro e apresenta todos os critérios G5 com evidência, risco residual ou bloqueio explícito. CI verde e avaliação externa informam a decisão; somente Lucas aprova ou rejeita o Gate 5.

## 2. Resultado esperado e fronteiras de decisão

Ao final, o projeto deverá possuir:

1. release/commit alvo congelado e identificável por hashes;
2. protocolo de avaliação externa versionado antes da sessão;
3. pelo menos uma sessão válida com QE externo real ou um bloqueio honesto por ausência de participante;
4. findings anonimizados, classificados e rastreáveis;
5. regressão final proporcional a qualquer correção;
6. baseline, retrospectiva, lição aprendida e source map reconciliados;
7. pacote de evidências G5-01 a G5-20;
8. recomendação técnica separada da decisão humana.

O incremento não presume aprovação. Resultados possíveis são:

- **pronto para decisão:** todas as evidências obrigatórias existem e nenhum bloqueio invalida o Gate;
- **pronto com riscos residuais:** riscos não críticos estão explícitos e podem ser aceitos ou rejeitados por Lucas;
- **bloqueado:** participante externo ausente, finding crítico/alto aberto, evidência contraditória ou regressão falha;
- **rejeitado tecnicamente:** um ou mais critérios obrigatórios não podem ser sustentados no escopo do Alpha.

## 3. Escopo

### 3.1 Incluído

- inventário imutável de release, tag, commits, assets, hashes e CIs da `v0.1.0a6`;
- matriz G5-01 a G5-20 com links para evidência primária;
- verificador offline e testável da estrutura do pacote de Gate;
- protocolo, roteiro, questionário e template de observação externa;
- preflight do protocolo pelo mantenedor, sem contabilizá-lo como avaliação externa;
- uma sessão obrigatória com QE externo elegível;
- segunda sessão opcional, relatada separadamente, sem alegação estatística;
- instalação de wheel publicado em diretório vazio e build da imagem a partir do source archive correspondente;
- execução `doctor`, demo keyless, leitura de JSON/Markdown e cleanup dry-run;
- avaliação da compreensão de status, classificação, evidências, limitações e próxima ação;
- minimização, anonimização e revisão do material publicável;
- triagem por severidade, impacto e critério G5 afetado;
- correções estritamente necessárias, se autorizadas após a triagem;
- repetição da sessão quando uma correção alterar o caminho avaliado;
- atualização da baseline com dados observados e lacunas explícitas;
- retrospectiva da Etapa 5, Lesson 003 e reconciliação do livro;
- regressão completa, package audit e scanner final;
- pacote de evidências e formulário de decisão do Gate 5;
- proposta condicional de nova pré-release quando houver mudança material.

### 3.2 Não incluído

- Developer Preview de três a cinco QEs, reservada ao Gate 7;
- pesquisa estatística de usabilidade, benchmark humano ou generalização populacional;
- telemetria, gravação de tela, áudio, vídeo ou coleta de dados pessoais;
- uso de código proprietário, repositório real do participante ou workload hostil;
- execução live paga nova sem autorização específica de custo e necessidade;
- teste de qualidade geral de modelo/provider;
- TypeScript, Java, MCP, interface gráfica ou Etapa 6;
- correção automática do SUT ou ampliação do escopo funcional do Alpha;
- release estável, certificação de segurança ou alegação de prontidão para produção;
- aprovação automática do Gate 5 por teste, IA, CI ou participante.

## 4. Findings da baseline

1. A `v0.1.0a6` está publicada com wheel e sdist auditados; o wheel possui SHA-256 `0b40e6597acb1064c15122a7ac96934e7b1e3f62df64bf5ff1dedcd62831ff72` e o sdist `b2963ce50ddcb4bf52080510fdc55656a9ab7cd42ff66ce3008c76fac2f46289`.
2. As sete capacidades públicas passaram repetidamente na CI. A sessão externa não deve repetir mecanicamente a CI; deve avaliar a jornada e a compreensão humana.
3. G5-01 a G5-18 e G5-20 possuem evidência técnica registrada. G5-19 permanece parcial por falta da retrospectiva final e da consolidação completa das métricas e decisões.
4. O walkthrough frio do 5.8 foi executado pelo mantenedor/automação. Ele prova consistência operacional, não compreensão externa.
5. Nenhum QE externo real executou o quickstart. O README e o livro preservam corretamente essa limitação.
6. O quickstart e a matriz canônica de suporte ainda continham frases históricas que identificavam `v0.1.0a5` como última release e `0.1.0a6` como candidata. O planejamento corrige essas divergências editoriais, mas o verificador documental deverá ganhar uma regra contra nova deriva.
7. A imagem Docker não está embutida no wheel. A sessão precisa usar o source archive correspondente para construir `asef/python-pytest:8.3.3` sem recorrer ao checkout do autor.
8. O Gate 5 não possui pacote de evidências consolidado, apenas plano/matriz de aceite.
9. A baseline contém estimativas do autor até o início do Dia 6. Dados posteriores não podem ser inferidos sem relato de Lucas.
10. A voz autoral ainda é necessária para “o que faria diferente”, critério pessoal de pronto e percepção após o Alpha Python.

## 5. Princípios da avaliação

### 5.1 A release sob avaliação é congelada

O protocolo registra tag, commit, URLs, nomes, tamanhos e SHA-256 antes da sessão. Nenhum asset é substituído. Se uma correção for necessária, ela produz novo commit e, quando material para a jornada, nova candidata; o resultado anterior permanece histórico.

### 5.2 Preflight não é validação externa

Mantenedor, Codex, CI ou automação podem ensaiar o roteiro e validar comandos. Nenhum deles conta como participante externo. O relatório deve distinguir `preflight` de `external_session`.

### 5.3 O participante não é avaliado

Falhas são findings sobre produto, documentação, protocolo ou ambiente. O relatório não atribui nota, competência ou culpa ao QE. Tempo por tarefa é descritivo e não possui threshold de aprovação.

### 5.4 Ajuda do autor é uma intervenção observável

O facilitador pode resolver apenas logística e riscos de segurança. Explicar comando, interpretação ou localização documental altera o resultado da tarefa e deve ser registrado. Uma tarefa central concluída somente após explicação individual não atende QA-USA-003.

### 5.5 Ausência de participante não pode ser simulada

Se Lucas não disponibilizar um QE elegível, a fatia externa fica `BLOCKED`. Walkthrough automatizado adicional, role-play por IA ou execução pelo mantenedor não substitui a evidência.

### 5.6 Evidência mínima e privacidade por padrão

Somente resultado estruturado, tempos aproximados, intervenções e observações necessárias serão versionados. Nome, e-mail, empresa, IP, username, paths pessoais, áudio, vídeo, tela, terminal bruto e conteúdo não autorizado não serão coletados.

## 6. Participante, consentimento e ambiente

### 6.1 Elegibilidade mínima

O participante obrigatório deve:

- atuar ou ter experiência prática em Quality Engineering/testes de software;
- conseguir usar PowerShell, Python virtual environment e Docker Desktop em nível básico;
- não ter escrito o ASEF nem participado das decisões 5.1 a 5.8;
- não ter recebido explicação individual do fluxo antes da sessão;
- aceitar a publicação anonimizada das observações estruturadas.

Conhecimento profundo de IA, arquitetura do ASEF ou LangGraph não é exigido. Familiaridade prévia com o repositório deve ser declarada e pode tornar a sessão informativa, não obrigatória.

### 6.2 Identidade pública

O repositório usa apenas `P01`, `P02` e assim por diante. O registro contém perfil amplo, como “QE com experiência em automação Python”, sem empregador, localização específica ou combinação que reidentifique a pessoa.

### 6.3 Consentimento

Antes de começar, o participante recebe e aceita:

- objetivo e duração máxima;
- dados que serão anotados;
- ausência de gravação por padrão;
- direito de interromper ou retirar observações antes da publicação;
- natureza experimental do software;
- proibição de usar credenciais, dados ou código reais.

O repositório registra apenas `consent_obtained: true`, data e versão do protocolo. Assinatura ou dado de contato permanece fora do Git e sob responsabilidade do facilitador, caso seja necessário.

### 6.4 Ambiente suportado

- Windows suportado pela documentação;
- PowerShell;
- Python 3.13;
- Docker Desktop iniciado;
- diretório inicialmente vazio e descartável;
- `OPENAI_API_KEY` ausente;
- wheel e source archive oficiais da mesma tag;
- nenhuma dependência do checkout local do mantenedor.

Ambiente incompatível descoberto durante a sessão é registrado como `ENVIRONMENT_BLOCKED`. Ele não vira sucesso nem finding automático do produto; o protocolo decide se a tentativa deve ser reagendada.

## 7. Protocolo da sessão externa

### 7.1 Preparação pelo facilitador

1. entregar apenas URL da release, README e documentação pública;
2. confirmar consentimento e ambiente descartável;
3. remover `OPENAI_API_KEY` do processo;
4. iniciar cronômetro apenas para observação descritiva;
5. não fornecer comandos fora do material público;
6. anotar intervenções com motivo e tarefa afetada.

### 7.2 Tarefas

| ID | Tarefa | Evidência observável | Resultado válido |
|---|---|---|---|
| EXT-01 | identificar estado, suporte e limitações | participante localiza pré-alpha, host/profile suportado e avisos | explica que não é produção nem sandbox universal |
| EXT-02 | obter e verificar a release | wheel/sdist corretos e hashes conferidos | usa somente assets `v0.1.0a6` ou candidata posterior autorizada |
| EXT-03 | instalar e preparar imagem | venv limpo, wheel instalado, imagem pytest construída do sdist | nenhum checkout ou package local é usado |
| EXT-04 | diagnosticar | `asef doctor --mode demo` e report correspondente | distingue `HEALTHY`, `DEGRADED` e `BLOCKED` e decide corretamente se prossegue |
| EXT-05 | executar a demo | `asef run`, exit e stdout JSON | encontra a run e não usa chave/provider |
| EXT-06 | localizar e validar reports | paths do stdout, parser e/ou schema | abre JSON e Markdown da mesma run e reconhece o JSON como normativo |
| EXT-07 | interpretar resultado | respostas estruturadas sem explicação do autor | identifica status, classificação, resultado funcional, integridade, fatos, inferências, recomendações e limitações |
| EXT-08 | planejar cleanup e localizar suporte | dry-run e links públicos | não usa `--apply` nem `docker system prune`; encontra troubleshooting, segurança e contribuição |

### 7.3 Perguntas de compreensão

Sem mostrar respostas esperadas, o facilitador pergunta:

1. A run terminou? Qual evidência sustenta a resposta?
2. Qual foi a classificação funcional e o que ela permite concluir?
3. O que `ACCEPTED` não prova?
4. Quais referências de evidência estão verificadas, ausentes ou divergentes?
5. Qual conteúdo é fato e qual é inferência?
6. Há recomendação acionável? Ela altera automaticamente o SUT?
7. Quais limitações são relevantes antes de experimentar outro projeto?
8. Qual seria a próxima ação segura para limpar ou investigar o ambiente?

Respostas são resumidas semanticamente; transcrição literal longa não é necessária.

### 7.4 Estados por tarefa

- `COMPLETED_INDEPENDENTLY` — concluída apenas com documentação pública;
- `COMPLETED_WITH_RECOVERY` — erro recuperado pelo participante usando documentação;
- `COMPLETED_WITH_INTERVENTION` — exigiu explicação individual;
- `FAILED` — material público não permitiu concluir;
- `ENVIRONMENT_BLOCKED` — precondição suportada indisponível;
- `NOT_ATTEMPTED` — sessão interrompida antes da tarefa.

### 7.5 Validade da sessão obrigatória

A sessão atende a evidência mínima quando:

- consentimento e elegibilidade estão registrados;
- EXT-01 a EXT-07 são tentadas;
- EXT-03 a EXT-07 terminam independentemente ou com recuperação documental;
- nenhuma tarefa central depende de explicação individual;
- o participante interpreta corretamente `ACCEPTED`, integridade e limitações;
- não ocorre finding crítico ou alto não resolvido;
- o relatório anonimizado passa pela revisão do participante ou pelo processo de retirada acordado.

EXT-08 pode produzir finding sem invalidar a compreensão central, desde que nenhuma ação destrutiva tenha sido incentivada. Uma única sessão demonstra o caso observado; não autoriza alegação de usabilidade geral.

## 8. Findings e decisão de correção

### 8.1 Severidade

| Severidade | Definição | Efeito no Gate |
|---|---|---|
| Crítica | risco de exposição, perda externa, execução proibida, integridade falsa ou alegação materialmente perigosa | bloqueia; correção e nova avaliação obrigatórias |
| Alta | impede instalação/demo/interpretação central no ambiente suportado ou exige explicação individual do autor | bloqueia; correção e repetição das tarefas afetadas |
| Média | fricção recuperável, ambiguidade secundária ou desvio documental sem conclusão perigosa | corrigir ou registrar risco explícito antes da decisão |
| Baixa | clareza editorial, navegação ou conveniência sem impacto no resultado | pode permanecer como backlog rastreado |

### 8.2 Campos obrigatórios

Cada finding possui ID `EXT-F-NNN`, tarefa, severidade, observação, evidência, impacto, critério G5, reprodução, decisão, responsável, estado e verificação. Texto bruto do participante não é exigido.

### 8.3 Limite de remediação

Correções do 5.9 devem restaurar o critério já planejado. Finding que exija linguagem adicional, UI, suporte genérico a projetos, sandbox hostil ou redesign amplo vira risco/backlog e pode bloquear o Gate; não expande silenciosamente o incremento.

## 9. Artefatos planejados

| Artefato | Finalidade |
|---|---|
| `docs/evaluations/alpha-python-external-evaluation-protocol.md` | protocolo congelado e respostas esperadas sob acesso do facilitador |
| `docs/templates/external-evaluation-observation-template.md` | instrumento anonimizado de sessão/findings |
| `docs/evaluations/YYYY-MM-DD-alpha-python-external-evaluation-P01.md` | resultado publicável da sessão obrigatória |
| `docs/project/stage-05-alpha-baseline.md` | baseline técnica e humana final do Alpha |
| `docs/project/gates/gate-05-evidence-package.md` | matriz consolidada, riscos, parecer e decisão |
| `book/retrospectives/YYYY-MM-DD-etapa-05.md` | retrospectiva factual e voz do autor |
| `docs/lessons/LESSON-003-etapa-05-alpha-python.md` | lição aprendida reutilizável |
| `docs/reviews/YYYY-MM-DD-revisao-incremento-59.md` | revisão técnica independente do pacote |
| `journal/YYYY-MM-DD-etapa-05-incremento-59-*.md` | decisões e eventos contemporâneos |
| `tools/gate5_evidence_check.py` e testes | completude estrutural offline, sem decidir o Gate |

Arquivos com data só serão materializados quando o evento ocorrer. O plano não cria resultado fictício antecipadamente.

## 10. Baseline final e livro

### 10.1 Dados factuais

Consolidar, com fonte e natureza:

- datas e dias corridos de 5.1 a 5.9;
- releases, commits, CIs e retrabalhos;
- testes, skips, coverage, Smoke e Security finais;
- hashes e tamanhos dos artifacts avaliados;
- custo live já observado e ausência de novo gasto, se aplicável;
- duração e estados das tarefas externas;
- findings por severidade e estado;
- decisões humanas que mudaram propostas da IA.

### 10.2 Dados que exigem voz de Lucas

Antes da retrospectiva, solicitar explicitamente:

- horas/interações atuais, somente se houver estimativa que Lucas deseje registrar;
- percepção após concluir o Alpha Python;
- o que faria diferente ao reiniciar;
- critério pessoal para chamar uma entrega de pronta;
- avaliação do equilíbrio entre velocidade, compreensão, revisão e cansaço.

Ausência de resposta aparece como dado não atualizado, nunca como estimativa da IA.

### 10.3 Limites das conclusões

Não calcular percentual de produtividade sem baseline comparável. Não extrapolar uma sessão para comunidade, mercado ou população de QEs. Não atribuir causalidade exclusiva à IA a partir de dias corridos.

## 11. Pacote e auditor do Gate 5

O pacote deverá conter, para cada G5-01 a G5-20:

- estado `MET`, `MET_WITH_RESIDUAL_RISK`, `BLOCKED` ou `NOT_MET`;
- afirmação limitada ao que foi observado;
- uma ou mais evidências primárias versionadas;
- ambiente/data/versão relevantes;
- risco residual e impacto;
- dependências de decisão humana.

O auditor offline verificará apenas propriedades mecânicas:

- exatamente vinte IDs únicos e ordenados;
- estados pertencentes à enumeração;
- links locais existentes e anchors válidos;
- release/tag/commit/hashes consistentes com o inventário congelado;
- sessão externa válida referenciada para QA-USA-003/G5-18;
- retrospectiva, lesson, baseline, review e journal presentes;
- nenhum placeholder, checkbox indecidido ou claim proibida;
- findings críticos/altos não podem coexistir com recomendação `APPROVE`;
- decisão humana permanece vazia antes do checkpoint e explícita depois dele.

O script retorna não zero para pacote incompleto, mas nunca escreve `APPROVED` nem escolhe riscos por Lucas.

## 12. Estratégia de testes e CI

### 12.1 Testes do instrumento

- parser/validator do resultado anonimizado;
- IDs, estados, severidades e referências desconhecidas rejeitados;
- consentimento falso/ausente invalida publicação da sessão;
- tarefa central omitida invalida a evidência obrigatória;
- intervenção em tarefa central impede marcar sessão como independente;
- finding crítico/alto aberto impede recomendação de aprovação;
- dados pessoais e paths de usuário conhecidos são rejeitados pelo scanner;
- protocolo congelado não pode ser alterado retroativamente sem nova versão.

### 12.2 Preflight publicado

Em diretório vazio, usando downloads oficiais:

1. verificar SHA-256;
2. extrair sdist e construir somente a imagem pytest;
3. instalar wheel com `--no-deps`;
4. remover `OPENAI_API_KEY`;
5. executar doctor e demo;
6. validar report pelo parser e Draft 2020-12;
7. executar cleanup dry-run;
8. executar auditor público 9/9;
9. escanear evidências;
10. verificar ausência de containers gerenciados.

### 12.3 Regressão final

- suíte core completa com branch coverage mínima de 85%;
- testes opcionais/frameworks no ambiente disponível;
- integrações Docker e quality;
- Smoke 20/20 em duas repetições;
- Security 12/12;
- provas Linux de cleanup/symlink;
- docs checker e gate evidence checker;
- secret scan em source, package, avaliação e evidências;
- build wheel/sdist e auditoria instalada;
- `git diff --check` e ausência de órfãos.

### 12.4 CI

Os sete jobs atuais permanecem autoridades independentes. A checagem mecânica do pacote entra no job `public-experience`, sem criar chamada live, secret, crawler externo ou execução da sessão humana em CI. Evidência externa já publicada é validada estruturalmente, não reproduzida.

## 13. Regra para correção e nova release

### Caminho A — `v0.1.0a6` permanece a release avaliada

Usar quando a sessão passa e as mudanças posteriores afetam somente evidência, governança, retrospectiva ou livro. Não criar versão vazia apenas para marcar o Gate.

### Caminho B — candidata `0.1.0a7`

Usar quando houver alteração em:

- código/package/schema/CLI;
- comportamento do doctor, run, report ou cleanup;
- instrução pública usada nas tarefas EXT-01 a EXT-08;
- CI/package audit que sustente uma alegação do Gate.

Nesse caminho, incrementar metadata/fallbacks, reconstruir artifacts, repetir preflight, tarefas externas afetadas, regressão e CI. Tag/pré-release exigem autorização separada antes da decisão do Gate.

### Caminho C — Gate bloqueado

Usar quando a correção ultrapassar o escopo, o participante não estiver disponível ou finding crítico/alto não puder ser encerrado. O pacote permanece publicável como rejeição/bloqueio factual.

## 14. Fatias de implementação

### 5.9.1 — Inventário e contrato de evidências

**Entregas:** inventário congelado da `v0.1.0a6`; protocolo; template; contratos/validator; regra de consistência de versão no docs checker; correção da frase histórica do quickstart; matriz inicial G5.

**Aceite:** hashes/commits/CIs reconciliam; testes adversariais do instrumento passam; nenhum resultado externo é pré-preenchido; revisão humana aprova o protocolo antes de recrutar/executar.

**Progresso em 2026-07-17:** inventário `1.0.0` congelou tag, commits, dois assets, hashes e três matrizes públicas de sete jobs. G5-01 a G5-20 possuem 40 referências primárias: 18 estão `MET`, G5-18 está `MET_WITH_RESIDUAL_RISK` até observação externa e G5-19 permanece `PARTIAL`. Protocolo e template anonimizados foram criados sem resultado fictício. O checker rejeita IDs/paths/jobs/digests divergentes, aprovação contraditória, PII, consentimento/privacidade ausentes, intervenção central e finding crítico/alto aberto. O docs checker agora reconcilia README, quickstart e suporte com a metadata. A regressão aprovou 355 testes/33 skips e branch coverage de 85%; a fatia aguarda revisão humana antes da 5.9.2.

**Decisão humana em 2026-07-17:** Lucas aprovou a 5.9.1 e autorizou o ensaio 5.9.2. Nenhuma sessão externa foi autorizada.

### 5.9.2 — Ensaio da release e kit do participante

**Entregas:** preflight integral a partir dos assets remotos, checklist do facilitador, pacote de links públicos e parecer de prontidão da sessão.

**Aceite:** jornada completa em diretório vazio, auditor 9/9, scanner verde e zero dependência do checkout; finding conhecido é resolvido ou torna a sessão bloqueada. O ensaio não conta como avaliação externa.

**Progresso em 2026-07-17:** os assets oficiais foram baixados novamente e conferiram com os hashes congelados. Wheel `0.1.0a6` instalou com `--no-deps`; imagem pytest foi construída do sdist; doctor terminou `DEGRADED/READY` com 12 checks; demo `SUCCEEDED/ACCEPTED`; auditor 9/9; cleanup `DRY_RUN_COMPLETE`; scanner verde; zero containers gerenciados. O finding `PREFLIGHT-F-001` constatou que README, quickstart e suporte dentro da tag dizem que `v0.1.0a5` é a última release e `0.1.0a6` ainda não foi publicada. Como isso afeta EXT-01/EXT-02, o kit ficou `HOLD`, o preflight `BLOCKED/NOT_READY` e a 5.9.3 não pode começar antes de decisão corretiva. A regressão final aprovou 356 testes/33 skips, coverage 85%, checker 10/10 e documentação 126 arquivos/107 links sem findings.

**Decisão corretiva em 2026-07-17:** Lucas autorizou somente a preparação da candidata `0.1.0a7`. A separação canônica entre release publicada e versão em desenvolvimento foi implementada e protegida pelo docs checker. Wheel/sdist locais passaram em build, scanner e ensaio fora do checkout: metadata `0.1.0a7`, doctor `DEGRADED/READY` 12 checks, demo `SUCCEEDED/ACCEPTED`, auditor 9/9, cleanup `DRY_RUN_COMPLETE` e zero containers. Regressão: 357 testes/33 skips, coverage 85%. Parecer `READY_FOR_PUBLICATION_CHECKPOINT`; sem publicação imutável, `PREFLIGHT-F-001` continua aberto, kit em `HOLD` e 5.9.3 bloqueada.

**Checkpoint público em 2026-07-17:** o commit `58ea802` foi enviado à `main` com autorização de Lucas. A CI `29620941881` aprovou os sete jobs canônicos. Tag e pré-release não foram criadas; continuam dependentes de nova decisão explícita.

**Publicação e postflight em 2026-07-18:** Lucas autorizou a tag e a pré-release. O commit de release `79fbeb0` passou nos sete jobs da CI `29647693611`; `v0.1.0a7` foi publicada com wheel e sdist auditados. Os assets remotos foram baixados novamente e passaram em hashes, docs checker 128/109, instalação sem dependências, doctor 12 checks, demo, auditor 9/9, cleanup, scanner e orphan check. `PREFLIGHT-F-001` está resolvido; kit/checklist estão `READY`; nenhuma sessão ou contato externo foi iniciado.

### 5.9.3 — Avaliação humana: externa adiada e interna acompanhada

**Decisão de contingência em 2026-07-18:** nenhum QE externo está disponível. Lucas (`I01`) executará as tarefas pelo chat, com papel de autor/mantenedor declarado, consentimento confirmado e resultado `INFORMATIVE_INTERNAL`. Essa sessão não será usada para alegar independência; feedback externo permanece posterior.

**Entregas atuais:** sessão I01, resultado interno anonimizado, questionário de compreensão, intervenções e findings; ausência de resultado externo registrada separadamente.

**Aceite:** consentimento; EXT-01 a EXT-08 tentadas; autoria e conhecimento prévio explícitos; nenhuma conclusão de independência; estado `INFORMATIVE_INTERNAL` ou bloqueio honesto; revisão de privacidade antes de versionar.

**Resultado em 2026-07-18:** sessão `I01` concluída como `INFORMATIVE_INTERNAL`. EXT-03 ficou `NOT_ATTEMPTED`; as demais tarefas terminaram com intervenção ou recuperação. Assistência da IA e papel autoral foram declarados. Resultado JSON/Markdown anonimizado passou à triagem sem alegação externa.

### 5.9.4 — Triagem e remediação limitada

**Entregas:** severidade/impacto/G5 de cada finding, decisão de escopo, correções autorizadas e repetição das tarefas afetadas.

**Aceite:** nenhum crítico/alto aberto para recomendar aprovação; médios resolvidos ou convertidos em risco explícito; regressão proporcional; caminho A, B ou C escolhido por Lucas antes de avançar.

**Resultado em 2026-07-18:** caminho A. `INT-F-001` HIGH e `INT-F-003` MEDIUM foram corrigidos por intervenção; `INT-F-002` MEDIUM foi aceito como risco porque a instalação humana isolada foi pulada. O postflight mitiga funcionamento técnico, não usabilidade externa. Nenhuma correção de produto, package ou release foi necessária.

### 5.9.5 — Baseline, retrospectiva, lesson e livro

**Entregas:** baseline final, retrospectiva Etapa 5, Lesson 003, source map, progresso, journal e limitações reconciliadas.

**Aceite:** fatos possuem fontes; estimativas estão rotuladas; voz de Lucas não é fabricada; contribuição da IA inclui sugestões aceitas, corrigidas e rejeitadas; G5-19 passa de parcial para atendido ou bloqueado com motivo.

**Resultado em 2026-07-18:** baseline final pré-Gate, retrospectiva editorial, Lesson 003, nota sobre autovalidação, proveniência e source map foram reconciliados. Métricas não atualizadas permaneceram ausentes em vez de estimadas. G5-19 passou a `MET`; redação editorial continua rascunho assistido até aprovação autoral própria.

### 5.9.6 — Regressão, pacote e decisão do Gate 5

**Entregas:** regressão completa, auditoria de package, review final, pacote G5-01 a G5-20, riscos residuais e formulário de decisão.

**Aceite técnico:** checkers verdes; CI pública verde no commit auditado; artifacts/hashes registrados; recomendação coerente com findings; release condicional concluída quando o caminho B for escolhido.

**Checkpoint final:** Lucas escolhe explicitamente `APPROVE`, `APPROVE_WITH_CONDITIONS` ou `REJECT/BLOCK`. Aprovação autoriza somente planejar a Etapa 6.

**Fechamento técnico em 2026-07-18:** regressão aprovou 362 testes/33 skips e branch coverage de 85%. O commit `2e7655e` e a CI `29654457005` aprovaram os sete jobs. Pacote e inventário final recomendam `APPROVE_WITH_CONDITIONS`; resta exclusivamente a decisão humana. Produto e package a7 não foram alterados.

### Modo acelerado autorizado para 5.9.3–5.9.6

As quatro fatias formam um fluxo contínuo de fechamento, sem checkpoints artificiais entre atualizações puramente factuais ou documentais:

1. executar 5.9.3 pelo chat com `I01`, consentimento confirmado e viés autoral explícito;
2. produzir o resultado anonimizado e validar contrato, privacidade e secret scan no mesmo ciclo;
3. triar imediatamente os findings e avançar pelo caminho A quando não houver correção material;
4. quando houver correção material, parar no checkpoint de escopo/release, corrigir somente o autorizado e repetir as tarefas afetadas;
5. consolidar 5.9.5 a partir dos fatos da sessão e da contribuição autoral fornecida por Lucas, sem fabricar percepção;
6. executar 5.9.6, reconciliar o inventário final e apresentar o Gate 5 para decisão explícita.

Somente quatro checkpoints humanos interrompem esse fluxo: autoridade/consentimento para a sessão; autorização de remediação material ou nova release; autorização para publicar o resultado anonimizado; decisão final do Gate 5. Commit/push do pacote final continua dependendo de autorização quando implicar publicação externa. Nenhuma atividade desse modo cria feature ou inicia a Etapa 6.

## 15. Critérios de aceite do incremento

1. release alvo possui tag, commit, assets, tamanhos e hashes congelados;
2. protocolo é versionado antes da sessão;
3. participante obrigatório é humano, externo e elegível;
4. consentimento e minimização de dados são comprovados sem PII no Git;
5. preflight usa somente assets/documentos públicos e diretório vazio;
6. sessão não usa checkout, secret, provider ou SUT real;
7. EXT-01 a EXT-07 são tentadas e possuem estado explícito;
8. intervenções do facilitador são registradas;
9. compreensão de `ACCEPTED`, integridade e limitações é observada;
10. resultado externo é anonimizado e escaneado;
11. ausência de participante produz bloqueio, não simulação;
12. todos os findings possuem severidade, impacto, G5 e decisão;
13. crítico/alto aberto impede recomendação de aprovação;
14. correção material repete tarefas afetadas;
15. regra A/B/C de release é aplicada sem version bump vazio;
16. G5-01 a G5-20 possuem estado e evidência primária;
17. gate checker rejeita pacote incompleto/contraditório;
18. baseline separa fato, estimativa, percepção e dado ausente;
19. retrospectiva e lesson preservam voz e julgamento humanos;
20. livro não extrapola uma sessão para validação geral;
21. regressão core mantém branch coverage mínima de 85%;
22. Smoke permanece 20/20 e Security 12/12;
23. sete jobs públicos passam no commit final;
24. source, package, avaliação e evidências passam no secret scan;
25. package instalado repete doctor/demo/report/cleanup fora do checkout;
26. riscos residuais incluem consequência e proprietário;
27. review técnica é separada da decisão de Lucas;
28. Gate não é aprovado automaticamente;
29. 5.9 não inicia Etapa 6;
30. progresso, Gate, baseline, README e source map ficam reconciliados.

## 16. Critérios de parada e rollback

Parar a fatia corrente se:

- PII, secret, path pessoal ou conteúdo não autorizado for coletado;
- participante retirar consentimento;
- ambiente exigir código/repositório real;
- facilitador precisar explicar tarefa central;
- hash da release não conferir;
- doctor retornar `BLOCKED` sem recuperação documentada;
- surgir finding crítico/alto;
- correção exigir ampliar o escopo do Alpha;
- regressão, scanner ou orphan check falhar;
- pacote recomendar aprovação com evidência ausente.

Rollback preserva o resultado histórico anonimizado quando consentido, reverte apenas a correção defeituosa e mantém a última release auditada. Release publicada nunca é sobrescrita; uma correção material usa nova versão.

## 17. Riscos e mitigação

| Risco | Mitigação | Evidência |
|---|---|---|
| chamar preflight de avaliação externa | tipos e documentos separados | protocolo/resultados distintos |
| participante próximo demais do projeto | critérios de elegibilidade e familiaridade declarada | perfil anonimizado |
| viés do facilitador | roteiro congelado e intervenções registradas | log estruturado da sessão |
| PII entrar no Git | coleta mínima, template allowlist e scanner | revisão de privacidade |
| ambiente bloquear a sessão | preflight e checklist prévios | estado `ENVIRONMENT_BLOCKED` |
| uma pessoa virar alegação geral | linguagem limitada ao caso observado | review editorial |
| finding ser minimizado para fechar o Gate | severidade e regras de bloqueio prévias | matriz de findings |
| 5.9 virar novo produto | limite de remediação e caminhos A/B/C | decisão de escopo |
| corrigir docs depois e avaliar versão antiga | release alvo congelada e repetição afetada | hashes/protocolo |
| inventar métricas/voz do autor | fonte/natureza obrigatórias e checkpoint com Lucas | baseline/retrospectiva |
| auditor automático “aprovar” Gate | checker somente mecânico | decisão humana separada |
| live smoke gerar custo desnecessário | reutilizar evidência 5.4; nova chamada só com autorização | journal/budget |

## 18. Checkpoints humanos

O plano e as fatias 5.9.1/5.9.2 já foram aprovados; `v0.1.0a7` já foi publicada e validada. Para o fluxo acelerado restante, exigem decisão separada:

1. disponibilização do participante, confirmação de elegibilidade, consentimento e canal da sessão;
2. severidade/escopo quando a triagem exigir remediação material, chamada paga ou nova release;
3. publicação do resultado externo após anonimização, revisão de privacidade e secret scan;
4. `APPROVE`, `APPROVE_WITH_CONDITIONS` ou `REJECT/BLOCK` para o Gate 5.

Commit/push que publique o pacote final e qualquer planejamento da Etapa 6 permanecem fora do fluxo automático. O caminho A, sem alteração material, pode atravessar 5.9.4 e 5.9.5 diretamente até o pacote decisório.

## 19. Definition of Done do 5.9

O incremento só pode ser declarado concluído quando:

- as seis fatias estiverem concluídas ou o estado bloqueado/rejeitado estiver formalizado;
- a sessão externa válida existir, salvo decisão explícita de bloquear o Gate;
- findings críticos/altos estiverem encerrados para uma recomendação de aprovação;
- G5-19 possuir retrospectiva/baseline/lesson ou bloqueio claro;
- o pacote G5-01 a G5-20 passar no auditor mecânico;
- a regressão e a CI do commit auditado estiverem verdes;
- artifacts/release aplicáveis estiverem reconciliados;
- Lucas tiver emitido decisão explícita sobre o Gate 5.

Concluir o 5.9 não inicia automaticamente trabalho multilíngue. Mesmo com Gate 5 aprovado, o próximo passo permitido é somente planejar detalhadamente a Etapa 6.
