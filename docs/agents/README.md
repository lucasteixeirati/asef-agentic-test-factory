# Papéis agênticos ASEF

Um papel agêntico é uma responsabilidade limitada com input e output tipados. Ele não é um processo autônomo com autoridade geral. O runtime decide transições, budgets, retries, rede, execução e checkpoints humanos.

## Papéis iniciais

| Papel | Responsabilidade | Saída principal |
|---|---|---|
| `requirements-analyst` | estruturar requisito, ambiguidades e riscos | análise tipada |
| `test-designer` | derivar cenários e rastreabilidade | cenários tipados |
| `automation-generator` | produzir artefato conforme skill/perfil | automação candidata |
| `execution-reviewer` | interpretar resultado normalizado sem inventar causalidade | análise de falha tipada |
| `evidence-auditor` | reconciliar fatos, inferências, evidências e limitações | findings de auditoria |

Os papéis podem compartilhar um mesmo modelo ou gateway. Separá-los documenta responsabilidade; não exige uma arquitetura multiagente nem permite que um agente delegue autoridade.

