# Journal — 2026-07-12 — Primeiros spikes arquiteturais

## Identificação

- **Dia do projeto:** Dia 2
- **Etapa:** Etapa 3 — Spikes arquiteturais
- **Situação:** concluída e aprovada

## Entregáveis

- baseline Python sem dependências;
- máquina de estados explícita;
- budgets compartilhados;
- eventos JSONL e manifests;
- gateway gravado e gateway OpenAI direto;
- DockerRunner com controles de segurança;
- três testes reais de Docker;
- spike LangGraph 1.2.9 com checkpoint;
- três relatórios de experimento.

## Resultados de teste

- compilação de `src/` e `tests/` aprovada;
- 23 testes unitários aprovados, com 8 integrações Docker ignoradas na rodada local por design;
- 10 integrações Docker reais aprovadas: 9 de segurança e 1 multilíngue;
- 5 testes LangGraph aprovados com serialização estrita;
- interrupção humana e retomada aprovadas sem nova chamada ao modelo;
- checkpoint SQLite retomado após fechamento da conexão e recriação do grafo;
- 5 testes PydanticAI aprovados offline, sem consumir créditos da API;
- demo gravada concluída em `SUCCEEDED`;
- chamada live concluída em `WAITING_FOR_CLARIFICATION`.

## Medição e uso de IA

- **Ferramenta/modelo de desenvolvimento:** GPT-5.6 Sol no ChatGPT/Codex, conforme informado pelo autor.
- **Ferramenta de concepção:** Gemini Pro, conforme informado pelo autor.
- **Tempo acumulado aproximado de colaboração com IA:** 10 horas até este registro.
- **Interações acumuladas aproximadas:** 150.
- **Precisão da medição:** estimativa retrospectiva do autor; não derivada de telemetria automática.
- **Impacto percebido na velocidade:** muito alto, ainda sem percentual defensável.

### Propostas da IA e julgamento humano

A proposta inicial explorada com IA era uma ferramenta agêntica abrangente para automatizar todo o SDLC. À medida que o autor compreendeu as implicações da proposta, combinou os insumos da IA com sua própria visão e redirecionou o projeto para Quality Engineering. A experiência profissional permitiu avaliar o que faz sentido no cotidiano de QA e relacionar a solução às tendências atuais do mercado, sem tratar a sugestão da IA como decisão automática.

### Estimativa versus andamento real

As primeiras estimativas produzidas pela IA indicavam semanas de desenvolvimento. No segundo dia, o projeto já se aproxima do encerramento experimental da Etapa 3. A diferença indica forte aceleração na concepção, documentação e construção dos spikes, mas ainda não permite concluir que toda a aplicação robusta será entregue em poucos dias: os gates posteriores incluem walking skeleton, alphas multilíngues, avaliação, segurança, experiência externa e hardening.

### Fricções da colaboração

- dúvidas sobre tokens, reasoning, limites de uso e janela de contexto exigiram uma pausa para esclarecimento com a própria IA;
- a velocidade de produção aumenta a necessidade de revisão humana para evitar confundir volume de artefatos com maturidade;
- o estado do projeto precisa permanecer registrado no repositório para não depender exclusivamente do contexto do chat.

## Previsões versus resultados — parcial

| Previsão ou expectativa | Resultado observado até agora | Situação |
|---|---|---|
| O desenvolvimento levaria semanas para alcançar os primeiros resultados técnicos | Baseline, contratos e spikes relevantes foram produzidos nos dois primeiros dias | Aceleração confirmada no recorte inicial |
| LangGraph deveria justificar-se por checkpoint, retomada e human-in-the-loop | Checkpoint em memória, interrupção, retomada e persistência SQLite foram aprovados | Hipótese tecnicamente favorecida, adoção ainda não decidida |
| Structured output do provider eliminaria parte da fragilidade da saída do modelo | A validação local continuou necessária para tipos, chaves e falhas de schema | Expectativa corrigida |
| Docker Desktop forneceria a fronteira inicial de isolamento | Controles básicos passaram, mas ACLs do Windows e um alerta de rede produziram fricção | Parcialmente confirmado |

## Reflexões provisórias para o livro

