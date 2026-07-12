# Contribuindo com o ASEF

Obrigado por considerar uma contribuição. O projeto está em fase experimental e valoriza evidências, reprodutibilidade e honestidade sobre limitações.

## Antes de começar

- leia o README e o Planejamento Mestre;
- procure experimento, ADR ou issue relacionada;
- mudanças arquiteturais relevantes começam com problema e evidência;
- não inclua secrets, dados internos, prompts privados ou contexto real de equipes;
- não apresente uma capability planejada como suportada.

## Desenvolvimento

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Integrações Docker são opt-in e requerem Docker Desktop/Engine compatível.

## Pull requests

Explique:

- problema e escopo;
- evidências e testes;
- riscos e limitações;
- impacto em contratos, segurança, documentação e livro/jornada;
- uso de IA relevante, incluindo sugestões rejeitadas ou corrigidas.

## Contextos e cassettes

- use sistemas e organizações fictícios;
- autenticação deve ser somente uma referência gerenciada pelo host;
- sanitize outputs antes do commit;
- cassettes não podem conter secrets ou conteúdo proprietário.

## Decisões

Mantenedores preservam autoridade sobre visão e arquitetura. Experimentos informam decisões, mas não alteram automaticamente ADRs aceitos.
