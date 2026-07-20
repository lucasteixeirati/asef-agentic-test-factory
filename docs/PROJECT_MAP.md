# Mapa do produto ASEF

Este é o ponto de entrada para localizar o que usar, estender, auditar ou estudar no ASEF. A quantidade de diretórios reflete quatro produtos relacionados, mas diferentes: runtime, prova de qualidade, documentação pública e memória da pesquisa.

## Quero usar o ASEF

O fluxo público pretendido é: descrever a necessidade em linguagem natural, fornecer apenas o contexto autorizado, selecionar ou confirmar uma skill, executar em ambiente controlado e revisar automações, evidências e limitações.

| Necessidade | Entrada principal | Skill | Perfil | Estado atual |
|---|---|---|---|---|
| teste unitário Python | requisito e SUT Python delimitado | `unit` | `python-pytest` | experimental |
| teste de API | requisito, contrato e endpoint autorizado | `backend-api` | `python-pytest` no adapter atual | parcial em loopback |
| teste de site | fluxos, URL e ambiente autorizado | `web-ui` | `node-typescript` | experimental e parcial na fixture local Chromium |
| teste de código Java | requisito e fixture Maven autorizada | `unit` | `java-junit` | experimental e parcial na fixture Calculator |

O Alpha atual não deve ser usado como aprovação de produção nem contra código arbitrariamente hostil. Um alvo publicamente acessível não implica autorização para automatizá-lo.

## Jornada cotidiana pretendida

1. o QE descreve objetivo, riscos e restrições em linguagem natural;
2. o ASEF resolve o contexto autorizado e detecta sistemas e perfis candidatos;
3. o humano confirma ambiguidades, ambiente, dados e efeitos permitidos;
4. um papel agêntico produz saída tipada dentro de uma skill versionada;
5. o runtime valida políticas, comandos, budget e artefatos;
6. adapters determinísticos executam no sandbox aplicável;
7. o ASEF normaliza resultados e preserva evidências;
8. o humano revisa conclusões, limitações e eventual exportação.

Agente propõe análise e automação; runtime controla transições, políticas, budgets e efeitos. Skill define **o que** testar; perfil define **em qual ecossistema**; adapter define **como** executar.

## Quero entender o código

| Caminho | Responsabilidade |
|---|---|
| `src/asef/application/` | casos de uso e orquestração |
| `src/asef/adapters/` | Docker, ferramentas, providers, persistência e relatórios |
| `src/asef/runtime/` | budgets e controle determinístico |
| `src/asef/skills/` | políticas executáveis das skills disponíveis |
| `src/asef/contracts.py` | contratos centrais do workflow |
| `src/asef/languages.py` | perfis de linguagem e capabilities declaradas |
| `src/asef/schemas/` | schemas públicos versionados |

## Quero estender

- `docs/skills/`: contratos das capacidades de teste;
- `docs/agents/`: papéis agênticos, autoridade e saídas tipadas;
- `docs/architecture/contracts/`: portas e contratos técnicos;
- `docs/contributing/adapter-guide.md`: criação de adapters;
- `tooling/`: imagens e toolchains controladas;
- `datasets/`: conformance, smoke, segurança e avaliação.

Uma skill documentada não está automaticamente implementada. O nível real de suporte é declarado em `docs/project/language-matrix.md` e no perfil correspondente em `src/asef/languages.py`.

## Quero auditar

- `tests/`: regressão do produto;
- `docs/project/gates/`: critérios e pacotes decisórios;
- `docs/evaluation/`: metodologia e resultados de avaliação;
- `.asef/`: runs e relatórios locais, normalmente não versionados;
- `SECURITY.md`: modelo de segurança e reporte de vulnerabilidades.

## Quero acompanhar a pesquisa

- `PLANEJAMENTO_MESTRE.md`: autoridade do roadmap;
- `journal/`: relato cronológico e decisões observadas;
- `book/`: evolução editorial;
- `concepcao/`: material de concepção;
- `spikes/`: experimentos que não representam suporte do produto.