- A IA ampliou drasticamente a velocidade percebida, mas o papel do engenheiro de qualidade continuou sendo definir relevância, riscos, evidências e critérios de aprovação.
- Conhecimento de QA foi usado não apenas para testar o produto, mas para testar as próprias propostas da IA.
- O redirecionamento de uma fábrica genérica do SDLC para uma fábrica de testes mostra que compreender uma sugestão pode levar a restringi-la, e não necessariamente a aceitá-la integralmente.
- A conclusão rápida de documentos e spikes não deve ser narrada como conclusão rápida do produto; maturidade depende dos gates ainda não executados.
- O livro deve distinguir produtividade percebida, produtividade medida e qualidade efetivamente demonstrada.

## Custos

- ChatGPT Plus: R$ 100,00 já registrado;
- créditos OpenAI API: R$ 10,00 adicionados;
- custo direto acumulado informado: R$ 110,00;
- consumo live observado: 124 tokens de entrada e 161 de saída;
- nenhuma conversão monetária por run implementada.

## Falhas e aprendizados

1. O budget do gateway e o estado usavam objetos de consumo diferentes; um teste detectou manifest incorreto. O controller passou a ser compartilhado pelo runtime.
2. Diretórios temporários do Windows falharam no mount do Docker Desktop; workspaces dentro de `.asef` funcionaram.
3. Estado LangGraph com dataclass customizada gerou aviso de serialização futura; o estado foi normalizado para tipos primitivos e aprovado em modo estrito.
4. A API key tinha uma aspa inicial inválida; a falha 401 foi diagnosticada sem revelar o valor.
5. `WAITING_FOR_CLARIFICATION` precisa de código de saída próprio, não ser tratado genericamente como falha pela CLI.
6. Structured output do provider não elimina validação local; chaves e tipos passaram a ser verificados independentemente.
7. O pacote de checkpoint SQLite é distribuído separadamente do LangGraph; a versão 3.1.0 foi isolada nos requisitos do spike.
8. A retomada durável preservou o ponto de execução e evitou repetir consumo de LLM, evidência favorável ao LangGraph.
9. O metapacote PydanticAI aumentou o ambiente dos spikes de 35 para 120 pacotes. A recomendação inicial foi usar a variante slim; o responsável decidiu manter o pacote completo para possibilidades futuras, com ativação controlada por contexto e política.
10. PydanticAI reduziu o adaptador tipado, mas o runtime ASEF continuou responsável por workflow, budget e evidências.
11. Duas suposições iniciais da IA falharam no primeiro teste: `result.usage` era propriedade e o runner exigia o controller compartilhado. Os erros foram corrigidos a partir da execução.
12. `pydantic_graph` emitiu um aviso de depreciação sobre event loop no Python 3.13, mantido como risco de compatibilidade.
13. A recuperação de schema foi colocada no runtime, com prompts limitados e contadores separados para chamadas e retries.
14. Uma revisão após os primeiros testes identificou que erros estruturais poderiam surgir dentro do gateway; foi criado um erro comum para evitar políticas divergentes.
15. Saídas inválidas repetidas agora terminam em `BUDGET_EXHAUSTED` com estado e manifest, não em loop ou exceção perdida.
16. Timeout do cliente Docker poderia deixar container órfão; o runner passou a nomear e remover forçadamente o container, e o teste confirmou ausência residual.
17. A existência do diretório não bastava para autorizar mount; foi adicionada raiz permitida com resolução de `..` e symlinks.
18. Memória, PIDs, timeout, parent traversal e symlink escape foram aprovados em integrações reais.
19. O warning `DOCKER_INSECURE_NO_IPTABLES_RAW` foi confirmado e classificado como risco residual incompatível com alegação de produção.
20. A matriz favoreceu LangGraph condicional, gateway direto, Docker experimental e JSONL; PydanticAI completo permaneceu disponível fora do caminho padrão e OpenTelemetry foi adiado.
21. O responsável ampliou a visão de contexto: perfil do QA, equipe, sistemas, repositórios, skills, MCPs e LLM policy passaram a compor um contrato validável.
22. Python, Node e Java iniciaram sob a mesma política por imagens fixadas em digest; isso prova o executor, não suporte end-to-end.
23. O Docker adicionou cerca de 302 ms de overhead mediano no comando mínimo observado, 8,61 vezes o processo local devido ao workload quase vazio.
24. Truncamento real de stdout/stderr e OOM com exit 137 foram confirmados.
25. O repositório foi publicado em `lucasteixeirati/asef-agentic-test-factory` e a primeira execução da CI passou.
26. O responsável aprovou ADR-004, ADR-005, ADR-006 e o Gate 3, autorizando o walking skeleton.

## Próximos passos

- iniciar a Etapa 4 — Walking skeleton;
- criar plano executável do incremento e primeiro journal da etapa.
