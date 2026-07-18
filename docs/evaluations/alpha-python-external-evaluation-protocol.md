# Protocolo de avaliação externa — Alpha Python

- **ID:** `ASEF-EXT-ALPHA`
- **Versão:** `1.0.1`
- **Estado:** tecnicamente pronto; sessão externa adiada por indisponibilidade de participante
- **Release congelada:** `v0.1.0a7`
- **Responsável pelo protocolo:** Lucas
- **Instrumento:** `docs/templates/external-evaluation-observation-template.md`

## Objetivo

Observar se um QE externo ao ciclo de autoria consegue, no ambiente suportado, compreender o estado do ASEF, instalar a release, diagnosticar os requisitos, executar a demo keyless e interpretar o report usando somente documentação pública.

A sessão demonstra apenas o caso observado. Ela não é benchmark de usabilidade, avaliação de competência do participante, Developer Preview completa, certificação de segurança ou validação para produção.

## Escopo e versão congelada

A sessão obrigatória usa:

- tag `v0.1.0a7` no commit `79fbeb0dbbef39799801b86cebd59f8b55edaa0a`;
- wheel `asef_agentic_test_factory-0.1.0a7-py3-none-any.whl`, SHA-256 `f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad`;
- sdist `asef_agentic_test_factory-0.1.0a7.tar.gz`, SHA-256 `d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af`;
- README, quickstart, suporte/limitações, interpretação e troubleshooting públicos;
- Windows, PowerShell, Python 3.13 e Docker Desktop.

Wheel, sdist e documentação devem permanecer atribuíveis à mesma release. Se uma correção material alterar package ou instruções usadas, o protocolo registra nova versão/release e as tarefas afetadas são repetidas.

## Participante elegível

O participante obrigatório:

- possui experiência prática em Quality Engineering ou automação de testes;
- consegue usar PowerShell, venv e Docker Desktop em nível básico;
- não escreveu o ASEF nem decidiu os incrementos 5.1 a 5.8;
- não recebeu explicação individual do fluxo;
- aceita a publicação anonimizada do resultado estruturado.

O repositório registra somente um ID como `P01` e descrição profissional ampla. Nome, contato, empresa e localização específica não entram no Git.

## Consentimento e segurança

Antes da sessão, o facilitador informa objetivo, duração máxima, dados anotados, caráter experimental e direito de interromper ou retirar observações antes da publicação. Não haverá áudio, vídeo, gravação de tela ou terminal bruto por padrão.

O participante não usa credenciais, código proprietário, repositório real, dados pessoais ou workload hostil. `OPENAI_API_KEY` permanece ausente. O diretório da sessão é novo, descartável e fora do checkout do mantenedor.

No arquivo publicável registra-se apenas `consent_obtained: true`, data e versão do protocolo. Qualquer registro administrativo adicional permanece fora do repositório.

## Material permitido ao participante

O facilitador entrega somente:

1. página pública da release;
2. README;
3. quickstart;
4. links públicos alcançáveis a partir desses documentos.

Este protocolo, o plano do 5.9 e a rubrica não são material de execução. Se o participante já os leu, isso é declarado e a sessão pode ser informativa em vez da evidência obrigatória.

## Regras do facilitador

- resolver somente logística, consentimento e risco imediato;
- não fornecer comandos que não estejam no material permitido;
- responder perguntas funcionais com “use a documentação pública disponível”;
- registrar toda intervenção, tarefa e motivo;
- não tocar no terminal para completar uma tarefa central;
- interromper diante de secret, dado real, comando destrutivo ou hash divergente;
- não reclassificar falha do produto como erro do participante;
- não alterar protocolo/rubrica depois de observar o resultado.

Uma explicação individual sobre instalação, doctor, run ou report torna a tarefa `COMPLETED_WITH_INTERVENTION` e impede tratá-la como conclusão independente.

## Tarefas

| ID | Instrução entregue | Observação necessária |
|---|---|---|
| EXT-01 | Identifique o estado atual, requisitos e limitações antes de instalar. | fontes consultadas e conclusão sobre segurança/suporte |
| EXT-02 | Obtenha os dois assets oficiais e confira se pertencem à release indicada. | nomes, hashes e reação a divergência |
| EXT-03 | Em diretório vazio, instale o wheel e prepare somente a imagem necessária para a demo. | ausência de checkout e origem da imagem |
| EXT-04 | Diagnostique o ambiente e decida se é seguro prosseguir. | comando, status, warnings e decisão |
| EXT-05 | Execute a demo pública sem provider. | exit, stdout, run e uso de credenciais |
| EXT-06 | Localize e valide os reports produzidos. | JSON/Markdown da mesma run e método de validação |
| EXT-07 | Explique o resultado, evidências e limites. | respostas às oito perguntas de compreensão |
| EXT-08 | Planeje cleanup e encontre suporte, segurança e contribuição. | dry-run e links encontrados |

