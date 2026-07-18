# Skill `mutation`

- **Versão:** 1.0.0
- **Estado:** available no perfil Python delimitado; planned nos demais.
- **Propósito:** avaliar se uma suíte detecta alterações controladas no código.
- **Pré-condição:** suíte determinística executável e escopo de mutação autorizado.
- **Saídas:** mutantes mortos, sobreviventes, inválidos e timeout, com localização e operador.
- **Permissões:** escrita somente em workspace efêmero; sem alteração do SUT de origem.
- **Budget:** duração e quantidade de mutantes próprios.
- **Checkpoint humano:** ampliação do escopo ou budget.
- **Limitações:** mutation score não é prova isolada de qualidade e não altera automaticamente a aceitação funcional.

