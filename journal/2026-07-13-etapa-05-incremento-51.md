# Journal — Etapa 5.1: contratos e independência do oracle

- **Data:** 2026-07-13
- **Incremento:** 5.1
- **Participantes:** Lucas e GPT-5.6 Sol
- **Estado:** concluído; ADR-009 aprovada por Lucas

## Intenção

Criar fundamentos verificáveis para o Alpha Python antes de integrar `pytest` ou modo live, evitando que o tooling Python contamine o core e que o teste gerado seja usado como seu próprio oracle.

## O que foi construído

O perfil Python passou a declarar honestamente maturidade atual e alvo. Foram criados contratos para datasets, coverage e mutation sem importar as ferramentas correspondentes. Uma suíte de referência contém soma, divisão e normalização de texto, além de uma variante com defeito semeado na divisão por zero.

Quatro casos Smoke iniciais ganharam requisito, metadados e oracle. O schema impede que o oracle seja incluído nos inputs de geração. Um manifest registra hashes das fontes para tornar alterações acidentais visíveis.

## Julgamento de QA aplicado

O incremento priorizou validade da conclusão sobre quantidade de features. Um teste gerado falhar não prova defeito no produto; um teste gerado passar também não prova ausência de defeito. A ADR-009 propõe cruzar evidências independentes e manter revisão humana quando houver suspeita sobre o SUT.

Também foi evitado apresentar Python como perfil de referência já concluído. O estado publicado é experimental, e cada capability informa se está parcial ou planejada.

## Fricção

A primeira chamada de testes tentou importar arquivos por um path dentro de `tests`, que não é package. Nenhum teste do produto rodou. Discovery executou os testes novos e depois a regressão completa sem falhas. Após uma revisão adicional, o schema passou a rejeitar campos desconhecidos, versões malformadas, duplicatas e referências com marcadores sensíveis.

O resultado local final foi: 10/10 no recorte 5.1; 133 testes descobertos no core, 114 aprovados e 19 opt-in; branch coverage de 88%; 18/18 nos frameworks/workflow opcionais; e 11/11 em Docker/security.

## Material para o livro

O caso mostra duas formas de honestidade técnica: separar a evidência usada para gerar da evidência usada para avaliar e separar capacidade desejada de capacidade realmente implementada. Ambas combatem uma narrativa de maturidade produzida mais rápido do que a evidência.

## Decisão humana e próximo passo

Lucas aprovou explicitamente a ADR-009 em 2026-07-13. A decisão encerra o 5.1 e autoriza o 5.2 — adapter `pytest` e normalização — após a publicação e confirmação da CI deste incremento.

## Evidência publicada

O commit `3352dc4` foi publicado no GitHub. A execução pública `29276529459` aprovou os jobs `core`, `docker-security` e `framework-spikes`, incluindo branch coverage, secret scan, instalação do package, demo sem chave fora do checkout e workflow opcional. A condição para iniciar 5.2 foi atendida.
