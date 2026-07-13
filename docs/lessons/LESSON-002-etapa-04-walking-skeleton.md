# Lição aprendida — Etapa 4: o ambiente de entrega também é requisito

- **Data:** 2026-07-13
- **Estado:** evidência técnica consolidada; revisão autoral pendente

## O que esperávamos

Um walking skeleton instalável, keyless, auditável e isolado, com critérios objetivos suficientes para decidir o Gate 4.

## O que aconteceu

O workflow funcional e as suítes passaram dentro do repositório. A auditoria do wheel revelou que os defaults públicos dependiam de arquivos que não acompanhavam a instalação. Depois da correção, o package passou a materializar sua própria demo e a CI ganhou execução fora do checkout.

Uma revisão adicional encontrou 80% de branch coverage geral e 85% no recorte principal, além de ausência de logging operacional. A Etapa 4 foi estendida para medir cobertura, testar branches frágeis e separar audit trail de logs.

## Papel da IA

- implementou rapidamente caminhos e documentação coerentes com o ambiente conhecido;
- ajudou a construir a auditoria que revelou a própria premissa incompleta;
- estruturou testes, observabilidade e matéria-prima editorial;
- não aprovou o gate nem definiu sozinha o nível de risco aceitável.

## Julgamento de QA

O finding mais valioso veio de mudar contexto e oracle, não de repetir o mesmo teste. Um artefato open source precisa ser exercitado como entrega instalada. Evidência de execução e log operacional resolvem problemas diferentes. Coverage é baseline estrutural; mutation ajuda a investigar a força dos asserts.

## O que faremos diferente

- testar o artefato distribuído desde o primeiro incremento executável;
- colocar coverage com branches na CI antes de declarar uma suíte madura;
- separar audit trail, logs operacionais e relatórios desde o contrato inicial;
- criar retrospectiva e mapa de fontes ao fechar cada milestone;
- capturar a voz do autor antes que a memória seja substituída pela narrativa dos commits.
