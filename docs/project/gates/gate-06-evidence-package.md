# Pacote de evidências — Gate 6

**Data da candidata:** 19/07/2026  
**Decisão:** aprovado por Lucas em 20/07/2026 (`aprovo gate 6`).

## Resultado técnico

| Critério | Evidência | Parecer técnico |
|---|---|---|
| jornada auditável | capability runs API/Web/Java, planos por hash e tutoriais | atendido |
| backend API fictícia | 6.3 cassette/live opt-in, OpenAPI fechado e conformance | atendido |
| Web UI TypeScript | Chromium isolado, 18/18 conformance e wheel instalado | atendido |
| unit multilíngue | Python referência, TypeScript/Node TAP e Java/Surefire sobre intenção aritmética comum | atendido no recorte |
| core neutro | adapters específicos e testes de fronteira sem imports de tooling no core | atendido |
| autoridade limitada | structured output, policies, budgets e checkpoint antes de execução | atendido |
| quality útil | coverage/mutation Python, ausência explícita nos demais e relações metamórficas justificadas | atendido no recorte |
| datasets estratificados | Smoke, Security, conformance API/Web/Java e metamórfico separados | atendido |
| condições Gate 5 | avaliação externa e jornada humana isolada continuam abertas sem prazo | condição preservada |

## Baseline local da candidata

- 495 testes, 41 skips condicionais e cobertura global 85%;
- Smoke `smoke-20260720T141205Z-ee591469`: 20/20, hash `c3783476…019d`;
- Security `security-20260720T141227Z-6878314a`: 12/12, hash `e3865388…1818`;
- Java Docker 3/3; Web UI Docker 3/3; TypeScript unit 1/1; quality Docker 3/3;
- wheel instalado fora do checkout para Web UI e Java;
- docs 167 arquivos/128 links e secret scan sem findings na candidata técnica;
- nenhum provider live, alvo externo, push, tag ou release.

Após o registro da aprovação, a regressão de fechamento passou com 496 testes, 41
skips condicionais e cobertura global de 85%; o checker aprovou 169 arquivos e 128
links, e o secret scan permaneceu sem findings.

## Limites da decisão

Esta aprovação promove `node-typescript` e `java-junit` a experimentais somente nas
capabilities comprovadas. O Gate não prova compatibilidade geral com projetos, produção, sites externos,
Gradle, Kotlin, `.bat`, Spring, autenticação, múltiplos browsers ou segurança contra
código arbitrariamente hostil. Avaliação externa permanece lacuna deliberada.
