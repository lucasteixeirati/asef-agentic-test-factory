# Checklist do facilitador — avaliação externa do Alpha Python

- **Versão:** `1.0.0`
- **Estado atual:** `HOLD`
- **Finding bloqueador:** `PREFLIGHT-F-001`
- **Correção local:** candidata `0.1.0a7` aprovada tecnicamente, mas ainda não publicada nem reauditada como asset remoto imutável

## Antes de recrutar ou agendar

- [ ] Lucas aprovou explicitamente o protocolo.
- [ ] O preflight está `READY`, sem crítico/alto aberto.
- [ ] A release alvo possui documentação, wheel e sdist coerentes.
- [ ] O kit do participante está `READY` e contém links imutáveis.
- [ ] Nenhum contato é iniciado por Codex sem autorização/canal explícito.

Enquanto qualquer item acima estiver aberto, não distribuir kit nem convidar participante.

## Elegibilidade

- [ ] experiência prática em QE ou automação;
- [ ] uso básico de PowerShell, venv e Docker Desktop;
- [ ] externo ao ciclo de autoria 5.1–5.8;
- [ ] sem briefing funcional individual;
- [ ] familiaridade prévia declarada;
- [ ] perfil público limitado e não identificável.

## Consentimento

- [ ] objetivo, duração e natureza experimental explicados;
- [ ] dados estruturados que serão anotados explicados;
- [ ] ausência de gravação por padrão confirmada;
- [ ] direito de interromper/retirar confirmado;
- [ ] proibição de código, dados e credenciais reais confirmada;
- [ ] consentimento obtido antes de qualquer tarefa.

## Integridade técnica

- [ ] diretório vazio fora do checkout;
- [ ] `OPENAI_API_KEY` ausente;
- [ ] tag/commit/asset names congelados;
- [ ] SHA-256 do wheel confere;
- [ ] SHA-256 do sdist confere;
- [ ] imagem pytest construída somente do sdist;
- [ ] nenhuma imagem quality exigida para a demo;
- [ ] Docker sem containers ASEF gerenciados antes de começar.

## Durante a sessão

- [ ] cronômetro usado apenas como dado descritivo;
- [ ] participante recebe somente o kit liberado;
- [ ] facilitador não fornece comandos/respostas;
- [ ] intervenção possui ID, tarefa, motivo e conteúdo limitado;
- [ ] terminal não é assumido pelo facilitador;
- [ ] secret, dado real, hash divergente ou comando destrutivo interrompe a sessão;
- [ ] EXT-01 a EXT-08 recebem estado explícito.

## Antes de publicar

- [ ] resultado usa ID `PNN` e não contém nome/contato/empresa;
- [ ] paths pessoais, IP, username e terminal bruto removidos;
- [ ] consentimento continua válido;
- [ ] revisão/retirada combinada foi honrada;
- [ ] scanner de segredos passou;
- [ ] finding possui severidade, impacto, G5, estado e decisão;
- [ ] sessão `VALID` não contém intervenção central ou crítico/alto aberto;
- [ ] participante não foi avaliado ou culpabilizado.

## Encerramento técnico

- [ ] cleanup permaneceu dry-run;
- [ ] evidências sanitizadas foram preservadas conforme o protocolo;
- [ ] nenhum container gerenciado permaneceu;
- [ ] resultado foi referenciado no inventário, sem alterar a decisão humana do Gate.
