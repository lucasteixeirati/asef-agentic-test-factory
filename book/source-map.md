# Mapa de fontes do livro

Este mapa evita reconstrução retrospectiva e não transforma o índice provisório em obrigação arquitetural.

| Capítulo provisório | Fontes já disponíveis | Maturidade |
|---|---|---|
| 1. Por que um engenheiro de qualidade decidiu construir com IA | Marco Zero; nota de concepção; relato dos 15 anos em QA | base narrativa |
| 2. Determinismo, probabilidade e confiança | ADR-001; estratégia de avaliação; structured output | evidência parcial |
| 3. O marco zero e a fábrica de software | `concepcao/`; timeline; journal do Marco Zero | forte |
| 4. O reposicionamento como fábrica de testes | nota de concepção; visão e escopo | forte |
| 5. Conceber com IA sem terceirizar decisões | revisão externa; rejeição da ADR-007; decisões humanas | forte |
| 6. O primeiro workflow e suas restrições | plano da Etapa 4; WF-001; WS-001 a WS-007 | forte |
| 7. Contratos, estado e evidências | contratos 1.1; ADRs; evidence model; observabilidade | forte |
| 8. Segurança para executar código gerado | EXP-002; Docker tests; sandbox policy | forte para baseline |
| 9. Como testar componentes não determinísticos | cassettes; structured output; retries; mutation pilot; adapter live e budget real do 5.4 | forte para o primeiro provider |
| 10. Experimentos com modelos, prompts e frameworks | EXP-001 a EXP-006; Lesson 001 | forte |
| 11. A primeira execução por outra pessoa | instalação limpa automatizada; usuário externo real ainda ausente | incompleta |
| 12. Falhas, retrabalho e decisões revertidas | journals das Etapas 3 e 4; ADR-007; auditoria do wheel; sete findings do 5.3; hardening de contexto e budget do 5.4 | forte |
| 13. Evolução baseada em evidências | ADR-004, ADR-007, ADR-008, ADR-009; checkpoints; revisões 5.3/5.4 | forte até o Alpha parcial |
| 14. Open source e comunidade | publicação GitHub; feedback comunitário ainda ausente | inicial |
| 15. Impacto da IA na velocidade e qualidade | baseline do Dia 2; atualização do Dia 3; nota do Dia 6 com aproximadamente 30 horas e 500 interações até o fim do Dia 5 | evidência contemporânea em evolução |
| 16. O que eu faria diferente | lessons e retrospectivas; exige distância temporal | aberta |

## Lacunas que exigem voz do autor

- o que Lucas faria diferente se reiniciasse o projeto hoje;
- validação futura das estimativas de aproximadamente 30 horas e 500 interações até o fim do Dia 5;
- critério pessoal para considerar uma entrega realmente pronta;
- experiência de um usuário externo real, quando ocorrer;
- percepção após o Alpha Python e as etapas multilíngues.
