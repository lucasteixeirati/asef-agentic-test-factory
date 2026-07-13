# Gate 4 — Pacote de evidências e decisão

- **Etapa:** 4 — Walking Skeleton
- **Data da auditoria:** 2026-07-13
- **Estado técnico:** pronto para decisão
- **Autoridade de aprovação:** Lucas

## Parecer

**Recomendação: aprovar com riscos residuais registrados.** Os 15 critérios obrigatórios possuem evidência proporcional ao objetivo do walking skeleton. A aprovação não deve ser interpretada como prontidão para produção, suporte multilíngue completo ou validação de segurança contra código hostil.

## Evidências consolidadas

| Critérios | Evidência principal |
|---|---|
| G4-01, G4-15 | wheel `0.1.0a1` instalado em venv novo; CLI executada em diretório vazio, sem API key; quickstart e CI correspondentes |
| G4-02, G4-03 | testes de preparação/contexto, snapshot persistido e seleção da skill `unit` |
| G4-04, G4-05 | testes de generation/workspace, hash do SUT e validação estática anterior ao Docker |
| G4-06, G4-07 | 11 integrações Docker, WS-001 real e reprodução dos fatos essenciais |
| G4-08, G4-10 | WS-002/WS-007, checkpoint SQLite opcional, resume idempotente e cancelamento 130 |
| G4-09, G4-12 | WS-003 a WS-006 e matriz pública 0, 2, 3, 4, 5, 6, 7 e 130 |
| G4-11 | contract tests para state 1.1, manifest, eventos, execução e reports |
| G4-13 | `tools/secret_scan.py` sobre arquivos públicos, wheel e artifacts; revisão de fixtures fictícias |
| G4-14 | core sem dependências runtime; LangGraph/SQLite apenas no extra opcional |

Regressão 4.R7: core com 108 testes descobertos, 89 aprovados e 19 opt-in/skip; suíte opcional 18/18; integrações Docker 11/11.

## Auditoria de instalação limpa

1. Wheel construído a partir do estado auditado.
2. Instalação com `pip install --no-deps` em ambiente virtual novo.
3. Execução fora do checkout, em diretório inicialmente vazio.
4. `OPENAI_API_KEY` removida do processo.
5. `asef prepare`, `asef generate` e `asef run` retornaram 0.
6. O run completo terminou `SUCCEEDED`/`ACCEPTED` e produziu relatório.

O wheel da 4.R7 mediu 49.478 bytes e apresentou SHA-256 `dd5b11b0df513a8475fd9c1f7312a33ffe4707a8eae579fb12b71eec6465caf0`.

## Auditoria de dados e secrets

O scanner cobre assinaturas fortes de chaves OpenAI, tokens GitHub, access keys AWS e private keys. Arquivos versionados e não ignorados, wheel e `.asef` produzida pela sessão limpa retornaram zero findings. A inspeção complementar não encontrou paths de usuário, autorização, bearer token, e-mail pessoal ou nomes de campos sensíveis nos artifacts.

Limite da evidência: pattern matching não substitui análise de entropia, scanner de histórico Git ou revisão humana de todas as formas possíveis de dado privado. Para o Gate 4, fixtures controladas e contexto fictício reduzem esse risco a um nível aceitável.

## Riscos residuais

| Risco | Consequência | Tratamento após o Gate 4 |
|---|---|---|
| Docker Desktop/daemon é parte da fronteira confiável | host comprometido ou daemon privilegiado invalida o isolamento | threat model e hardening progressivo |
| Policy AST não é uma sandbox universal | código hostil pode explorar casos não modelados | manter aviso experimental e ampliar testes adversariais |
| Demo usa cassettes estreitos e SUT sintético | não mede qualidade de LLM nem generalização | dataset de avaliação e modo live controlado nas próximas etapas |
| Apenas Python/unit é end-to-end | promessa multilíngue ainda é arquitetural | implementar perfis por capability e gates próprios |
| SQLite/checkpoint é local e opcional | concorrência e distribuição não estão provadas | avaliar somente quando houver caso real |
| Evidências vivem no filesystem local | não há assinatura, SBOM ou armazenamento imutável | adicionar proveniência e supply-chain controls antes de produção |
| Retomada não foi validada com múltiplos writers | corrida pode gerar decisões conflitantes | testes de concorrência antes de uso compartilhado |

## Decisão humana

- [x] Aprovar o Gate 4 e iniciar o planejamento detalhado da Etapa 5.
- [ ] Aprovar com condição adicional registrada abaixo.
- [ ] Rejeitar e devolver para correções.

**Decisão/condição:** aprovado por Lucas, com aceitação explícita dos riscos residuais documentados. A aprovação autoriza o planejamento detalhado da Etapa 5, não sua implementação automática.

**Data:** 2026-07-13.

## Hardening adicional solicitado antes da decisão

Em 2026-07-13, Lucas adiou a decisão e solicitou revisão de testes, logs e livro. A 4.R8 implementou:

| Condição | Evidência | Estado |
|---|---|---|
| Coverage com branches e proteção contra regressão | core 89%/threshold 85%; opcional 85%/threshold 85% | Atendida |
| Ampliação orientada a risco | 123 testes core descobertos; gateway, cassettes, store, atomicidade, eventos e logging | Atendida |
| Mutation pilot | 13/13 mutantes mortos após reforço dos asserts | Atendida |
| Logging operacional separado de evidência | `observability.md`, JSONL rotativo e testes de redaction | Atendida |
| Audit trail incremental | eventos correlacionados, deduplicação e fail-closed | Atendida |
| Saúde editorial | proveniência, source map, retrospectiva, nota e Lesson 002 | Atendida tecnicamente; voz autoral continua pendente |

### Regressão 4.R8

- core: 123 descobertos, 104 aprovados e 19 opt-in/skip;
- coverage core: 89%, threshold 85%;
- workflow opcional: 18/18 e coverage 85%, threshold 85%;
- Docker: 11/11;
- mutation: 13/13 mortos no recorte;
- wheel instalado sem dependências fora do checkout;
- demo sem API key: `SUCCEEDED`/`ACCEPTED`;
- source, wheel, logs e artifacts: secret scan sem findings;
- wheel final: 52.008 bytes, SHA-256 `395d869b08df41b747e4f24fe5fb5d2ad7a813d8eef53f9ab225229eddf5fcb6`; wheel funcional anterior reinstalado e demo repetida antes do ajuste isolado de redaction.

**Parecer atualizado:** Gate 4 aprovado por Lucas, com os riscos residuais registrados e aceitos.

**CI pública da 4.R8:** run `29253153366`, com jobs core, frameworks/opcional e Docker/security aprovados.
