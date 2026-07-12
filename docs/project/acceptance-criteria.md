# Critérios de aceite por maturidade

## Walking skeleton — Gate 4 futuro

- input validado por schema;
- run identificada;
- uma chamada gravada ou live produz structured output;
- artifact gerado apenas em workspace temporário;
- uma validação determinística executada;
- eventos JSONL e manifest mínimo produzidos;
- relatório de sucesso ou falha produzido;
- cancelamento e ao menos um budget demonstrados;
- nenhuma dependência do core em pytest além do adapter.
- QualityContext validado e snapshot sanitizado;
- skill `unit` selecionada por capability;
- espera humana retomada sem repetir nós concluídos;
- exit codes distinguem input, espera, falha, policy, budget e infraestrutura;
- critérios detalhados em `docs/project/gates/gate-04-acceptance-plan.md`.

## Alpha Python — Gate 5 futuro

- WF-001 completo com função Python existente;
- pytest executado em Docker Desktop/WSL2;
- análise, riscos, cenários e testes rastreáveis;
- correção limitada a arquivos de teste;
- classificação de `TEST_ERROR`, `SUT_DEFECT_SUSPECTED`, `POLICY_VIOLATION` e `INFRASTRUCTURE_ERROR` demonstrada;
- Smoke Dataset aprovado;
- Security Dataset crítico aprovado;
- coverage e mutation result normalizados;
- modo demo sem rede e modo live configurável;
- manifest e relatório completos;
- instalação limpa no ambiente de referência.

## Alpha multilíngue — Gate 6 futuro

- Python referência e TypeScript suportado end-to-end;
- Java experimental executável;
- Language Conformance Dataset aprovado conforme o nível;
- nenhuma regra de domínio alterada apenas para adicionar TypeScript;
- capabilities e ausências publicadas;
- coverage e mutation testing operacionais nos perfis suportados;
- testes metamórficos aplicados onde houver relação válida;
- Eval Dataset estratificado e relatório de limitações.

## Developer preview — Gate 7 futuro

- 3–5 engenheiros de qualidade participaram;
- instalação e primeira run observadas;
- compreensão do relatório avaliada;
- findings registrados por severidade;
- críticos e altos resolvidos ou transformados em bloqueio;
- ao menos uma tentativa externa de usar ou modificar exemplo/adapter;
- feedback e dados publicados de forma anonimizada.

## v0.1 — Gate 8 futuro

Além da matriz obrigatória do Planejamento Mestre:

- todos os MUST de `requirements-v01.md` rastreados para evidência;
- nenhum finding crítico aberto;
- findings altos possuem resolução ou risco explicitamente aceito pelo responsável, sem invalidar critério obrigatório;
- imagens fixadas por digest;
- política de segurança e limitações publicadas;
- datasets públicos possuem origem e licença;
- modo demo funciona sem credenciais;
- modo live exige budget explícito;
- release reproduzível em ambiente limpo;
- documentação de uso e contribuição revisada.

## Gate 2 — Critérios desta etapa

- topologia completa do WF-001;
- transições, retries, interrupções e terminais definidos;
- schemas conceituais de input, estado, execução, avaliação e relatório;
- contratos de skills e adapters independentes de frameworks;
- sandbox e budgets baseline especificados;
- Smoke, Evaluation, Holdout, Security e Conformance Datasets estruturados;
- ADRs de fronteiras, adapters e independência do oracle aceitos;
- critérios de aceite dos alphas e v0.1 documentados;
- nenhuma decisão de implementação da Etapa 3 antecipada como fato.
