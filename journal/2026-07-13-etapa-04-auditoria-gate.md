# Journal — auditoria final da Etapa 4

- **Data:** 2026-07-13
- **Etapa:** 4.R7
- **Participantes:** Lucas e GPT-5.6 Sol

## Intenção

Validar se o walking skeleton estava realmente pronto para outro engenheiro de qualidade instalar e estudar, sem confiar apenas nos testes executados dentro do repositório.

## O que aconteceu

A primeira inspeção encontrou uma discrepância entre a promessa pública e a implementação: os defaults da CLI apontavam para `examples/context` e `tests/fixtures`. O código passava no checkout, mas o wheel instalado não possuía uma demo autônoma. A IA propôs materializar recursos públicos do próprio package em `.asef/demo/v1`; a correção foi aceita por estar alinhada ao objetivo open source e ganhou teste fora da árvore do projeto.

Depois da correção, um wheel foi construído e instalado sem dependências em um ambiente virtual novo. Em uma pasta vazia e com `OPENAI_API_KEY` removida, `prepare`, `generate` e `run` passaram. O último executou quatro testes no Docker e terminou `SUCCEEDED`/`ACCEPTED`.

## Evidências e velocidade

- 4.R7 começou e terminou em 2026-07-13: 1 dia corrido;
- wheel final auditado: 49.478 bytes;
- três comandos públicos aprovados com exit 0;
- três escopos de secret scan aprovados: source, wheel e artifacts;
- um finding de portabilidade detectado e corrigido antes do gate;
- nenhum custo adicional informado; o demo não consumiu créditos de API.

## Reflexão de QA

O teste mais valioso deste incremento não aumentou a quantidade de funcionalidades. Ele mudou o ponto de observação: de “funciona na máquina do autor” para “funciona como artefato entregue”. Essa diferença é típica de Quality Engineering e mostrou por que critérios de aceite precisam ser validados no contexto real de distribuição.

Também ficou evidente que um gate técnico não deve se autoaprovar. A automação comprova critérios; a decisão sobre riscos residuais continua humana.

## Material para o livro

Este episódio é um bom exemplo de como a IA pode acelerar implementação e documentação, mas também reproduzir uma premissa falsa por várias iterações quando todos os testes compartilham o mesmo ambiente. A mudança de perspectiva do QA — instalar o wheel fora do checkout — revelou a lacuna.

## Próxima decisão

Lucas deve revisar o pacote de evidências, aceitar ou rejeitar os riscos residuais e decidir explicitamente o Gate 4. A Etapa 5 não começa apenas porque a suíte está verde.
