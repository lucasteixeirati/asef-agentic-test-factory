# Revisão técnica — fatia 5.8.6

- **Data:** 2026-07-17
- **Estado:** candidata aprovada tecnicamente e nos sete jobs públicos; publicação depende de decisão humana
- **Escopo:** versão candidata, walkthrough frio, regressões, package/scanner e fechamento documental

## Findings corrigidos

1. CLI e builder possuíam fallbacks de versão separados. Ambos foram promovidos para `0.1.0a6` e um teste passou a reconciliá-los com `pyproject.toml`.
2. O auditor verificava identidade/shape do schema, mas não executava um validator Draft 2020-12 completo. `jsonschema==4.25.1` passou a ser dependência exclusiva de teste/auditoria e valida uma instância real.
3. O job instalado precisava manter o wheel sem dependências e ainda executar schema validation. A instalação do validator foi separada e ocorre somente depois do `pip install --no-deps`.
4. A jornada final ainda não tinha walkthrough frio roteirizado. A sessão em diretório vazio percorreu os oito passos sem findings novos.

## Evidências locais

- metadata, CLI e report builder: `0.1.0a6`;
- walkthrough frio: doctor `DEGRADED/READY`, demo `SUCCEEDED/ACCEPTED`, cleanup `DRY_RUN_COMPLETE` e auditor 9/9;
- Smoke: 20/20, hash `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`;
- Security: 12/12, hash `e386538869acc970a86d935b7068c794e5522b884caf327a953b3b4434b1818b`;
- Docker/quality Windows: 20 descobertos, 17 aprovados e três skips conhecidos do host;
- provas Linux isoladas: cleanup recursivo e preservação de target externo, 2/2;
- regressão: 345 testes aprovados, 33 skips opcionais, branch coverage 85,34%;
- source, evidências, wheel/sdist e reports submetidos ao secret scanner;
- nenhum container com label ASEF permaneceu.

## Riscos residuais

- `python-pytest` permanece experimental e delimitado ao perfil de referência;
- Docker não é garantia para código arbitrariamente hostil ou produção;
- quality é opcional e não altera aceitação funcional;
- Windows continua sem apply recursivo de diretórios; a prova existe no runner Linux controlado;
- live permanece variável, pago e fora do gate obrigatório de PR;
- walkthrough foi roteirizado pelo mantenedor, não por participante externo;
- a nova composição de sete jobs ainda precisa de execução pública no commit da candidata.

## Parecer

A implementação das seis fatias do 5.8 foi consolidada no commit `9739c1e`. Após autorização explícita de Lucas, o commit foi enviado à `main` e a [CI pública `29597109452`](https://github.com/lucasteixeirati/asef-agentic-test-factory/actions/runs/29597109452) aprovou os sete jobs, inclusive `public-experience`. A candidata `0.1.0a6` está apta ao checkpoint separado de tag/pré-release; o incremento ainda não deve ser declarado publicado nem concluído sem essa decisão. Gate 5, 5.9 e Etapa 6 permanecem decisões independentes.
