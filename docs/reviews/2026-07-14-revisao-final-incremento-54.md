# Revisão final do incremento 5.4

- **Data:** 2026-07-14
- **Escopo:** adapter OpenAI live, Structured Outputs, budgets monetários, retry e evidência de provider
- **Decisão técnica local:** aprovada
- **Candidata de publicação:** pré-alpha `0.1.0a3`
- **Publicação:** pendente de commit, CI pública, tag e release

## Mudanças principais

1. `AgenticTestPort` e `TestCorrectionPort` receberam implementação live pública sobre a Responses API.
2. Análise, geração e correção usam schemas estritos, prompts versionados e validação local.
3. A aplicação permanece autoridade de workflow, reserva, retry, correção e budget.
4. Uso observado registra provider, modelo, response ID, tokens, latência e custo estimado em BRL.
5. Contexto enviado ao provider fica restrito ao `read_scope`, UTF-8, 64 KiB e bloqueio de marcadores sensíveis.
6. A CLI exige modo, contexto, modelo, budget e tarifas explícitos; demo continua keyless e offline.
7. Cassette live é opt-in e omite prompt integral, headers e credenciais.
8. O estado evoluiu para `1.3.0`, preservando leitura dos estados `1.1.0` e `1.2.0` suportados.

## Finding encerrado na revisão

Valores monetários `NaN` e `Infinity` não satisfazem comparações comuns como menor, maior ou igual. Isso poderia permitir que um budget live não finito escapasse da validação e neutralizasse o teto de custo. O contrato de request/estado, o gateway e as tarifas do adapter passaram a exigir números finitos antes do transporte. Regressões cobrem budget, custo observado e tarifas. As operações públicas de geração e correção também revalidam o requisito antes de chamar o provider.

## Evidência

- core: 199 descobertos, 183 aprovados e 16 opt-in; branch coverage de 87%;
- frameworks/workflow opcional: 18/18;
- Docker: 15 descobertos, 14 aprovados e um skip conhecido de symlink por privilégio do Windows;
- smoke OpenAI explicitamente autorizado: uma chamada, sem retry, `gpt-5.4-2026-03-05`, 194 tokens de entrada, 138 de saída, 4.515 ms e R$ 0,01533 estimados sob teto de R$ 0,10;
- wheel `asef_agentic_test_factory-0.1.0a3-py3-none-any.whl`: SHA-256 `b147f6e4e868e2c1c04f24fce8cf42c42b549556727c35d2c10148265b945871`;
- sdist `asef_agentic_test_factory-0.1.0a3.tar.gz`: SHA-256 `02890480965ad8add1b7ba0d42c7213823cf758c6cb2b16968591aa0b53409d5`;
- wheel instalado sem dependências em venv novo e identificado como `0.1.0a3`;
- demo keyless executada fora do checkout: `SUCCEEDED`/`ACCEPTED`;
- secret scan do repositório, pacotes e artifacts da demo, além de `git diff --check`: aprovados.

## Limites preservados

- o modo live é experimental e depende de chave, preços/câmbio atualizados e autorização de custo;
- custo em BRL é estimativa operacional, não conciliação de faturamento;
- o fluxo combinado com oracle/correção do 5.3 ainda não é o default da CLI;
- cassettes live não devem ser publicados sem revisão humana adicional;
- não há alegação de segurança para código arbitrariamente hostil ou uso em produção;
- nenhum release, tag ou mudança remota ocorre sem decisão humana.

## Parecer

Os critérios técnicos locais do incremento 5.4 estão atendidos e o finding de fechamento está encerrado. Artefatos, instalação limpa, demo keyless e scans locais foram aprovados. A revisão recomenda `0.1.0a3` como próxima pré-alpha; a aprovação definitiva de publicação depende agora do commit e da CI pública verde antes da tag/release.
