# Plano detalhado da Etapa 7 — Developer Preview

**Status:** aprovado por Lucas em 20/07/2026; 7.1 executada localmente e pronta para
checkpoint de commit, sem push, tag ou release.

**Data do planejamento:** 20/07/2026

**Gate de entrada:** Gate 6 aprovado em 20/07/2026.

**Gate de saída:** Gate 7 — evidência humana externa controlada.

## 1. Objetivo

Validar, com 3–5 engenheiros de qualidade externos ao ciclo de autoria, se a versão
experimental do ASEF pode ser descoberta, instalada, executada, interpretada e
estendida usando somente materiais públicos. A Etapa 7 deve substituir suposições do
autor por observações rastreáveis antes do hardening da v0.1.

O Developer Preview é um estudo formativo de uma amostra pequena. Não é benchmark
estatístico, pesquisa de mercado, certificação de segurança, aprovação para produção
ou demonstração de compatibilidade geral.

## 2. Hipóteses a testar

| ID | Hipótese | Evidência mínima |
|---|---|---|
| DP-H01 | um QE elegível entende propósito, maturidade e limites sem explicação individual | tarefa de descoberta e resumo sem intervenção central |
| DP-H02 | a instalação limpa e o diagnóstico são executáveis no ambiente declarado | instalação a partir de artifacts congelados e `doctor` interpretado corretamente |
| DP-H03 | a demo keyless produz evidência localizável e verificável | run concluída, JSON/Markdown reconciliados e integridade explicada |
| DP-H04 | API, Web UI e Java são compreendidos como recortes experimentais, não suporte geral | cada trilha observada ao menos uma vez no conjunto válido |
| DP-H05 | ao menos um QE consegue modificar um exemplo ou iniciar uma extensão pela documentação | tentativa observada, mesmo que produza finding ou não seja concluída |
| DP-H06 | segurança, autoridade de agentes/skills e cleanup são compreendidos | participante evita live/alvo real, identifica checkpoints e planeja cleanup seguro |
| DP-H07 | a documentação permite recuperação sem assistência privada | recuperação autônoma registrada separadamente de intervenção do facilitador |

Hipótese não confirmada gera finding ou lacuna; não será convertida em sucesso por
interpretação benevolente, assistência da IA ou conhecimento prévio do autor.

## 3. Escopo

### Incluído

- candidata alpha imutável contendo o fechamento da Etapa 6;
- Windows 11 x86-64, PowerShell, Python 3.13 e Docker Desktop como ambiente válido
  inicial;
- descoberta pública, instalação limpa, `doctor`, demo recorded/keyless, reports e
  cleanup dry-run;
- trilhas locais e fictícias de `backend-api`, `web-ui` e `java-junit`;
- tentativa delimitada de modificar exemplo ou criar esqueleto de extensão;
- consentimento, observação estruturada, privacidade, triagem e síntese anonimizada;
- correções necessárias para remover findings da própria jornada preview.

### Excluído

- provider live, chave real, custo pago ou envio de contexto a terceiros;
- sites, APIs, repositórios, dados ou código reais dos participantes;
- produção, pentest, carga hostil, scraping, pagamento, autenticação ou bypass;
- promessa de suporte geral a TypeScript, Java, Kotlin, `.bat`, Gradle ou projetos
  externos;
- telemetry automática, gravação de tela/áudio/vídeo ou coleta de terminal bruto;
- divulgação ampla, campanha comunitária ou validação longitudinal, reservadas à
  Etapa 9;
- início do hardening da Etapa 8 antes da decisão do Gate 7.

## 4. Restrições herdadas

- os Gates 5 e 6 mantêm o produto experimental e não aprovado para produção;
- avaliação interna `I01` é informativa e não conta como participante externo;
- o protocolo `ASEF-EXT-ALPHA 1.0.1` e a release `v0.1.0a7` são fontes históricas
  reutilizáveis, mas não provam a experiência multilíngue da Etapa 6;
- o corpus final deve ter entre 3 e 5 sessões válidas; sessão inválida, retirada ou
  bloqueada pelo ambiente permanece registrada, mas não conta para o mínimo;
- nenhuma pessoa será contatada, convidada ou agendada sem autorização específica de
  Lucas e consentimento anterior às tarefas;
