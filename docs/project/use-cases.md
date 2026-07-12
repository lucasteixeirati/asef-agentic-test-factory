# Casos de uso e priorização

## Método de priorização

Os casos são classificados por valor educacional, alinhamento com Quality Engineering, capacidade de gerar evidências, risco técnico e dependências.

| Prioridade | Significado |
|---|---|
| P0 | Necessário para o primeiro workflow e os alphas |
| P1 | Necessário para a v0.1 robusta |
| P2 | Evolução posterior à v0.1 |
| P3 | Pesquisa futura, sem compromisso |

## Casos priorizados

| ID | Caso de uso | Prioridade | Persona principal | Resultado |
|---|---|---:|---|---|
| UC-001 | Gerar testes para uma função existente a partir de requisito e SUT | P0 | P1/P2 | Testes, execução e relatório |
| UC-002 | Executar uma demo sem credencial | P0 | P1 | Run reproduzida e explicada |
| UC-003 | Classificar falhas de teste, SUT, política ou infraestrutura | P0 | P2 | Evidência e próxima ação |
| UC-004 | Corrigir um teste gerado dentro de budget | P0 | P2 | Nova tentativa rastreada |
| UC-005 | Produzir manifest e trilha de eventos | P0 | P2/P3 | Run auditável |
| UC-006 | Executar o mesmo contrato em Python e TypeScript | P1 | P2/P4 | Conformidade multilíngue |
| UC-007 | Avaliar testes com coverage e mutation testing | P1 | P2/P3 | Evidência de efetividade |
| UC-008 | Criar novo perfil ou adaptador de capacidade | P1 | P4 | Extensão validada |
| UC-009 | Comparar modelo, prompt ou framework | P1 | P2/P3 | Experimento reproduzível |
| UC-010 | Revisar e aprovar exportação de artefatos | P1 | P1/P3 | Decisão humana registrada |
| UC-011 | Gerar testes para API | P2 | P1/P2 | Suite e relatório de API |
| UC-012 | Trabalhar sobre repositório real | P2 | P2 | Patch controlado e evidências |
| UC-013 | Integrar workflow em CI | P2 | P2/P4 | Execução automatizada |
| UC-014 | Usar MCP para integração externa | P2 | P4 | Interoperabilidade demonstrada |
| UC-015 | Memória entre execuções | P3 | P2/P3 | Experimento de benefício e risco |

## Seleção do primeiro workflow

O UC-001 foi selecionado porque atravessa requisitos, risco, design, geração, execução, avaliação, correção e relatório sem exigir um repositório complexo. Ele permite validar o runtime e a arquitetura de evidências antes de ampliar o contexto.

UC-002 a UC-005 fazem parte do suporte necessário ao primeiro workflow. UC-006 e UC-007 comprovam a visão multilíngue e o diferencial de QE antes da v0.1.

## Casos explicitamente fora do primeiro ciclo

- geração completa de aplicações;
- alteração autônoma de repositório real;
- deploy ou release automático;
- múltiplos agentes livres negociando sem workflow explícito;
- memória de longo prazo sem hipótese mensurável;
- integrações corporativas antes do core.

