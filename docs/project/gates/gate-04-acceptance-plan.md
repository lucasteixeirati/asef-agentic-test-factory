# Gate 4 — Plano de aceite do Walking Skeleton

- **Estado:** aprovado por Lucas em 2026-07-13
- **Responsável pela decisão:** Lucas

## Critérios obrigatórios

| ID | Critério | Evidência esperada | Estado |
|---|---|---|---|
| G4-01 | Clone limpo executa modo demo documentado | CI + sessão de instalação | Atendido |
| G4-02 | QualityContext é validado antes de LLM/Docker | testes WS-003 + eventos | Atendido |
| G4-03 | Skill `unit` é selecionada por sistema/capability | snapshot + contract test | Atendido |
| G4-04 | Teste real é gerado apenas no workspace efêmero | artifact + hash + path test | Atendido |
| G4-05 | Validação determinística precede execução | static result + sequência de eventos | Atendido |
| G4-06 | Docker executa sem rede, secrets ou escrita no original | integration tests + manifest | Atendido |
| G4-07 | Run de sucesso é reproduzível | WS-001 repetido com mesmos fatos essenciais | Atendido |
| G4-08 | Espera humana persiste e retoma sem repetir nós concluídos | WS-002 + checkpoint | Atendido |
| G4-09 | Falhas de input, policy, budget e infraestrutura são distintas | WS-003 a WS-006 | Atendido |
| G4-10 | Cancelamento encerra de forma explicável | WS-007 | Atendido |
| G4-11 | Eventos, state, manifest, contexto e reports são consistentes | schema/contract tests | Atendido |
| G4-12 | Exit codes e stdout/stderr seguem o contrato público | CLI end-to-end | Atendido |
| G4-13 | Nenhum secret ou dado privado aparece nos artifacts | secret scan + fixtures públicas | Atendido |
| G4-14 | Core não depende diretamente de OpenAI, LangGraph ou Docker | dependency/import test ou revisão | Atendido |
| G4-15 | Quickstart descreve limitações e funciona sem API key | README + execução CI | Atendido |

## Critérios informativos

- duração por etapa e run;
- overhead Docker observado no fluxo real;
- tamanho dos artifacts;
- chamadas/tokens gravados;
- retrabalho e falhas introduzidas pela IA;
- diferença entre previsão e duração real.

## Não exigido para aprovação

- modo live;
- pytest, coverage ou mutation;
- MCP real;
- mais de uma skill;
- TypeScript ou Java end-to-end;
- interface gráfica;
- suporte de produção.

## Regra de decisão

Todos os critérios obrigatórios precisam estar atendidos ou possuir risco explicitamente aceito que não invalide o objetivo do walking skeleton. O responsável aprova o gate; CI verde sozinha não constitui aprovação.

O detalhamento técnico, os riscos residuais e a recomendação estão no [pacote de evidências do Gate 4](gate-04-evidence-package.md). O estado `Atendido` representa comprovação técnica, não aprovação automática do gate.

Após a regressão adicional 4.R8, Lucas aprovou explicitamente o gate e aceitou os riscos residuais documentados. O próximo passo autorizado é o planejamento detalhado da Etapa 5.