- antes do recrutamento, Lucas executa as jornadas publicadas e registra um checkpoint
  de prontidão do autor; nesse checkpoint decide se `.bat` e Kotlin podem permanecer
  como lacunas de uma preview ou se são pré-requisitos a implementar primeiro;
- publicação, tag/release, correção remota e distribuição do kit exigem checkpoints
  separados; aprovar este plano não autoriza essas ações;
- não há prazo para recrutar participantes ou fechar a lacuna externa.

## 5. Unidade de avaliação e participantes

### Elegibilidade

Cada participante válido:

- possui experiência prática em Quality Engineering ou automação de testes;
- consegue operar PowerShell, ambiente virtual e Docker Desktop em nível básico;
- não escreveu o ASEF nem participou das decisões das Etapas 5–7;
- não recebeu walkthrough funcional privado antes da sessão;
- usa ambiente compatível e aceita a publicação de resultado anonimizado.

Amigos e contatos profissionais do autor podem participar se atenderem aos mesmos
critérios. A amostra por conveniência e seus vieses devem ser declarados; ela não
representa a população de QEs.

### Identidade e privacidade

- IDs públicos: `P01` a `P05`;
- registrar apenas papel amplo, faixa de experiência e familiaridade declarada;
- nome, contato, empresa, hostname, username, IP, paths pessoais e material bruto não
  entram no Git;
- nenhum áudio, vídeo ou screen recording por padrão;
- retirada é permitida até o checkpoint combinado antes da publicação;
- IA pode ajudar a estruturar material sanitizado, mas não observar sozinha, inventar
  respostas, completar tarefas ou substituir consentimento humano.

## 6. Jornada comum e trilhas

### Núcleo obrigatório para cada sessão válida

| ID | Tarefa | Resultado observado |
|---|---|---|
| DP-01 | descobrir propósito, maturidade, ambiente e proibições | fontes e interpretação inicial |
| DP-02 | obter artifacts congelados e verificar identidade/hashes | integridade e reação a divergência |
| DP-03 | instalar em diretório novo, sem checkout do mantenedor | instalação e fricções reais |
| DP-04 | executar `doctor` e decidir se deve prosseguir | status, warnings e decisão segura |
| DP-05 | executar demo recorded/keyless | run, terminal e ausência de credencial |
| DP-06 | localizar, verificar e interpretar reports | fatos, inferências, classificação e limites |
| DP-07 | localizar suporte, segurança e contribuição | capacidade de autoatendimento |
| DP-08 | planejar cleanup seguro | dry-run e ausência de comando destrutivo |

### Trilhas especializadas distribuídas no conjunto

| ID | Trilha | Obrigação do conjunto válido |
|---|---|---|
| DP-T1 | backend API contra fixture loopback autorizada | observada ao menos uma vez |
| DP-T2 | Web UI TypeScript/Playwright contra fixture empacotada | observada ao menos uma vez |
| DP-T3 | Java/JUnit contra fixture Calculator | observada ao menos uma vez |
| DP-T4 | modificar exemplo ou iniciar extensão documentada | tentativa real por ao menos um participante |

Com três participantes, cada trilha funcional recebe ao menos uma sessão; DP-T4 pode
ser combinada com uma delas. Com quatro ou cinco, as repetições priorizam a trilha de
maior risco observada nas primeiras sessões. A alocação é registrada antes de cada
sessão para evitar seleção posterior de resultados favoráveis.

## 7. Papel do facilitador

O facilitador pode resolver consentimento, logística e risco imediato. Não pode
fornecer comandos ausentes do material público, explicar a interpretação central,
assumir o terminal ou corrigir silenciosamente o ambiente.

Estados por tarefa:

- `COMPLETED_INDEPENDENTLY`;
- `COMPLETED_WITH_RECOVERY` pela documentação pública;
- `COMPLETED_WITH_INTERVENTION`;
- `FAILED`;
- `ENVIRONMENT_BLOCKED`;
- `NOT_ATTEMPTED`;
- `WITHDRAWN`.

Toda intervenção recebe ID, tarefa, motivo e impacto. Uma intervenção que explique
instalação, execução ou interpretação central invalida essa evidência de independência.

## 8. Fatias executáveis

### 7.0 — reconciliação e aprovação do plano

