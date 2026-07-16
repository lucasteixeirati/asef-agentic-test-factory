# Baseline de medição da construção

## Objetivo

Registrar a velocidade de criação dos módulos e demais entregáveis em dias, além dos custos financeiros diretos informados, sem inventar valor-hora ou granularidade que não será acompanhada.

## Unidade de tempo

- A unidade oficial inicial será **dia corrido**.
- Cada módulo ou entregável terá data de início e conclusão.
- Um item iniciado e concluído na mesma data será registrado como **1 dia**.
- Itens em paralelo manterão suas próprias datas; seus dias não serão somados como se fossem trabalho sequencial.
- Horas poderão aparecer apenas como observação opcional, sem obrigação de coleta.

## Registro por entregável

| Campo | Descrição |
|---|---|
| Identificador | Nome único do módulo ou entregável |
| Categoria | Aplicação, documentação, experimento, livro ou governança |
| Data de início | Primeiro dia com trabalho registrado |
| Data de conclusão | Dia em que o critério de conclusão foi atendido |
| Dias corridos | Contagem inclusiva entre início e conclusão |
| Estado | Planejado, em andamento, concluído ou bloqueado |
| Retrabalho | Sim/não e motivo resumido |
| Evidência | Arquivo, release, experimento ou decisão relacionada |

## Baseline financeira inicial

| Item | Valor | Validade/período | Observação |
|---|---:|---|---|
| ChatGPT Plus | R$ 0,00 efetivamente desembolsado no primeiro mês; preço nominal de R$ 100,00/mês | Primeiro mês promocional gratuito | O preço nominal não é contabilizado como gasto enquanto não houver cobrança |
| Créditos OpenAI API | R$ 10,00 adquiridos | Adicionados em 2026-07-12 | Saldo pré-pago; consumo live observado até o Dia 5 foi de aproximadamente R$ 0,01533 |
| Valor-hora de trabalho | Não aplicável | — | Não será contabilizado como custo financeiro |
| Outros custos | R$ 0,00 | Baseline inicial | Registrar somente se ocorrerem |

O preço nominal do ChatGPT Plus não será tratado como desembolso no primeiro mês porque Lucas informou ter recebido esse período gratuitamente. O custo direto efetivamente informado até o início do Dia 6 é de R$ 10,00 em créditos pré-pagos da API; o único smoke medido consumiu aproximadamente R$ 0,01533 desse saldo. Aquisição de crédito e consumo efetivo permanecem métricas distintas. Novos custos só serão adicionados quando informados ou comprovados.

## Indicadores iniciais

- dias por módulo;
- dias por entregável documental;
- dias por milestone;
- quantidade de entregáveis concluídos por milestone;
- entregáveis com retrabalho;
- decisões revistas após crítica humana ou de outra IA;
- custo direto acumulado do projeto.

## Baseline inicial de colaboração com IA

| Indicador | Valor informado | Natureza |
|---|---:|---|
| Tempo acumulado de uso até o Dia 2 | aproximadamente 10 horas | Estimativa retrospectiva do autor |
| Interações acumuladas até o Dia 2 | aproximadamente 150 | Estimativa retrospectiva do autor |
| Impacto percebido na velocidade | muito alto | Percepção qualitativa; sem percentual calculado |
| Estimativa inicial da IA | semanas de desenvolvimento | Estimativa original ainda sem decomposição comparável |
| Andamento observado | Etapa 3 em andamento no Dia 2 | Fato documental; não equivale à conclusão do produto |

### Atualização no Dia 3

| Indicador | Valor informado | Natureza |
|---|---:|---|
| Interações acumuladas estimadas | aproximadamente 300 | Derivação da média informada de cerca de 100 interações por dia em três dias; não é telemetria |
| Horas acumuladas | não atualizadas | Permanecem conhecidas apenas as aproximadamente 10 horas relatadas até o Dia 2 |
| Velocidade percebida | alta | Percepção do autor após o walking skeleton |
| Desgaste percebido | não significativo | O autor relata progresso sólido, verificações e clareza de objetivo |
| Confiança | crescente a cada etapa concluída com qualidade | Percepção qualitativa do autor |

Os números não serão convertidos artificialmente em percentual de produtividade. As próximas comparações usarão dias por entregável, retrabalho, critérios de gate e evidências de qualidade.

