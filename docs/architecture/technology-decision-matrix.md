# Matriz de decisão tecnológica — Gate 3

- **Data:** 2026-07-12
- **Status:** aprovada pelo responsável no Gate 3
- **Escala:** 1 (fraco) a 5 (forte)
- **Regra:** pontuação orienta a decisão, mas riscos bloqueadores e lacunas de evidência prevalecem.

## Engine de workflow

| Critério | Peso | Python explícito | LangGraph |
|---|---:|---:|---:|
| Controle determinístico | 25 | 5 | 4 |
| Persistência e retomada | 20 | 2 | 5 |
| Auditabilidade | 15 | 4 | 5 |
| Baixa complexidade/dependências | 15 | 5 | 3 |
| Testabilidade | 15 | 5 | 4 |
| Valor educacional | 10 | 4 | 5 |
| **Total ponderado / 500** | **100** | **415** | **430** |

**Recomendação:** adotar LangGraph condicionalmente no walking skeleton para grafo, checkpoint e interrupção. A semântica dos estados, budgets, políticas e evidências continua pertencendo ao ASEF. A baseline Python permanece como oracle de simplicidade e conformance.

## Adapter de provider

| Critério | Peso | HTTP direto | PydanticAI completo |
|---|---:|---:|---:|
| Controle explícito | 20 | 5 | 4 |
| Structured output | 20 | 3 | 5 |
| Baixa dependência | 15 | 5 | 2 |
| Testabilidade | 15 | 4 | 5 |
| Evidência live no projeto | 15 | 5 | 2 |
| Portabilidade entre providers | 10 | 2 | 5 |
| Estabilidade observada | 5 | 4 | 3 |
| **Total ponderado / 500** | **100** | **410** | **380** |

**Recomendação ajustada pelo responsável:** usar o gateway direto no caminho principal do walking skeleton e manter PydanticAI completo instalado no ambiente experimental para cenários futuros. Componentes do pacote somente serão ativados por skill, contexto e política explícitos; ele não controlará o workflow.

## Observabilidade

| Opção | Decisão proposta | Evidência |
|---|---|---|
| JSONL + state + manifest | Adotar no walking skeleton | Reproduzível e aprovado nos testes |
| OpenTelemetry | Adiar | Nenhum deploy centralizado ou benefício demonstrado na CLI local |

## Isolamento

| Opção | Decisão proposta | Evidência |
|---|---|---|
| Docker Desktop/WSL2 | Adotar para desenvolvimento experimental | 8/8 testes reais; risco residual do daemon documentado |
| `subprocess` local | Usar apenas como baseline funcional confiável | Não é fronteira de segurança |
| Bloqueio de imports | Não tratar como sandbox | Controle contornável dentro do processo |

## Stack mínima proposta para a Etapa 4

- Python 3.13;
- contratos e políticas ASEF;
- LangGraph 1.2.9 com checkpoint SQLite, sob controle do runtime ASEF;
- gateway OpenAI Responses direto;
- Docker Desktop/WSL2 para execução isolada experimental;
- JSONL, state JSON e manifest JSON;
- `unittest` para a baseline atual;
- modo demo por cassette, com live bloqueado sem budget explícito.

## Tecnologias adiadas ou rejeitadas

- PydanticAI completo: disponível no ambiente experimental, não ativado no caminho padrão;
- OpenTelemetry: adiado;
- Pydantic Graph como engine: não avaliado e fora do escopo;
- sandbox por subprocess/import blacklist: rejeitada como fronteira de segurança.