O tempo é aproximado e descritivo. Não há threshold de velocidade.

## Estados por tarefa

- `COMPLETED_INDEPENDENTLY` — documentação pública foi suficiente;
- `COMPLETED_WITH_RECOVERY` — o próprio participante encontrou e corrigiu o caminho pela documentação;
- `COMPLETED_WITH_INTERVENTION` — houve explicação individual;
- `FAILED` — a jornada pública não permitiu concluir;
- `ENVIRONMENT_BLOCKED` — precondição suportada indisponível;
- `NOT_ATTEMPTED` — sessão encerrada antes da tarefa.

## Perguntas de compreensão

1. A run terminou? Que evidência sustenta isso?
2. Qual foi a classificação funcional e o que ela permite concluir?
3. O que `ACCEPTED` não prova?
4. Quais referências de evidência estão verificadas, ausentes ou divergentes?
5. Qual conteúdo é fato e qual é inferência?
6. Existe recomendação acionável? Ela altera automaticamente o SUT?
7. Quais limitações importam antes de experimentar outro projeto?
8. Qual é a próxima ação segura para limpar ou investigar o ambiente?

O facilitador resume o sentido das respostas; transcrição extensa não é necessária.

## Rubrica congelada

Esta seção é do facilitador e não deve ser consultada pelo participante durante as tarefas.

- A release é experimental/pré-alpha, suporta o recorte Windows/Python 3.13/Docker Desktop e não promete produção ou isolamento hostil.
- Wheel e sdist devem corresponder aos hashes congelados; divergência interrompe a sessão.
- A imagem pytest é construída do sdist correspondente, não do checkout do autor. A imagem quality é opcional.
- `HEALTHY` ou `DEGRADED/READY` permitem prosseguir; `BLOCKED` exige diagnóstico antes da run.
- A demo é keyless/recorded e não comprova qualidade live geral.
- JSON é normativo; Markdown é derivado e não pode acrescentar conclusões.
- `SUCCEEDED`/`ACCEPTED` prova o caminho determinístico observado, não correção universal, produção ou certificação.
- Integridade `VERIFIED` depende de containment e SHA-256; `MISSING`/`MISMATCH` não pode ser chamada de verificada.
- Fatos possuem evidência; inferências possuem bases; recomendações não alteram o SUT automaticamente.
- Cleanup é dry-run por padrão. `docker system prune` não é alternativa autorizada.

Para a evidência obrigatória, EXT-03 a EXT-07 devem terminar `COMPLETED_INDEPENDENTLY` ou `COMPLETED_WITH_RECOVERY`, e a interpretação central deve coincidir semanticamente com a rubrica.

## Findings e severidade

Cada finding recebe ID `EXT-F-NNN`, tarefa, observação, evidência, impacto, critério G5, severidade, estado e decisão.

- `CRITICAL`: exposição, perda, execução proibida, integridade falsa ou alegação perigosa;
- `HIGH`: impede instalação/demo/interpretação central ou exige explicação individual;
- `MEDIUM`: fricção recuperável ou ambiguidade secundária;
- `LOW`: clareza editorial ou conveniência sem impacto no resultado.

Crítico/alto aberto bloqueia recomendação de aprovação do Gate. O participante não recebe severidade pessoal nem nota.

## Critério de validade

A sessão obrigatória é válida quando:

- elegibilidade e consentimento estão registrados;
- EXT-01 a EXT-07 foram tentadas;
- EXT-03 a EXT-07 foram concluídas independentemente ou com recuperação documental;
- o participante identificou corretamente `ACCEPTED`, integridade e limitações;
- nenhuma intervenção explicou tarefa central;
- nenhum finding crítico/alto permanece aberto;
- o resultado foi anonimizado, escaneado e submetido à revisão/retirada acordada.

Ausência de participante, consentimento retirado ou ambiente incompatível não será substituído por IA, mantenedor ou automação.

## Publicação e mudança do protocolo

O resultado usa o template versionado e passa por revisão de privacidade antes do Git. Correção editorial do protocolo incrementa patch; mudança de tarefa, rubrica, elegibilidade ou validade incrementa versão minor/major e invalida comparações silenciosas.

O protocolo não decide o Gate 5. Ele produz uma evidência limitada para G5-18/QA-USA-003 e para o pacote decisório final.
