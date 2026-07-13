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
| Licença ChatGPT Plus | R$ 100,00 | 1 mês a partir do início informado | Custo fixo inicial do projeto |
| Créditos OpenAI API | R$ 10,00 | Adicionados em 2026-07-12 | Budget máximo informado para testes live |
| Valor-hora de trabalho | Não aplicável | — | Não será contabilizado como custo financeiro |
| Outros custos | R$ 0,00 | Baseline inicial | Registrar somente se ocorrerem |

O custo de R$ 100,00 não será dividido artificialmente entre entregáveis. Durante o mês de validade, ele será referenciado como custo fixo vigente. Com os R$ 10,00 de créditos da API, o custo direto acumulado informado é R$ 110,00. Novos custos só serão adicionados quando efetivamente informados ou comprovados.

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

Os números não serão convertidos artificialmente em percentual de produtividade. As próximas comparações usarão dias por entregável, retrabalho, critérios de gate e evidências de qualidade.

## Baseline do Marco Zero

| Entregável | Categoria | Início | Conclusão | Dias | Estado |
|---|---|---|---|---:|---|
| Concepção e planejamento consolidado | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Revisão e modularização documental | Governança | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote documental do Marco Zero | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote da Etapa 1 — visão, domínio e escopo | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Pacote da Etapa 2 — contratos, workflow e avaliação | Documentação | 2026-07-11 | 2026-07-11 | 1 | Concluído |
| Etapa 3 — spikes arquiteturais | Implementação/experimento | 2026-07-12 | 2026-07-12 | 1 | Concluído |
| Etapa 4 — walking skeleton e Gate 4 técnico | Implementação/documentação | 2026-07-12 | 2026-07-13 | 2 | Concluído tecnicamente; decisão pendente |

Esta baseline é retrospectiva e cobre apenas os registros disponíveis. A medição prospectiva começa após sua criação.
