# Matriz inicial de linguagens e toolchains

## Decisão proposta para o Gate 1

| Ecossistema | Nível pretendido na v0.1 | Papel arquitetural |
|---|---|---|
| Python | Referência | Primeiro workflow completo e baseline |
| TypeScript/Node.js | Suportado | Provar independência do core e tooling web |
| Java | Experimental | Provar composição com build corporativo complexo |
| Go | Planejado | Candidato de simplicidade e binários compilados |
| .NET | Planejado | Candidato corporativo e multiplataforma |

## Toolchains candidatos

| Capacidade | Python | TypeScript | Java |
|---|---|---|---|
| Project detection | `pyproject.toml` | `package.json` | `pom.xml` inicialmente |
| Dependências | uv/pip a experimentar | npm/pnpm a experimentar | Maven inicialmente |
| Build/validation | compile/import checks | TypeScript compiler | Maven compiler |
| Test runner | pytest | Vitest inicialmente | JUnit 5 |
| Static analysis | Ruff | ESLint | Checkstyle/SpotBugs a avaliar |
| Coverage | coverage.py | V8/Istanbul | JaCoCo |
| Mutation | mutmut ou Cosmic Ray | StrykerJS | PIT |
| Resultado normalizado | contrato ASEF | contrato ASEF | contrato ASEF |
| Container | imagem Python fixada | imagem Node fixada | imagem JDK/Maven fixada |

As ferramentas são candidatas, não decisões arquiteturais definitivas. Cada seleção dependerá de spike, licença, automação, formato de saída, estabilidade e custo de manutenção.

## Critérios de seleção

- relevância para a comunidade de qualidade;
- diversidade suficiente para testar a arquitetura;
- execução não interativa;
- resultados estruturados ou normalizáveis;
- imagem de container reproduzível;
- licença compatível;
- comunidade e manutenção ativas;
- integração viável com coverage e mutação;
- complexidade sustentável para um mantenedor inicial.

## Capabilities por nível

| Capacidade | Referência | Suportado | Experimental |
|---|---:|---:|---:|
| Descoberta | Obrigatória | Obrigatória | Obrigatória |
| Build/validação | Obrigatória | Obrigatória | Obrigatória |
| Test runner | Obrigatória | Obrigatória | Obrigatória |
| Normalização | Obrigatória | Obrigatória | Obrigatória |
| Coverage | Obrigatória | Obrigatória | Desejável |
| Mutation | Obrigatória | Obrigatória | Desejável |
| Tutorial | Completo | Completo | Básico |
| Conformance suite | Completa | Completa | Subconjunto publicado |

## Ambiente

O ambiente de referência será Windows com Docker Desktop/WSL2. Cada perfil executará o SUT em imagem fixada e não deverá depender de a linguagem estar instalada diretamente no host, além dos componentes necessários à própria CLI.

## Baseline comprovada na Etapa 3

| Perfil | Estado atual | Evidência |
|---|---|---|
| Python 3.13 | Executor por digest aprovado | EXP-006 |
| Node 22 / TypeScript futuro | Inicialização por digest aprovada | EXP-006 |
| Java 21 | Inicialização por digest aprovada | EXP-006 |

“Inicialização aprovada” não equivale a suporte. Detecção de projeto, instalação, build, test runner, coverage, mutation e normalização ainda exigem conformance por ecossistema.

## Questões para os spikes

- uv ou pip oferece a melhor baseline reprodutível para Python?
- Vitest ou Jest reduz complexidade sem perder representatividade?
- Maven é suficiente para o primeiro perfil Java ou Gradle precisa estar no alpha?
- quais ferramentas oferecem relatórios estruturados mais estáveis?
- quais mutation engines funcionam adequadamente em containers e CI?
