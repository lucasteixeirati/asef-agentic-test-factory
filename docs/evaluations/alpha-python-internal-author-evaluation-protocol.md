# Protocolo de avaliação interna acompanhada — Alpha Python

- **ID:** `ASEF-INT-ALPHA`
- **Versão:** `1.0.0`
- **Estado:** aprovado; consentimento confirmado; pronto para sessão pelo chat
- **Release congelada:** `v0.1.0a7`
- **Participante anonimizado:** `I01`, autor/mantenedor do projeto

## Natureza e limite da evidência

Esta sessão preserva as tarefas EXT-01 a EXT-08 e usa somente materiais públicos, mas não é avaliação externa nem independente. O conhecimento prévio e a participação na autoria introduzem viés incontornável. O resultado será `INFORMATIVE_INTERNAL`, poderá apoiar clareza documental e regressão da jornada, e não poderá declarar atendida a elegibilidade externa.

A ausência atual de QE externo permanece risco residual explícito. Feedback de usuários futuros será coletado como evidência posterior e não será reconstruído retroativamente.

## Consentimento e canal

Lucas confirmou em 2026-07-18 o consentimento para a avaliação e para versionar somente o resultado anonimizado. O canal é o chat de desenvolvimento: Codex entrega uma tarefa por vez; `I01` executa e relata somente observações sanitizadas. Não há gravação, terminal bruto ou PII versionados, e a retirada pode ocorrer antes da publicação.

## Escopo congelado

- tag `v0.1.0a7`, commit `79fbeb0dbbef39799801b86cebd59f8b55edaa0a`;
- wheel SHA-256 `f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad`;
- sdist SHA-256 `d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af`;
- links e cartões do kit público `1.0.0`;
- Windows, PowerShell, Python 3.13 e Docker Desktop.

## Regras do facilitador

- fornecer somente o cartão da tarefa corrente e os links públicos do kit;
- não operar o terminal nem preencher observação que não tenha sido relatada por `I01`;
- marcar qualquer orientação individual como intervenção;
- interromper diante de secret, dado real, comando destrutivo ou hash divergente;
- separar falha observada, conhecimento prévio e limitação de independência;
- não promover o resultado a avaliação externa.

## Tarefas e resultado

EXT-01 a EXT-08 mantêm instruções, estados e perguntas do protocolo externo `1.0.1`. Cada resposta registra fonte consultada, observação anonimizada, recuperação e intervenção. O arquivo de resultado só será criado após as tarefas e antes de versioná-lo passará por revisão de privacidade, secret scan e confirmação de consentimento.

## Uso no Gate 5

O resultado pode apoiar G5-18 como observação interna e G5-19 como decisão humana documentada. Uma recomendação de Gate deverá declarar que independência externa não foi observada e escolher explicitamente entre risco residual, condição de feedback posterior ou bloqueio. O checker e a IA não tomam essa decisão.
