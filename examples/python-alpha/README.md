# Suíte de referência do Alpha Python

Esta suíte contém SUTs pequenos, existentes e deliberadamente simples para avaliar o WF-001 sem gerar implementação e testes a partir da mesma interpretação.

- `reference_sut/`: comportamento curado esperado;
- `defective_sut/`: variante controlada com defeito semeado;
- `datasets/smoke/`: requisitos e oracles ficam fora desta árvore e não entram no prompt por padrão.

Os dois projetos usam somente a biblioteca padrão. A variante defeituosa é evidência de avaliação e nunca deve ser corrigida automaticamente pelo workflow.
