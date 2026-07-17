# Revisão técnica — fatia 5.8.3

- **Data:** 2026-07-17
- **Estado:** aprovada localmente
- **Escopo:** README, quickstart, tutorial demo/live, interpretação e troubleshooting

## Findings corrigidos

1. O README concentrava operação, live, datasets, cleanup e roadmap, dificultando a entrada de cinco minutos. Ele foi reduzido e passou a encaminhar detalhes para autoridades dedicadas.
2. A documentação podia sugerir que a release `v0.1.0a5` já continha o report 5.8. A distinção entre release publicada e linha de desenvolvimento ficou explícita.
3. O quickstart por checkout não cobria wheel, doctor anterior à run, parser público do report ou cleanup dry-run. A jornada agora cobre os quatro sem exigir provider.
4. O fluxo demo podia ser confundido com o oracle combinado 5.3. O tutorial declara que o CLI linear atual usa avaliação determinística da execução gerada e pode ter oracle `null`.
5. O exemplo live fixava modelo e podia induzir reutilização de tarifa antiga. Modelo, tarifas e câmbio passaram a ser decisões atuais do operador, com budget positivo e secret somente no host.
6. Classification, `null`, quality e evidence integrity não possuíam um guia de leitura único. A semântica pública agora está reunida sem transformar recommendation em ação.
7. Troubleshooting estava disperso. O novo guia começa por exit/classification/doctor e bloqueia ações inseguras recorrentes.

## Evidências

- README e cinco documentos dedicados presentes;
- links relativos locais resolvidos;
- paths, assets, comandos e flags confrontados com o CLI atual;
- classifications e quality statuses reconciliados com os enums públicos;
- secret scan dos seis documentos aprovado;
- 337 testes aprovados, com 33 skips opcionais;
- branch coverage geral: 85,34%;
- `git diff --check` aprovado;
- nenhum live call, custo, instalação externa ou alteração de código de produto.

## Parecer

A 5.8.3 atende seu escopo e está aprovada localmente. A jornada pública é curta na entrada e progressiva nos detalhes, distingue o que foi publicado do que está apenas no desenvolvimento e evita recomendações operacionais inseguras. A arquitetura consolidada, contribuição, adapter guide e código de conduta continuam exclusivamente na 5.8.4. Nenhum commit, push, CI, candidata ou release foi criado.
