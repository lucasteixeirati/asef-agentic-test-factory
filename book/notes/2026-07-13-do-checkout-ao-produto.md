# Nota contemporânea — Do checkout ao produto

- **Data:** 2026-07-13
- **Origem:** auditoria 4.R7 e hardening 4.R8
- **Proveniência:** evidência verificável estruturada por GPT-5.6 Sol
- **Estado:** rascunho assistido; percepção do autor pendente

## A suíte estava verde

O walking skeleton possuía testes unitários, contratos, integrações Docker e uma demonstração funcional. Ainda assim, a primeira instalação real do wheel mostrou que a CLI procurava contexto e cassettes nas pastas de exemplos e testes do próprio repositório.

Os testes não estavam errados; o ambiente de observação era estreito. Todos executavam dentro do checkout e compartilhavam uma premissa invisível. Quando a perspectiva mudou para a de outro engenheiro instalando o artefato, a promessa pública falhou.

## Uma mudança de ponto de observação

A correção transformou o demo em recurso materializado pelo package e criou uma prova fora da árvore do Git. Essa história conecta uma prática conhecida de Quality Engineering — testar o produto no contexto de entrega — a um projeto acelerado por IA.

Na 4.R8, o mesmo princípio foi aplicado à suíte: contar testes deu lugar a medir branches, procurar módulos frágeis e introduzir mutation testing em um recorte controlado. A pergunta deixou de ser “quantos testes passaram?” e passou a ser “quais erros relevantes ainda sobreviveriam?”.

## Hipótese editorial

IA pode acelerar a construção de caminhos coerentes dentro das premissas fornecidas. O QA agrega valor ao variar ambiente, perspectiva, oracle e hipótese. A velocidade da implementação aumenta a importância dessa mudança deliberada de ponto de observação.

## Voz do autor a incorporar

- O finding do wheel surpreendeu você ou confirmou uma suspeita?
- Depois desse episódio, o que passou a significar “pronto” neste projeto?
- A velocidade da IA aumentou ou diminuiu sua necessidade de desconfiança profissional?