**Entregas:** este plano, plano de aceite do Gate 7, Planejamento Mestre, governança e
estratégia open source reconciliados.

**Aceite:** escopo, autoridade, critérios de validade e checkpoints são revisados por
Lucas; nenhuma implementação, publicação ou abordagem externa é iniciada.

### 7.1 — baseline e candidata do Developer Preview

**Progresso em 20/07/2026:** delta desde a7 inventariado, identidade `0.1.0a8`
reconciliada, artifacts construídos e escaneados, wheel final instalado fora do
checkout e jornadas demo/API/Web/Java aprovadas. Regressão, Docker, Smoke, Security e
docs passaram. A candidata está `READY_FOR_COMMIT_CHECKPOINT`; os artifacts continuam
locais e mutáveis até um commit e uma reconstrução posterior.

**Entregas planejadas:** inventário das mudanças desde `v0.1.0a7`; decisão de versão
da candidata (esperada `0.1.0a8`, sem antecipar tag); release state coerente; build de
wheel/sdist; auditoria instalada fora do checkout; regressões core, Docker, Smoke,
Security, conformance e documentação.

**Aceite:** artifacts locais representam integralmente API, Web UI e Java aprovados
no Gate 6; hashes, metadata e documentação concordam; nenhum crítico/alto permanece.

**Checkpoint:** Lucas decide separadamente se autoriza commit/push da candidata e,
depois, tag/pré-release. Artifact mutável não pode ser distribuído a participante.

### 7.2 — protocolo, instrumentos e ética

**Entregas planejadas:** protocolo `ASEF-DEVPREVIEW-01`, kit do participante,
checklist do facilitador, template de observação, formulário de consentimento
administrativo não versionado e schema/inventário de resultados.

**Aceite:** núcleo DP-01–DP-08, trilhas, rubrica, validade, severidade, privacidade,
retirada, intervenções e tratamento de material bruto estão congelados antes da
primeira observação.

### 7.3 — ensaio interno e preflight

**Entregas planejadas:** ensaio frio instalado, executado por Lucas sem contar para o
corpus; preflight de cada trilha; auditoria do kit; secret scan; threat review do
processo de coleta; correção dos findings do ensaio; checkpoint de prontidão do autor
sobre testes próprios e lacunas `.bat`/Kotlin.

**Aceite:** todas as tarefas são tecnicamente executáveis a partir do kit; o ensaio
não preenche respostas de participantes; nenhum crítico/alto aberto; resultado
`READY_FOR_IMMUTABLE_CANDIDATE`.

**Checkpoint:** sem a confirmação de Lucas de que testou suficientemente a candidata,
a 7.4 e o recrutamento permanecem em espera. Se `.bat` ou Kotlin forem declarados
pré-requisitos, a execução da Etapa 7 pausa para planejamento próprio dessas lacunas.

### 7.4 — candidata remota imutável

**Entregas planejadas:** tag/pré-release autorizada, artifacts e hashes publicados,
CI verde e postflight rebaixando novamente os assets do remoto em ambiente limpo.

**Aceite:** código, docs, wheel, sdist e links do kit apontam para a mesma identidade;
postflight completo; nenhuma mutação da release durante o corpus.

**Checkpoint:** tag, release e publicação só ocorrem após autorização explícita.

### 7.5 — recrutamento e sessões

**Entregas planejadas:** matriz de elegibilidade anonimizada, autorização de contato,
consentimentos, 3–5 resultados válidos e registros de sessões inválidas/retiradas sem
PII.

**Aceite:** cada sessão segue o protocolo congelado; todas executam o núcleo; o
conjunto cobre DP-T1–DP-T4; nenhuma IA ou facilitador substitui observação humana.

**Checkpoint:** Lucas fornece ou autoriza canal e destinatários antes de qualquer
contato, e o checkpoint de prontidão da 7.3 deve estar aprovado. Codex não envia
convites autonomamente.

### 7.6 — triagem, correções e repetição controlada

**Entregas planejadas:** backlog `DP-F-NNN`, severidade/recorrência, decisão,
correções e matriz de tarefas afetadas.

**Aceite:** crítico/alto é corrigido e repetido ou bloqueia o Gate; risco médio só
pode ser aceito com justificativa; correção material cria nova candidata e repete as
tarefas afetadas, sem misturar silenciosamente releases no mesmo agregado.