### Atualização no início do Dia 6

Lucas declarou 2026-07-15 como início formal do Dia 6 de desenvolvimento. As estimativas abaixo são derivadas de sua percepção média, não de telemetria ou cronômetro:

| Indicador | Valor informado/derivado | Natureza |
|---|---:|---|
| Dedicação média | aproximadamente 6 horas por dia | Estimativa do autor |
| Horas acumuladas até o fim do Dia 5 | aproximadamente 30 horas | Derivação de cinco dias pela média informada |
| Interações médias | aproximadamente 100 por dia | Percepção do autor mantida após o Dia 3 |
| Interações acumuladas até o fim do Dia 5 | aproximadamente 500 | Derivação, não telemetria |
| Produtividade percebida nos Dias 4 e 5 | alta | A ideia evoluiu da concepção à medida que o autor compreendeu e aprofundou o sistema |
| Confiança | alta | Associada à revisão e validação antes de avançar etapas |
| Desgaste | cansaço ao final do dia | Trabalho percebido como intelectualmente exigente e multidisciplinar |
| Papel atual do autor | acompanhamento, leitura, compreensão e validação | O código é produzido com assistência da IA; a decisão de avanço permanece humana |

Na percepção de Lucas, as interações recentes exigiram mais aprimoramentos do que correções diretas. A postura de revisão antes de cada etapa, porém, continua encontrando ajustes técnicos. O tempo entre interações aumentou porque ele lê e procura compreender o que foi construído e por quê; portanto, menor frequência momentânea não deve ser confundida com menor contribuição humana.

### Ferramentas por período

| Período | Ferramentas/modelos informados | Uso dominante |
|---|---|---|
| Concepção | GPT Free e Gemini Pro | Exploração inicial, comparação e formação da ideia |
| Desenvolvimento | GPT-5.6 Sol na IDE Visual Studio Code | Análise, implementação, testes, documentação e revisão assistida |
| Primeiro smoke live do produto | OpenAI API, modelo retornado `gpt-5.4-2026-03-05` | Validação controlada do adapter live com budget explícito |

## Baseline do Marco Zero

| Entregável | Categoria | Início | Conclusão | Dias | Estado |
|---|---|---|---|---:|---|
| Concepção e planejamento consolidado | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Revisão e modularização documental | Governança | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote documental do Marco Zero | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote da Etapa 1 — visão, domínio e escopo | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote da Etapa 2 — contratos, workflow e avaliação | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Etapa 3 — spikes arquiteturais | Implementação/experimento | 2026-07-12 | 2026-07-12 | 1 | Concluído |
| Etapa 4 — walking skeleton, hardening e Gate 4 | Implementação/documentação | 2026-07-12 | 2026-07-13 | 2 | Concluído e aprovado |
| Etapa 5.1 — contratos e referência Python | Implementação/documentação | 2026-07-13 | 2026-07-13 | 1 | Concluído e publicado |
| Etapa 5.2 — adapter pytest em Docker | Implementação/integração | 2026-07-13 | 2026-07-13 | 1 | Concluído e publicado |
| Etapa 5.3 — oracle e correção limitada | Implementação/revisão | 2026-07-14 | 2026-07-14 | 1 | Concluído com retrabalho de sete findings; publicado em `v0.1.0a2` |
| Etapa 5.4 — adapter live e budgets | Implementação/revisão | 2026-07-14 | 2026-07-15 | 2 | Concluído com hardening de contexto e budget; publicado em `v0.1.0a3` |
| Etapa 5.5 — Smoke Dataset | Implementação/CI | 2026-07-15 | 2026-07-15 | 1 | Concluído e publicado; Smoke 20/20 no job `alpha-smoke` |
| Etapa 5.6 — coverage e mutation do SUT | Implementação/CI | 2026-07-15 | 2026-07-15 | 1 | Concluído e publicado em `v0.1.0a4`; cinco jobs verdes |
| Etapa 5.7 — segurança, doctor e retenção | Implementação/revisão | 2026-07-15 | 2026-07-16 | 2+ | Concluído e publicado em `v0.1.0a5`; seis jobs verdes |

Esta baseline é retrospectiva e cobre apenas os registros disponíveis. A medição prospectiva começa após sua criação.
