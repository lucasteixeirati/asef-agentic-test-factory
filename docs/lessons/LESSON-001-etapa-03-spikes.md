# Lição aprendida — Etapa 3: spikes arquiteturais

- **Data:** 2026-07-12
- **Etapa:** Etapa 3
- **Estado:** retrospectiva técnica pronta; decisão do gate pendente

## O que esperávamos

- Python explícito seria mais simples;
- LangGraph precisaria provar checkpoint e retomada;
- PydanticAI reduziria parsing e validação;
- Docker bloquearia rede, escrita e excesso de recursos;
- structured output ainda exigiria defesa local.

## O que aconteceu

- LangGraph provou interrupção e retomada durável, mas adicionou dependências;
- PydanticAI reduziu o adapter, porém o metapacote trouxe integrações excessivas;
- a recuperação de schema precisou cobrir erros no runtime e dentro do gateway;
- timeout Docker exigiu limpeza explícita para evitar container órfão;
- validação de raiz autorizada foi necessária para impedir mounts arbitrários;
- 8 cenários Docker reais passaram no ambiente de referência.

## Papel da IA

- gerou implementações iniciais, testes, comparações e documentação;
- fez suposições incorretas sobre uma API e sobre compartilhamento de budget, detectadas pelos testes;
- acelerou ciclos de hipótese, implementação e revisão;
- não substituiu a decisão humana sobre escopo, risco residual ou stack mínima.

## Julgamento de QA

- flags de segurança não foram aceitas como evidência sem testes reais;
- caminhos de correção e timeout foram testados como produtos, não como exceções secundárias;
- resultados negativos e warnings foram preservados;
- tecnologias modernas foram comparadas pelo valor demonstrado, não pela popularidade.

## O que faremos diferente

- instalar variantes slim desde o início dos próximos spikes;
- definir previamente a autoridade de budgets compartilhados;
- testar cleanup e recuperação junto do caminho feliz;
- separar claramente “aprovado para experimento” de “seguro para produção”;
- manter notas contemporâneas para o livro durante a implementação.
