# Relato — planejamento do incremento 5.8

- **Data:** 2026-07-16
- **Estado:** plano detalhado produzido; implementação pendente de aprovação
- **Dependência:** incremento 5.7 publicado em `v0.1.0a5`

Lucas autorizou o planejamento detalhado do 5.8, sem autorizar implementação. A auditoria encontrou um report de run construído diretamente pelo `JsonRunStore`, sem contrato próprio e sem separação tipada entre fatos, inferências, recomendações e limitações. Também encontrou caminhos terminais anteriores ao workspace sem garantia uniforme de report, documentação pública concentrada no README e ausência de guias dedicados para quickstart, demo, live, interpretação, troubleshooting, suporte e contribuição de adapters.

O plano divide o trabalho em seis fatias: contrato/schema; builder e terminais; jornada pública; arquitetura/contribuição; experiência instalada/CI; e revisão/candidata. A proposta adiciona um sétimo job `public-experience`, inteiramente keyless, para validar wheel em diretório vazio, quickstart, report e documentação.

O 5.8 não inclui participante externo real, Developer Preview, retrospectiva final, Gate 5, linguagem adicional ou Etapa 6. A candidata esperada é `0.1.0a6`, condicionada a revisão e decisão humana posterior.
