# Estratégia de avaliação

## Princípio de independência

Gerar implementação e testes com o mesmo modelo pode comprovar consistência interna sem comprovar correção. O oracle, os testes de referência e os casos de avaliação devem ser independentes do componente avaliado sempre que possível.

## Datasets

- **Smoke:** feedback rápido e regressão básica.
- **Development:** casos visíveis usados durante a construção.
- **Evaluation:** casos separados para comparação de versões.
- **Holdout:** casos protegidos, usados somente em avaliações definidas.
- **Adversarial/Security:** abuso, políticas e falha segura.
- **Language Conformance:** invariantes contratuais entre adaptadores.

## Metadados por caso

- identificador e versão;
- origem e licença;
- autor ou processo de curadoria;
- requisito canônico;
- riscos cobertos;
- oracle e testes de referência;
- linguagens compatíveis;
- histórico de mudanças;
- exposição ou não ao desenvolvimento;
- classificação de dificuldade e tipo de evidência.

## Prevenção de circularidade e vazamento

- testes ocultos não entram no prompt de geração;
- development e evaluation datasets permanecem separados;
- holdouts possuem acesso restrito e uso registrado;
- mudanças no ground truth exigem revisão;
- LLM-as-a-judge não será a única evidência para critérios verificáveis;
- geração, execução e julgamento terão responsabilidades distinguíveis.

## Técnicas no escopo

- testes unitários, contratos e transições;
- golden tests para estruturas estáveis;
- integração com providers;
- avaliação por datasets e repetições;
- regressão de prompts e workflows;
- coverage e mutation testing;
- testes metamórficos quando houver relações válidas;
- testes adversariais;
- avaliação humana amostral.

As técnicas serão introduzidas conforme suas precondições, sem serem removidas da visão.

## Métricas candidatas

- taxa de tarefas aceitas;
- sucesso na primeira tentativa e após correção;
- cobertura de requisitos;
- testes visíveis e ocultos aprovados;
- mutation score;
- regressões;
- tentativas, duração, tokens e custo;
- violações de política e intervenções humanas;
- outputs estruturalmente inválidos;
- reprodutibilidade observada;
- falhas de infraestrutura, geração, teste e produto separadas.

Toda métrica exige definição operacional antes do uso. Resultados iniciais serão apresentados como baseline experimental, não como generalização universal.

