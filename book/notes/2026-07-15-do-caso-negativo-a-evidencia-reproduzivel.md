# Do caso negativo à evidência reproduzível

O incremento 5.5 tornou concreta uma distinção importante: sucesso da suíte não significa que todas as runs terminam em sucesso funcional. Um requisito ambíguo deve esperar; um SUT defeituoso deve pedir revisão; um budget esgotado deve parar; uma operação proibida deve ser bloqueada. Quando esses fatos coincidem com expectativas curadas, o comportamento do sistema está correto.

Essa separação exigiu dois níveis de contrato. `case.json` descreve a intenção semântica e protege o oracle; `demo.json` descreve a fixture determinística, os contadores e o terminal esperado. O runner compara fatos estáveis e exclui identidade operacional do fingerprint. Assim, repetir não significa reproduzir timestamps e IDs, mas reproduzir decisões observáveis.

A primeira execução Docker mostrou outro aspecto da engenharia assistida por IA: uma arquitetura correta ainda encontra limites concretos do ambiente. Dois nomes temporários seguros, quando aninhados em um workspace já longo, ultrapassaram o limite de path do Windows. A evidência permitiu localizar a falha, encurtar apenas nomes internos e preservar as garantias públicas. A revisão também ampliou o hash para todo o `read_scope`, porque reprodutibilidade depende de tudo que realmente influencia a execução.

O resultado local foi 20/20 em duas repetições, mas a interpretação permanece deliberadamente modesta. Dez casos curados oferecem uma regressão explicável; não formam benchmark, não estimam desempenho universal de modelos e não substituem avaliação estatística. A força da evidência vem da clareza de seu escopo.
