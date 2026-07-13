# Journal — 4.R8: hardening antes do Gate 4

- **Data:** 2026-07-13
- **Etapa:** 4.R8
- **Participantes:** Lucas e GPT-5.6 Sol
- **Estado:** implementação, regressão local e CI pública concluídas

## Decisão humana

Lucas decidiu não aprovar imediatamente o Gate 4. Pediu três revisões: testes e possibilidade de ampliar cobertura, existência de logs na aplicação e estado das anotações do livro.

## Revisão inicial

A suíte possuía 108 testes, mas coverage ainda não era medida na CI. A primeira medição encontrou 80% geral e 85% no recorte canônico. A aplicação possuía state, manifest, events, stdout/stderr e reports, mas não logging operacional. O livro possuía cerca de seis mil palavras entre journals e notas, porém sem mapa de fontes, retrospectiva da Etapa 4 ou proveniência editorial formal.

## Qualidade

Coverage com branches passou a integrar a CI. Testes de gateway live usam transporte simulado e não consomem API. Cassettes inválidos, store corrompido, paths maliciosos, atomicidade, append-only e redaction ganharam cenários próprios. Após as alterações, o core canônico atingiu 89% e o workflow opcional 85%.

### Mutation pilot

Mutmut 3.6.0 exige `fork`; por isso foi executado em Linux, dentro de container descartável e com o workspace original read-only. Duas tentativas de coleta revelaram dependências auxiliares ausentes no isolamento: `asef.legacy` e a fixture `examples/state`.

Na primeira execução completa, 5 de 13 mutantes sobreviveram. Quatro alteravam os atributos/mensagem de `BudgetExceeded`; um enfraquecia a combinação de sucesso em `exit_code_for`. Depois de ampliar os asserts, 13 de 13 foram mortos.

## Observabilidade

O runtime passou a distinguir audit trail e logging operacional. Eventos novos carregam identidade, correlação, timestamp e tempo desde o evento anterior. Saves repetidos não duplicam o stream; corrupção não é sobrescrita. JSONs usam atomic replace. O log operacional usa JSONL, níveis, rotação, campos controlados e redaction, sem poluir stdout.

Uma regressão Windows revelou que handlers abertos impediam a remoção de diretórios temporários. A CLI passou a fechar handlers antes de retornar, transformando um detalhe de teste em requisito de portabilidade.

## Livro

Foram criados mapa de fontes, política de proveniência, retrospectiva assistida, nota sobre checkout versus produto e Lesson 002. Percepções que somente Lucas pode fornecer continuam marcadas como pendentes, em vez de serem inferidas pela IA.

## Falha de ambiente registrada

Uma execução de coverage falhou porque o comando global foi iniciado sem `PYTHONPATH=src`. A CI instalará o package em modo editável. O comando foi repetido no ambiente correto e passou; a diferença reforça a necessidade de manter comandos locais equivalentes aos jobs públicos.

## Custos e velocidade

- nenhum uso de API e nenhum novo custo financeiro informado;
- 4.R8 iniciada e implementada no mesmo dia corrido;
- mutation completo levou cerca de 70 segundos após o harness estar correto;
- o valor principal veio dos cinco mutantes sobreviventes e das duas falhas do isolamento, não do score isolado.

## Próximo passo

Docker passou em 11/11. Após a aprovação, o wheel do marco final mediu 52.014 bytes, SHA-256 `41ab457797d0f2232ed434e6442a8e55c86773fdd7d22c5d82671dbded84fd60`; a versão funcional equivalente foi instalada em venv novo fora do checkout. A demo sem API key terminou `SUCCEEDED`/`ACCEPTED`, e source, wheel, logs e artifacts passaram no secret scan.

O commit `d0d7c32` foi publicado. A CI pública `29253153366` aprovou core, frameworks/workflow opcional e Docker/security. O Gate 4 pode ser reapresentado a Lucas, sem inferir aprovação automática.

## Aprovação humana do Gate 4

Lucas aprovou explicitamente o Gate 4 em 2026-07-13 e aceitou os riscos residuais documentados. A decisão encerra a Etapa 4 e autoriza o planejamento detalhado da Etapa 5. A implementação do Alpha Python não foi iniciada automaticamente.
