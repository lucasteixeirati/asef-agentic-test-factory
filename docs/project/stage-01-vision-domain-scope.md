# Pacote da Etapa 1 — Visão, domínio e escopo

## Objetivo

Transformar a intenção do Marco Zero em uma especificação compreensível por terceiros e preparar as decisões que antecedem contratos e arquitetura detalhada.

## Entregáveis

| Entregável | Arquivo | Situação |
|---|---|---|
| Visão em uma página | `product-vision.md` | Produzido no Marco Zero |
| Personas | `personas.md` | Aprovado |
| Glossário | `glossary.md` | Aprovado |
| Mapa de domínio e capacidades | `domain-capabilities.md` | Aprovado |
| Casos de uso priorizados | `use-cases.md` | Aprovado |
| Escopo e não escopo | `scope.md` | Aprovado |
| Requisitos e atributos de qualidade | `requirements-v01.md` | Aprovado |
| Matriz de linguagens | `language-matrix.md` | Aprovado |
| Primeiro workflow vertical | `first-workflow.md` | Aprovado |

## Decisões propostas

1. P1 e P2 serão as personas primárias da experiência v0.1.
2. WF-001 — Test Generation & Evaluation será o primeiro workflow.
3. Python será perfil de referência.
4. TypeScript será perfil suportado na v0.1.
5. Java será perfil experimental executável na v0.1.
6. Language profiles serão compostos por adaptadores de capacidade.
7. O SUT existente será independente da geração dos testes no workflow principal.
8. Docker Desktop/WSL2 permanecerá como ambiente de referência inicial.

## Gate 1 — Resultado

| Critério | Evidência | Situação |
|---|---|---|
| Um QE externo entenderia o projeto sem explicação verbal? | Visão, personas, glossário e escopo | Aprovado |
| O primeiro workflow resolve problema concreto de qualidade? | UC-001 e WF-001 | Aprovado |
| O primeiro incremento é pequeno sem reduzir a visão multilíngue? | Limites do alpha e matriz de linguagens | Aprovado |
| Os contratos propostos evitam acoplamento a Python? | Arquitetura de adaptadores e capabilities | Aprovado |
| Os principais termos possuem definição única? | `glossary.md` | Aprovado |

## Decisão

O responsável aprovou explicitamente o pacote e as decisões propostas em 2026-07-11. A Etapa 1 está encerrada e a Etapa 2 está autorizada.
