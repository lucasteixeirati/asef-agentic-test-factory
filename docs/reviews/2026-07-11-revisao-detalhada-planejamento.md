# Revisão detalhada do Planejamento Mestre

**Data:** 2026-07-11  
**Parecer:** aprovado com ajustes estruturais antes da conclusão da Etapa 0

## Decisões resultantes

- separar SUT, geração de testes e oracle;
- tratar geração de implementação como fixture sintética, não como prova principal;
- decompor o adaptador multilíngue por capacidades;
- adicionar development, evaluation e holdout datasets com controle de exposição;
- validar o projeto com 3–5 QEs antes da v0.1;
- transformar critérios da v0.1 em matriz objetiva de prontidão;
- usar Docker Desktop como ambiente inicial de containers;
- definir Windows + Docker Desktop/WSL2 como ambiente de referência inicial;
- ampliar o manifest para rastreabilidade e reprodutibilidade;
- mover detalhes especializados para documentos próprios;
- estabelecer autoridade e precedência documental.

## Findings preservados para rastreabilidade

1. O workflow inicial poderia validar código e testes produzidos pela mesma interpretação incorreta.
2. `LanguageAdapter` concentrava responsabilidades demais.
3. Faltavam independência de oracle, holdout e prevenção de vazamento.
4. A validação comunitária ocorria somente após a v0.1.
5. Critérios da v0.1 não eram integralmente verificáveis.
6. “Cada versão pequena” conflitava com a definição robusta da v0.1.
7. A implementação Python do core precisava ser diferenciada do agnosticismo do domínio.
8. Processo local não poderia ser comparado a container como fronteira equivalente.
9. Faltava uma matriz de ambientes suportados.
10. Conformidade entre linguagens precisava validar contratos, não outputs idênticos.
11. O manifest não continha dados suficientes para reprodução.
12. Registros de revisão estavam aumentando indevidamente o Planejamento Mestre.
13. Faltava uma política explícita de autoridade documental.

O relatório completo desta revisão permanece registrado na conversa de concepção assistida por IA; este documento preserva os findings e decisões que impactam o repositório.