### 7.7 — síntese e memória do projeto

**Entregas planejadas:** relatório agregado anonimizado, limites da amostra, mapa de
hipóteses, decisões de produto, retrospectiva, journal e notas do livro sobre
diferenças entre intenção e experiência.

**Aceite:** contagens brutas substituem percentuais enganosos; casos negativos e
intervenções permanecem visíveis; participação da IA na preparação/análise é
declarada; nenhuma voz ou conclusão de participante é fabricada.

### 7.8 — pacote e decisão do Gate 7

**Entregas planejadas:** inventário mecânico, pacote de evidências, auditoria de
privacidade, regressão final, lista de riscos residuais e formulário de decisão.

**Aceite:** critérios do Gate 7 são avaliados por evidência; decisão humana é
`APPROVE`, `APPROVE_WITH_CONDITIONS` ou `REJECT/BLOCK`; aprovação autoriza somente o
planejamento detalhado da Etapa 8.

## 9. Severidade e regras de parada

| Severidade | Exemplo | Tratamento |
|---|---|---|
| `CRITICAL` | secret/PII publicado, efeito destrutivo, integridade falsamente aprovada | interromper sessão e etapa; remediar antes de continuar |
| `HIGH` | instalação/demo/trilha central impossível ou interpretação perigosa sem ajuda | bloquear Gate; corrigir e repetir evidência afetada |
| `MEDIUM` | recuperação possível, ambiguidade secundária ou fricção recorrente | corrigir ou aceitar risco explicitamente antes do Gate |
| `LOW` | conveniência ou redação sem alterar decisão segura | priorizar no backlog rastreável |

Também interrompem a sessão: credencial, dado/código real, hash divergente, comando
destrutivo, retirada de consentimento, alvo externo ou ambiente fora da política.

## 10. Métricas e interpretação

Registrar por tarefa e sessão:

- estado, duração aproximada e fonte pública consultada;
- recuperação, intervenção e motivo;
- finding, severidade, recorrência e decisão;
- entendimento de maturidade, terminal, classificação, integridade, fatos/inferências,
  autoridade, limitações e cleanup;
- ambiente em categorias amplas e trilha atribuída.

Relatar contagens como `3 de 4`, nunca transformar a amostra em alegação populacional.
Tempo é diagnóstico, não threshold. Satisfação subjetiva complementa, mas não
substitui conclusão de tarefa e evidência observável.

## 11. Critérios de conclusão da Etapa 7

- 3–5 sessões externas válidas sobre candidata(s) rastreáveis;
- núcleo DP-01–DP-08 observado em todas as sessões válidas;
- DP-T1, DP-T2 e DP-T3 observadas ao menos uma vez no conjunto;
- DP-T4 tentada por ao menos um participante;
- interpretação central correta sem explicação individual nas sessões que compõem a
  evidência final;
- nenhum finding crítico/alto aberto;
- findings médios possuem correção ou risco aceito com justificativa;
- resultados e síntese são anonimizados, consentidos e passam no secret scan;
- regressão técnica, documentação e package audit permanecem verdes;
- pacote do Gate 7 recebe decisão humana explícita.

## 12. Riscos do plano

| Risco | Mitigação |
|---|---|
| disponibilidade limitada de QEs | sem prazo artificial; sessões sequenciais e lacuna visível |
| viés por amizade/conveniência | elegibilidade uniforme, ausência de briefing e limitação publicada |
| versão mudar durante as sessões | release imutável; nova coorte/tarefas repetidas após correção material |
| facilitador ensinar o fluxo | material congelado e intervenção estruturada |
| vazamento de PII/secret | coleta mínima, sem gravação, sanitização, revisão e scanner |
| sobreafirmação por amostra pequena | contagens brutas, casos negativos e limites explícitos |
| ambiente impedir sessão | preflight, estado `ENVIRONMENT_BLOCKED` e não contagem silenciosa |
| trilhas demorarem demais | núcleo comum, alocação prévia e timebox de segurança sem critério de velocidade |

## 13. Autorizações separadas

A aprovação deste planejamento autoriza somente iniciar a fatia 7.1 local. Não
autoriza push, tag, release, provider live, alvo externo, contato com participantes,
agendamento, publicação de resultado ou início da Etapa 8.
