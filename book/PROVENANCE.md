# Proveniência editorial

## Por que registrar

O livro trata de desenvolvimento assistido por IA. A origem de cada texto também precisa ser evidência: fatos do repositório, percepção do autor e estruturação feita pela IA não são equivalentes.

## Classes

- **Voz do autor:** percepção, julgamento ou memória fornecida explicitamente por Lucas.
- **Evidência verificável:** código, teste, commit, ADR, journal, custo ou execução referenciada.
- **Estruturação por IA:** organização, síntese ou primeira redação feita pelo modelo a partir das fontes.
- **Inferência editorial:** interpretação proposta, ainda sujeita à revisão do autor.

## Estados

- `matéria-prima` — preservada, ainda sem tratamento narrativo;
- `rascunho assistido` — texto estruturado pela IA e aguardando revisão autoral;
- `revisado pelo autor` — conteúdo e voz aprovados por Lucas;
- `pronto para edição` — revisado tecnicamente e editorialmente;
- `publicado` — versão associada a release ou edição.

## Registro atual

| Arquivo | Origem dominante | Estruturação | Estado |
|---|---|---|---|
| `notes/2026-07-12-concepcao-velocidade-e-julgamento-de-qa.md` | relato explícito do autor + journals | GPT-5.6 Sol | matéria-prima |
| `notes/2026-07-12-o-contexto-do-qa-como-parte-do-produto.md` | percepção explícita do autor | GPT-5.6 Sol | matéria-prima |
| `notes/2026-07-13-do-checkout-ao-produto.md` | evidências da 4.R7 + relato explícito do autor | GPT-5.6 Sol | revisado pelo autor em 2026-07-13 |
| `retrospectives/2026-07-13-etapa-04.md` | código, testes, ADRs, journals + relato explícito do autor | GPT-5.6 Sol | revisado pelo autor em 2026-07-13 |
| `notes/2026-07-15-dia-06-produtividade-e-revisao.md` | relato explícito de Lucas + evidências de `v0.1.0a3` | estruturação assistida por IA | rascunho assistido |

Uma aprovação de gate não aprova automaticamente a voz ou a redação de um capítulo.
